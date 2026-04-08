import subprocess
import os
from datetime import datetime
import platform

class CameraRecorder:
    def __init__(self, rtsp_url_1, rtsp_url_2=None, output_dir="recordings", record_mode="SINGLE"):
        # record_mode có thể là: "SINGLE", "DUAL_FILE", "PIP"
        self.rtsp_url_1 = rtsp_url_1
        # Nếu chưa có camera 2, ta dùng tạm camera 1 làm luồng 2 để test PIP/DUAL
        self.rtsp_url_2 = rtsp_url_2 if rtsp_url_2 else rtsp_url_1
        
        self.output_dir = output_dir
        self.record_mode = record_mode
        self.processes = []
        self.current_files = []
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def start_recording(self, waybill_code):
        if self.processes:
            self.stop_recording()
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.processes = []
        self.current_files = []

        if self.record_mode == "SINGLE":
            filename = f"{waybill_code}_{timestamp}.mp4"
            filepath = os.path.join(self.output_dir, filename)
            self._launch_ffmpeg([
                'ffmpeg', '-y', '-rtsp_transport', 'tcp',
                '-i', self.rtsp_url_1,
                '-c:v', 'copy', '-c:a', 'copy', filepath
            ])
            self.current_files.append(filepath)

        elif self.record_mode == "DUAL_FILE":
            # Ghi Camera 1
            file1 = os.path.join(self.output_dir, f"{waybill_code}_{timestamp}_Cam1.mp4")
            self._launch_ffmpeg([
                'ffmpeg', '-y', '-rtsp_transport', 'tcp',
                '-i', self.rtsp_url_1,
                '-c:v', 'copy', '-c:a', 'copy', file1
            ])
            self.current_files.append(file1)
            
            # Ghi Camera 2
            file2 = os.path.join(self.output_dir, f"{waybill_code}_{timestamp}_Cam2.mp4")
            self._launch_ffmpeg([
                'ffmpeg', '-y', '-rtsp_transport', 'tcp',
                '-i', self.rtsp_url_2,
                '-c:v', 'copy', '-c:a', 'copy', file2
            ])
            self.current_files.append(file2)

        elif self.record_mode == "PIP":
            # Ghép PIP (Picture-in-Picture)
            filename = f"{waybill_code}_{timestamp}_PIP.mp4"
            filepath = os.path.join(self.output_dir, filename)
            
            # --- Tối ưu Hiệu năng (Hardware Acceleration) ---
            sys_os = platform.system()
            vcodec = 'libx264'
            
            if sys_os == 'Darwin':
                vcodec = 'h264_videotoolbox'  # Mac Apple Silicon / Intel
            elif sys_os == 'Windows':
                # Trên Windows, thử ưu tiên NVIDIA NVENC, nếu hụt FFmpeg tự động báo lỗi nhưng ta có thể để cờ mặc định
                # Để đảm bảo tính tương thích vạn năng, ta tạm dùng libx264. 
                # (Trong tương lai có thể viết hàm probe phần cứng chi tiết hơn nếu cần)
                vcodec = 'libx264'
            
            if self.rtsp_url_1 == self.rtsp_url_2:
                # Nếu chỉ có 1 camera (đang test), ta lấy 1 luồng mạng rồi nhân bản (split) trong nội bộ máy 
                # để 2 khung hình đồng bộ tuyệt đối 100%, không bị lệch thời gian.
                command = [
                    'ffmpeg', '-y', '-rtsp_transport', 'tcp',
                    '-i', self.rtsp_url_1,
                    '-filter_complex', 
                    '[0:v]split=2[main][pip_raw]; [pip_raw]scale=iw/3:-1[pip]; [main][pip]overlay=main_w-overlay_w-10:10',
                    '-c:v', vcodec, '-b:v', '2000k', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-movflags', '+faststart',
                    filepath
                ]
            else:
                # Nếu là 2 camera thật hoặc camera 2 mắt,
                # Thêm cờ đồng bộ thời gian thực để ép máy chủ FFmpeg khớp 2 luồng song song
                command = [
                    'ffmpeg', '-y', 
                    '-use_wallclock_as_timestamps', '1', '-rtsp_transport', 'tcp', '-i', self.rtsp_url_1,
                    '-use_wallclock_as_timestamps', '1', '-rtsp_transport', 'tcp', '-i', self.rtsp_url_2,
                    '-filter_complex', 
                    '[1:v]scale=iw/3:-1[pip]; [0:v][pip]overlay=main_w-overlay_w-10:10',
                    '-c:v', vcodec, '-b:v', '2000k', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-movflags', '+faststart',
                    filepath
                ]
            self._launch_ffmpeg(command)
            self.current_files.append(filepath)
            
        print(f"🎬 Bắt đầu ghi hình ({self.record_mode}) Đơn hàng: {waybill_code}")
        for f in self.current_files:
            print(f"📁 Lưu tại: {f}")
            
        return self.current_files

    def _launch_ffmpeg(self, checksed_cmd):
        # Chạy ẩn FFmpeg
        p = subprocess.Popen(
            checksed_cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        self.processes.append(p)

    def stop_recording(self):
        if not self.processes:
            return
            
        print(f"🛑 Đã ĐÓNG GÓI xong, lưu chuỗi video thành công!")
        for p in self.processes:
            try:
                p.communicate(b'q\n', timeout=5)
            except subprocess.TimeoutExpired:
                p.terminate()
                
        self.processes = []
        # Return danh sách file để lưu CSDL
        saved_files = self.current_files
        self.current_files = []
        return saved_files
