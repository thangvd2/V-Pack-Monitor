import sys
import threading
from unittest.mock import MagicMock, patch

import pytest

# Pre-mock heavy external deps to avoid side effects during import
for _mod in ("recorder", "telegram_bot", "telebot", "psutil", "cloud_sync", "network"):
    sys.modules.setdefault(_mod, MagicMock())

import database
import video_worker


@pytest.fixture(autouse=True)
def _reset_worker(monkeypatch):
    """Ensure executor is cleaned up between tests and shutdown is fast."""
    monkeypatch.setattr(video_worker, "_SHUTDOWN_TIMEOUT", 0.1)
    yield
    try:
        video_worker.shutdown()
    finally:
        video_worker._executor = None


# =============================================================================
# TestVideoWorker — executor lifecycle, submit, shutdown, task processing
# =============================================================================
class TestVideoWorker:
    # --- lazy init ---

    def test_submit_lazy_init_creates_executor(self):
        """submit_stop_and_save auto-creates ThreadPoolExecutor when _executor is None."""
        assert video_worker._executor is None
        mock_rec = MagicMock()
        mock_rec.stop_recording.return_value = []
        with patch("video_worker._process_stop_and_save"):
            video_worker.submit_stop_and_save(1, mock_rec, "WB001", 1, save=False)
            assert video_worker._executor is not None

    # --- submit delegation ---

    def test_submit_delegates_to_executor(self):
        """submit_stop_and_save submits work to executor (wrapped for bounded queue)."""
        mock_executor = MagicMock()
        with video_worker._lock:
            video_worker._executor = mock_executor

        mock_rec = MagicMock()
        video_worker.submit_stop_and_save(100, mock_rec, "WB100", 1)

        # Submit is now called with a wrapper function for bounded queue tracking
        mock_executor.submit.assert_called_once()
        call_args = mock_executor.submit.call_args
        assert call_args is not None

    # --- shutdown behaviour ---

    def test_shutdown_calls_wait_false_then_poll(self):
        """shutdown() calls executor.shutdown(wait=False) then polls — timeout guard."""
        mock_executor = MagicMock()
        mock_executor._threads = []  # No active threads — exit immediately
        with video_worker._lock:
            video_worker._executor = mock_executor

        video_worker.shutdown()

        mock_executor.shutdown.assert_called_once_with(wait=False)
        assert video_worker._executor is None

    def test_shutdown_resets_executor_to_none(self):
        """After shutdown, module-level _executor is reset to None."""
        mock_rec = MagicMock()
        mock_rec.stop_recording.return_value = []
        with patch("video_worker._process_stop_and_save"):
            video_worker.submit_stop_and_save(1, mock_rec, "WB001", 1, save=False)
            assert video_worker._executor is not None
        video_worker.shutdown()
        assert video_worker._executor is None

    def test_double_shutdown_idempotent(self):
        """Calling shutdown() twice does not raise — second call is a no-op."""
        mock_rec = MagicMock()
        mock_rec.stop_recording.return_value = []
        with patch("video_worker._process_stop_and_save"):
            video_worker.submit_stop_and_save(1, mock_rec, "WB001", 1, save=False)
            video_worker.shutdown()
        # Second call — must not raise
        video_worker.shutdown()
        assert video_worker._executor is None

    # --- concurrency ---

    def test_concurrent_submit_shutdown_no_deadlock(self):
        """Concurrent submit + shutdown must not deadlock."""
        mock_rec = MagicMock()
        mock_rec.stop_recording.return_value = []
        # Pre-create executor with a real task (mock processing to avoid DB side effects)
        with patch("video_worker._process_stop_and_save"):
            video_worker.submit_stop_and_save(1, mock_rec, "WB001", 1, save=False)

        done = threading.Event()

        def do_shutdown():
            # 0.5s ceiling: mocked task completes in ~0ms; 500ms is generous
            # even for slow CI. If thread isn't done in 0.5s → deadlock detected.
            original_timeout = video_worker._SHUTDOWN_TIMEOUT
            video_worker._SHUTDOWN_TIMEOUT = 0.5
            try:
                video_worker.shutdown()
            finally:
                video_worker._SHUTDOWN_TIMEOUT = original_timeout
            done.set()

        t = threading.Thread(target=do_shutdown)
        t.start()
        assert done.wait(timeout=3), "shutdown() hung — possible deadlock"
        t.join(timeout=1)

    # --- task success callback ---

    def test_process_valid_video_marks_ready(self, sample_station_id):
        """Worker with valid video files updates DB status to READY."""
        rid = database.create_record(sample_station_id, "WB_OK", "SINGLE")
        mock_rec = MagicMock()
        mock_rec.stop_recording.return_value = ["/fake/video.mp4"]

        with (
            patch("video_worker._get_video_info", return_value=(True, 30.5)),
            patch("video_worker._decrement_processing"),
            patch("video_worker._notify_sse_safe"),
        ):
            video_worker._process_stop_and_save(
                rid,
                mock_rec,
                "WB_OK",
                sample_station_id,
                save=True,
            )

        assert database.get_record_by_id(rid)["status"] == "READY"

    # --- task failure callback ---

    def test_process_no_files_marks_failed(self, sample_station_id):
        """Worker with no output files updates DB status to FAILED."""
        rid = database.create_record(sample_station_id, "WB_FAIL", "SINGLE")
        mock_rec = MagicMock()
        mock_rec.stop_recording.return_value = []

        with (
            patch("video_worker._send_failed_alert"),
            patch("video_worker._decrement_processing"),
            patch("video_worker._notify_sse_safe"),
        ):
            video_worker._process_stop_and_save(
                rid,
                mock_rec,
                "WB_FAIL",
                sample_station_id,
                save=True,
            )

        assert database.get_record_by_id(rid)["status"] == "FAILED"

    # --- save=False path ---

    def test_process_save_false_deletes_record(self, sample_station_id):
        """Worker with save=False deletes the record from DB."""
        rid = database.create_record(sample_station_id, "WB_DEL", "SINGLE")
        mock_rec = MagicMock()
        mock_rec.stop_recording.return_value = ["/fake/video.mp4"]

        with (
            patch("video_worker._decrement_processing"),
            patch("video_worker._notify_sse_safe"),
        ):
            video_worker._process_stop_and_save(
                rid,
                mock_rec,
                "WB_DEL",
                sample_station_id,
                save=False,
            )

        assert database.get_record_by_id(rid) is None

    # --- exception during processing ---

    def test_process_exception_marks_failed(self, sample_station_id):
        """Exception during processing marks DB status FAILED."""
        rid = database.create_record(sample_station_id, "WB_ERR", "SINGLE")
        mock_rec = MagicMock()
        mock_rec.stop_recording.side_effect = RuntimeError("FFmpeg crashed")

        with (
            patch("video_worker._send_failed_alert"),
            patch("video_worker._decrement_processing"),
            patch("video_worker._notify_sse_safe"),
        ):
            video_worker._process_stop_and_save(
                rid,
                mock_rec,
                "WB_ERR",
                sample_station_id,
                save=True,
            )

        assert database.get_record_by_id(rid)["status"] == "FAILED"


