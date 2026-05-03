from unittest.mock import MagicMock, patch

import pytest
import recorder
from recorder import CameraRecorder, _detect_hw_encoder


@pytest.fixture(autouse=True)
def reset_hw_encoder_cache():
    # Reset global cache before each test
    recorder._hw_encoder_cache = None
    yield
    recorder._hw_encoder_cache = None


@patch("subprocess.run")
def test_detect_hw_encoder_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    enc, extra = _detect_hw_encoder()
    assert enc == "h264_qsv"
    assert "qsv" in extra


@patch("subprocess.run")
def test_detect_hw_encoder_fallback(mock_run):
    mock_run.return_value = MagicMock(returncode=1)
    enc, extra = _detect_hw_encoder()
    assert enc == "libx264"
    assert extra == ""


@patch("subprocess.Popen")
def test_start_recording_single(mock_popen, tmp_path):
    mock_popen.return_value = MagicMock()
    rec = CameraRecorder("rtsp://fake", output_dir=str(tmp_path), record_mode="SINGLE")

    files = rec.start_recording("TEST-WB-123")
    assert len(files) == 1
    assert "TEST-WB-123" in files[0]
    assert mock_popen.call_count == 1
    cmd = mock_popen.call_args[0][0]
    assert "-f" in cmd
    assert "mpegts" in cmd


@patch("subprocess.Popen")
def test_start_recording_dual(mock_popen, tmp_path):
    mock_popen.return_value = MagicMock()
    rec = CameraRecorder("rtsp://fake1", "rtsp://fake2", output_dir=str(tmp_path), record_mode="DUAL_FILE")

    files = rec.start_recording("TEST-WB-123")
    assert len(files) == 2
    assert "Cam1" in files[0]
    assert "Cam2" in files[1]
    assert mock_popen.call_count == 2


@patch("subprocess.Popen")
@patch("recorder._detect_hw_encoder", return_value=("libx264", ""))
def test_start_recording_pip(mock_detect, mock_popen, tmp_path):
    mock_popen.return_value = MagicMock()
    rec = CameraRecorder("rtsp://fake1", "rtsp://fake2", output_dir=str(tmp_path), record_mode="PIP")

    files = rec.start_recording("TEST-WB-123")
    assert len(files) == 1
    assert "PIP" in files[0]
    assert mock_popen.call_count == 1


@patch("os.rename")
@patch("os.remove")
@patch("subprocess.run")
@patch("subprocess.Popen")
@patch("os.path.exists", return_value=True)
@patch("os.path.getsize", return_value=1024)
def test_stop_recording(mock_getsize, mock_exists, mock_popen, mock_run, mock_remove, mock_rename, tmp_path):
    mock_proc = MagicMock()
    mock_proc.stdin = MagicMock()
    mock_popen.return_value = mock_proc
    mock_run.return_value = MagicMock(returncode=0, stdout="")

    rec = CameraRecorder("rtsp://fake", output_dir=str(tmp_path), record_mode="SINGLE")
    files = rec.start_recording("TEST-WB-123")

    # Simulate stop
    final_files = rec.stop_recording()

    # Assert stdin.write(b"q\n") was called
    mock_proc.stdin.write.assert_called_with(b"q\n")
    # Because we mocked exists and getsize to True/1024, it should return the file
    assert final_files == files
