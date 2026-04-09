/**
 * V-Pack Monitor - CamDongHang v1.10.0
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useRef, useState, useEffect } from 'react';
import { X, Play, Pause, Camera, Download, Volume2, VolumeX } from 'lucide-react';

function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function VideoPlayerModal({ isOpen, videoUrl, waybillCode, onClose }) {
  const videoRef = useRef(null);
  const progressRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [buffered, setBuffered] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const hideTimer = useRef(null);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === ' ' && videoRef.current) {
        e.preventDefault();
        togglePlay();
      }
      if (e.key === 'ArrowLeft' && videoRef.current) videoRef.current.currentTime -= 5;
      if (e.key === 'ArrowRight' && videoRef.current) videoRef.current.currentTime += 5;
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  const scheduleHide = () => {
    setShowControls(true);
    clearTimeout(hideTimer.current);
    hideTimer.current = setTimeout(() => {
      if (videoRef.current && !videoRef.current.paused) {
        setShowControls(false);
      }
    }, 3000);
  };

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

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    setCurrentTime(videoRef.current.currentTime);
    if (videoRef.current.buffered.length > 0) {
      setBuffered(videoRef.current.buffered.end(videoRef.current.buffered.length - 1));
    }
  };

  const handleLoadedMetadata = () => {
    if (!videoRef.current) return;
    setDuration(videoRef.current.duration);
  };

  const handleProgressClick = (e) => {
    if (!progressRef.current || !videoRef.current) return;
    const rect = progressRef.current.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    videoRef.current.currentTime = pos * duration;
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !videoRef.current.muted;
    setIsMuted(videoRef.current.muted);
  };

  const handleVolumeChange = (e) => {
    if (!videoRef.current) return;
    const vol = parseFloat(e.target.value);
    videoRef.current.volume = vol;
    setVolume(vol);
    setIsMuted(vol === 0);
  };

  const takeSnapshot = () => {
    if (!videoRef.current) return;
    try {
      const canvas = document.createElement('canvas');
      const video = videoRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
      const a = document.createElement('a');
      a.href = dataUrl;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      a.download = `Snapshot_${waybillCode}_${timestamp}.jpg`;
      a.click();
    } catch (err) {
      console.error("Snapshot error:", err);
    }
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="bg-[#0f172a] border border-white/10 rounded-2xl shadow-2xl w-full max-w-5xl overflow-hidden relative" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className={`flex items-center justify-between p-4 bg-black/40 border-b border-white/10 absolute top-0 left-0 right-0 z-10 transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
          <h3 className="text-white font-bold tracking-wider">Ma van don: <span className="text-blue-400">{waybillCode}</span></h3>
          <div className="flex items-center gap-2">
            <span className="text-white/60 text-xs font-mono">{formatTime(currentTime)} / {formatTime(duration)}</span>
            <button onClick={onClose} className="p-2 bg-white/10 hover:bg-rose-500/80 rounded-lg text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Video */}
        <div className="relative aspect-video w-full flex items-center justify-center bg-black group"
             onMouseMove={scheduleHide}
             onMouseLeave={() => { if (isPlaying) setShowControls(false); }}>
          <video
            ref={videoRef}
            src={videoUrl}
            className="w-full h-full object-contain"
            controls={false}
            autoPlay
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onClick={togglePlay}
          />

          {/* Big play button when paused */}
          {!isPlaying && (
            <button onClick={togglePlay} className="absolute inset-0 flex items-center justify-center">
              <div className="p-6 bg-blue-600/80 rounded-full text-white shadow-2xl hover:bg-blue-500 transition-all hover:scale-110">
                <Play className="w-12 h-12" fill="currentColor" />
              </div>
            </button>
          )}

          {/* Controls */}
          <div className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/60 to-transparent px-4 pb-4 pt-20 transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>

            {/* Progress bar */}
            <div ref={progressRef} onClick={handleProgressClick} className="w-full h-2 bg-white/10 rounded-full cursor-pointer mb-3 group/progress relative">
              <div className="absolute inset-y-0 left-0 bg-white/20 rounded-full" style={{ width: `${(buffered / (duration || 1)) * 100}%` }} />
              <div className="absolute inset-y-0 left-0 bg-blue-500 rounded-full" style={{ width: `${progress}%` }} />
              <div className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-400 rounded-full shadow-lg opacity-0 group-hover/progress:opacity-100 transition-opacity" style={{ left: `calc(${progress}% - 8px)` }} />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button onClick={togglePlay} className="p-2 bg-blue-600 hover:bg-blue-500 rounded-full text-white transition-transform hover:scale-110 shadow-lg shadow-blue-500/30">
                  {isPlaying ? <Pause className="w-5 h-5" fill="currentColor" /> : <Play className="w-5 h-5 ml-0.5" fill="currentColor" />}
                </button>

                <div className="flex items-center gap-1">
                  <button onClick={toggleMute} className="p-1 text-white/70 hover:text-white transition-colors">
                    {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                  </button>
                  <input
                    type="range" min="0" max="1" step="0.05"
                    value={isMuted ? 0 : volume}
                    onChange={handleVolumeChange}
                    className="w-20 h-1 accent-blue-500 cursor-pointer"
                  />
                </div>

                <span className="text-white/80 text-sm font-mono">{formatTime(currentTime)} / {formatTime(duration)}</span>

                <div className="flex bg-white/10 rounded-lg p-0.5 border border-white/5">
                  {[0.5, 1, 1.5, 2].map(speed => (
                    <button
                      key={speed}
                      onClick={() => setPlaybackRate(speed)}
                      className={`px-2 py-0.5 text-xs font-semibold rounded-md transition-colors ${playbackRate === speed ? 'bg-blue-500 text-white shadow' : 'text-slate-300 hover:text-white hover:bg-white/10'}`}
                    >
                      {speed}x
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={takeSnapshot}
                  className="p-2 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-white border border-emerald-500/30 rounded-lg flex items-center gap-1.5 transition-all font-semibold px-3 text-sm"
                  title="Chup khung hinh hien tai"
                >
                  <Camera className="w-4 h-4" />
                  <span className="hidden md:inline">Snapshot</span>
                </button>

                <a
                  href={videoUrl}
                  download
                  className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors border border-white/5"
                  title="Tai video xuong"
                >
                  <Download className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
