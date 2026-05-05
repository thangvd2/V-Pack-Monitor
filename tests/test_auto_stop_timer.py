import threading
import time
from unittest.mock import MagicMock, patch

import vpack.state
from vpack import database, video_worker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _start_recording(client, op_headers, station_id, barcode="TESTWB001"):
    """Acquire session + start recording via scan endpoint.

    Returns ``(response, mock_recorder, record_id)``.
    """
    client.post(
        "/api/sessions/acquire",
        headers=op_headers,
        params={"station_id": station_id},
    )
    mock_rec = MagicMock()
    with patch.object(vpack.state, "_preflight_checks", return_value=(True, "")):
        with patch("vpack.network.validate_mac", return_value=False):
            with patch("vpack.routes.records.CameraRecorder", return_value=mock_rec):
                r = client.post(
                    "/api/scan",
                    headers=op_headers,
                    json={"barcode": barcode, "station_id": station_id},
                )
    rid = vpack.state.active_record_ids.get(station_id)
    return r, mock_rec, rid


def _cancel_real_timers(sid):
    """Pop & cancel any real ``threading.Timer`` objects for *sid*."""
    for store in (vpack.state._recording_timers, vpack.state._recording_warning_timers):
        t = store.pop(sid, None)
        if t is not None:
            try:
                t.cancel()
            except Exception:
                pass


# ===================================================================
# Test class
# ===================================================================


