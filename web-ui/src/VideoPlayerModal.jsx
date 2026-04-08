import React, { useRef, useState, useEffect } from 'react';
import { X, Play, Pause, Camera, Settings, Download, Forward, Rewind } from 'lucide-react';

export default function VideoPlayerModal({ isOpen, videoUrl, waybillCode, onClose }) {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showControls, setShowControls] = useState(true);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  if (!isOpen) return null;

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const changeSpeed = (rate) => {
    setPlaybackRate(rate);
  };

  const takeSnapshot = () => {
    if (!videoRef.current) return;
    
    try {
      const canvas = document.createElement('canvas');
      const video = videoRef.current;
      
      // Set canvas dimensions to match video source
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
      
      // Create download link
      const a = document.createElement('a');
      a.href = dataUrl;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      a.download = `Snapshot_${waybillCode}_${timestamp}.jpg`;
      a.click();
    } catch (err) {
      console.error("Snapshot error:", err);
      alert("Không thể chụp ảnh. Vui lòng thử lại.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4">
      <div className="bg-[#0f172a] border border-white/10 rounded-2xl shadow-2xl w-full max-w-5xl overflow-hidden relative">
        <div className="flex items-center justify-between p-4 bg-black/40 border-b border-white/10 absolute top-0 left-0 right-0 z-10 opacity-100 hover:opacity-100 transition-opacity">
          <h3 className="text-white font-bold tracking-wider">Mã vận đơn: <span className="text-blue-400">{waybillCode}</span></h3>
          <button onClick={onClose} className="p-2 bg-white/10 hover:bg-rose-500/80 rounded-lg text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="relative aspect-video w-full flex items-center justify-center bg-black group"
             onMouseEnter={() => setShowControls(true)}
             onMouseLeave={() => setShowControls(false)}>
          <video 
            ref={videoRef}
            src={videoUrl}
            className="w-full h-full object-contain"
            controls={false}
            autoPlay
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onClick={togglePlay}
          />
          
          {/* Custom Controls Overlay */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4 pt-16 transition-opacity duration-300 flex flex-col gap-2">
             <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <button onClick={togglePlay} className="p-3 bg-blue-600 hover:bg-blue-500 rounded-full text-white transition-transform hover:scale-110 shadow-lg shadow-blue-500/30">
                    {isPlaying ? <Pause className="w-6 h-6" fill="currentColor" /> : <Play className="w-6 h-6 ml-1" fill="currentColor" />}
                  </button>
                  
                  <div className="flex bg-white/10 rounded-lg p-1 border border-white/5">
                    {[0.5, 1, 1.5, 2].map(speed => (
                      <button 
                        key={speed}
                        onClick={() => changeSpeed(speed)}
                        className={`px-3 py-1 text-sm font-semibold rounded-md transition-colors ${playbackRate === speed ? 'bg-blue-500 text-white shadow' : 'text-slate-300 hover:text-white hover:bg-white/10'}`}
                      >
                        {speed}x
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button 
                    onClick={takeSnapshot}
                    className="p-2 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-white border border-emerald-500/30 rounded-lg flex items-center gap-2 transition-all font-semibold px-4"
                    title="Chụp khung hình hiện tại"
                  >
                    <Camera className="w-5 h-5" />
                    <span className="hidden md:inline">Snapshot</span>
                  </button>

                  <a 
                    href={videoUrl}
                    download
                    className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors border border-white/5"
                    title="Tải video xuống"
                  >
                    <Download className="w-5 h-5" />
                  </a>
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