# =============================================================================
# TestCrashRecovery — _recover_pending_records (defined in api.py)
# =============================================================================
class TestCrashRecovery:
    def test_recover_recording_records(self, sample_station_id):
        """RECORDING records with no recoverable files are marked FAILED."""
        import api

        rid = database.create_record(sample_station_id, "REC_WB", "SINGLE")
        assert database.get_record_by_id(rid)["status"] == "RECORDING"

        with (
            patch("os.path.exists", return_value=False),
            patch("api._get_video_info_external", return_value=(False, 0)),
        ):
            api._recover_pending_records()

        assert database.get_record_by_id(rid)["status"] == "FAILED"

    def test_recover_processing_records_with_valid_video(self, sample_station_id):
        """PROCESSING records with a valid video file are recovered to READY."""
        import api

        rid = database.create_record(sample_station_id, "PROC_WB", "SINGLE")
        database.update_record_status(rid, "PROCESSING", video_paths="/fake/video.mp4")

        def mock_exists(p):
            # .tmp.ts does not exist, but final .mp4 does
            return p == "/fake/video.mp4"

        with (
            patch("os.path.exists", side_effect=mock_exists),
            patch("api._get_video_info_external", return_value=(True, 15.0)),
        ):
            api._recover_pending_records()

        assert database.get_record_by_id(rid)["status"] == "READY"

    def test_ready_records_excluded_from_pending(self, sample_station_id):
        """READY status records are not returned by get_pending_records."""
        rid = database.create_record(sample_station_id, "READY_WB", "SINGLE")
        database.update_record_status(rid, "READY")

        pending = database.get_pending_records()
        assert rid not in [r["id"] for r in pending]