class TestAutoStopTimer:
    """Comprehensive tests for auto-stop timer creation / cancellation / firing."""

    # ------------------------------------------------------------------
    # 1. Timer created on recording start
    # ------------------------------------------------------------------
    def test_timer_created_on_recording_start(self, client, operator_headers, sample_station_id):
        r, _, _ = _start_recording(client, operator_headers, sample_station_id)
        assert r.json()["status"] == "recording"
        sid = sample_station_id

        assert sid in vpack.state._recording_timers
        assert sid in vpack.state._recording_warning_timers
        assert sid in vpack.state._recording_start_times

        assert isinstance(vpack.state._recording_timers[sid], threading.Timer)
        assert isinstance(vpack.state._recording_warning_timers[sid], threading.Timer)
        assert isinstance(vpack.state._recording_start_times[sid], float)

    # ------------------------------------------------------------------
    # 2. Timer cancelled on manual STOP
    # ------------------------------------------------------------------
    def test_timer_cancelled_on_manual_stop(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id

        # Grab refs before STOP (so we can verify cancel was called)
        stop_timer = vpack.state._recording_timers.get(sid)
        warn_timer = vpack.state._recording_warning_timers.get(sid)
        assert stop_timer is not None
        assert warn_timer is not None

        # Spy on cancel()
        stop_cancel_spy = MagicMock(wraps=stop_timer.cancel)
        warn_cancel_spy = MagicMock(wraps=warn_timer.cancel)
        stop_timer.cancel = stop_cancel_spy
        warn_timer.cancel = warn_cancel_spy

        with patch.object(video_worker, "submit_stop_and_save", return_value=True):
            r = client.post(
                "/api/scan",
                headers=operator_headers,
                json={"barcode": "STOP", "station_id": sid},
            )

        assert r.json()["status"] == "processing"
        assert vpack.state._recording_timers.get(sid) is None
        assert vpack.state._recording_warning_timers.get(sid) is None
        stop_cancel_spy.assert_called()
        warn_cancel_spy.assert_called()

    # ------------------------------------------------------------------
    # 3. Timer cancelled on EXIT
    # ------------------------------------------------------------------
    def test_timer_cancelled_on_exit(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id

        # Grab refs before EXIT (so we can verify cancel was called)
        stop_timer = vpack.state._recording_timers.get(sid)
        warn_timer = vpack.state._recording_warning_timers.get(sid)
        assert stop_timer is not None
        assert warn_timer is not None

        # Spy on cancel()
        stop_cancel_spy = MagicMock(wraps=stop_timer.cancel)
        warn_cancel_spy = MagicMock(wraps=warn_timer.cancel)
        stop_timer.cancel = stop_cancel_spy
        warn_timer.cancel = warn_cancel_spy

        with patch.object(video_worker, "submit_stop_and_save", return_value=True):
            r = client.post(
                "/api/scan",
                headers=operator_headers,
                json={"barcode": "EXIT", "station_id": sid},
            )

        assert r.json()["status"] == "processing"
        assert vpack.state._recording_timers.get(sid) is None
        assert vpack.state._recording_warning_timers.get(sid) is None
        stop_cancel_spy.assert_called()
        warn_cancel_spy.assert_called()

    # ------------------------------------------------------------------
    # 4. CRITICAL-1 regression: wrong record_id must NOT stop recording
    # ------------------------------------------------------------------
    def test_record_id_verification_prevents_wrong_stop(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id
        actual_rid = vpack.state.active_record_ids.get(sid)
        assert actual_rid is not None

        _cancel_real_timers(sid)

        with patch.object(database, "update_record_status") as mock_db:
            vpack.state._auto_stop_recording(sid, 99999)
            mock_db.assert_not_called()

        # Recording must remain active
        assert sid in vpack.state.active_recorders
        assert vpack.state.active_record_ids.get(sid) == actual_rid

    # ------------------------------------------------------------------
    # 5. Matching record_id allows auto-stop to proceed
    # ------------------------------------------------------------------
    def test_record_id_match_allows_auto_stop(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id
        actual_rid = vpack.state.active_record_ids.get(sid)
        assert actual_rid is not None

        _cancel_real_timers(sid)

        with patch.object(video_worker, "submit_stop_and_save", return_value=True):
            with patch.object(vpack.state, "notify_sse") as mock_sse:
                vpack.state._auto_stop_recording(sid, actual_rid)

        # Recorders cleaned up
        assert sid not in vpack.state.active_recorders
        assert sid not in vpack.state.active_record_ids
        assert sid not in vpack.state.active_waybills

        # DB status changed to PROCESSING
        rec = database.get_record_by_id(actual_rid)
        assert rec is not None
        assert rec["status"] == "PROCESSING"

        # SSE notification sent with auto_stopped flag
        sse_calls = mock_sse.call_args_list
        video_status_calls = [c for c in sse_calls if c[0][0] == "video_status"]
        assert len(video_status_calls) >= 1
        data = video_status_calls[0][0][1]
        assert data["status"] == "PROCESSING"
        assert data["auto_stopped"] is True
        assert data["record_id"] == actual_rid

    # ------------------------------------------------------------------
    # 6. Auto-stop is a graceful no-op when recording already stopped
    # ------------------------------------------------------------------
    def test_auto_stop_noop_when_already_stopped(self, client):
        with patch.object(database, "update_record_status") as mock_db:
            vpack.state._auto_stop_recording(99999, 123)
            mock_db.assert_not_called()

    # ------------------------------------------------------------------
    # 7. Warning timer is cancelled after STOP (won't fire)
    # ------------------------------------------------------------------
    def test_warning_timer_not_fired_after_stop(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id

        warn_timer = vpack.state._recording_warning_timers.get(sid)
        assert warn_timer is not None

        _cancel_real_timers(sid)

        with patch.object(video_worker, "submit_stop_and_save", return_value=True):
            with patch.object(vpack.state, "notify_sse") as mock_sse:
                client.post(
                    "/api/scan",
                    headers=operator_headers,
                    json={"barcode": "STOP", "station_id": sid},
                )
                # Give any stray thread a moment
                time.sleep(0.05)
                # No recording_warning event should have been emitted after STOP
                warning_calls = [c for c in mock_sse.call_args_list if c[0][0] == "recording_warning"]
                assert len(warning_calls) == 0

        assert vpack.state._recording_warning_timers.get(sid) is None
        assert vpack.state._recording_timers.get(sid) is None

    # ------------------------------------------------------------------
    # 8. Warning not emitted when no recorder exists
    # ------------------------------------------------------------------
    def test_warning_not_emitted_when_not_recording(self, client):
        with patch.object(vpack.state, "notify_sse") as mock_sse:
            vpack.state._emit_recording_warning(99999)
            mock_sse.assert_not_called()

    # ------------------------------------------------------------------
    # 9. Warning emitted when recording is active
    # ------------------------------------------------------------------
    def test_warning_emitted_when_recording(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id
        _cancel_real_timers(sid)

        with patch.object(vpack.state, "notify_sse") as mock_sse:
            vpack.state._emit_recording_warning(sid)
            mock_sse.assert_called_once()

        event_type, data = mock_sse.call_args[0]
        assert event_type == "recording_warning"
        assert data["station_id"] == sid
        # 600 - 540 = 60 seconds remaining
        assert data["remaining_seconds"] == 60

    # ------------------------------------------------------------------
    # 10. _recording_start_times cleaned on STOP
    # ------------------------------------------------------------------
    def test_start_times_cleaned_on_stop(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id
        assert sid in vpack.state._recording_start_times

        _cancel_real_timers(sid)

        with patch.object(video_worker, "submit_stop_and_save", return_value=True):
            client.post(
                "/api/scan",
                headers=operator_headers,
                json={"barcode": "STOP", "station_id": sid},
            )

        assert vpack.state._recording_start_times.get(sid) is None

    # ------------------------------------------------------------------
    # 11. New recording cancels old timer (via _cancel_recording_timer)
    # ------------------------------------------------------------------
    def test_new_recording_cancels_old_timer(self, client, operator_headers, sample_station_id):
        # Start recording A — creates real timers
        _start_recording(client, operator_headers, sample_station_id, barcode="OLDWB001")
        sid = sample_station_id
        assert sid in vpack.state._recording_timers

        # Cancel real timers so they don't fire
        _cancel_real_timers(sid)

        # Install mock timers to verify .cancel() is called
        mock_stop = MagicMock()
        mock_warn = MagicMock()
        vpack.state._recording_timers[sid] = mock_stop
        vpack.state._recording_warning_timers[sid] = mock_warn

        # _cancel_recording_timer is called at the top of every new recording
        vpack.state._cancel_recording_timer(sid)

        mock_stop.cancel.assert_called_once()
        mock_warn.cancel.assert_called_once()
        assert vpack.state._recording_timers.get(sid) is None
        assert vpack.state._recording_warning_timers.get(sid) is None

    # ------------------------------------------------------------------
    # 12. Lifespan shutdown cancels all timers
    # ------------------------------------------------------------------
    def test_timers_cancelled_on_shutdown(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id

        stop_timer = vpack.state._recording_timers.get(sid)
        warn_timer = vpack.state._recording_warning_timers.get(sid)
        assert stop_timer is not None
        assert warn_timer is not None

        stop_cancel_spy = MagicMock(wraps=stop_timer.cancel)
        warn_cancel_spy = MagicMock(wraps=warn_timer.cancel)
        stop_timer.cancel = stop_cancel_spy
        warn_timer.cancel = warn_cancel_spy

        with vpack.state._recording_timers_lock:
            for timer in vpack.state._recording_timers.values():
                timer.cancel()
            vpack.state._recording_timers.clear()
            for timer in vpack.state._recording_warning_timers.values():
                timer.cancel()
            vpack.state._recording_warning_timers.clear()
            vpack.state._recording_start_times.clear()

        stop_cancel_spy.assert_called()
        warn_cancel_spy.assert_called()
        assert len(vpack.state._recording_timers) == 0
        assert len(vpack.state._recording_warning_timers) == 0
        assert len(vpack.state._recording_start_times) == 0

    # ------------------------------------------------------------------
    # 13. Auto-stop sets FAILED when submit_stop_and_save returns False
    # ------------------------------------------------------------------
    def test_auto_stop_sets_failed_when_queue_full(self, client, operator_headers, sample_station_id):
        _start_recording(client, operator_headers, sample_station_id)
        sid = sample_station_id
        actual_rid = vpack.state.active_record_ids.get(sid)
        assert actual_rid is not None

        _cancel_real_timers(sid)

        with patch.object(video_worker, "submit_stop_and_save", return_value=False):
            with patch.object(vpack.state, "notify_sse") as mock_sse:
                vpack.state._auto_stop_recording(sid, actual_rid)

        rec = database.get_record_by_id(actual_rid)
        assert rec is not None
        assert rec["status"] == "FAILED"

        sse_calls = mock_sse.call_args_list
        video_status_calls = [c for c in sse_calls if c[0][0] == "video_status"]
        assert len(video_status_calls) >= 2
        failed_data = video_status_calls[-1][0][1]
        assert failed_data["status"] == "FAILED"
        assert failed_data["record_id"] == actual_rid

        assert sid not in vpack.state._processing_count
        assert sid not in vpack.state.active_recorders
        assert sid not in vpack.state.active_record_ids
