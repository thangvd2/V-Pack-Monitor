/**
 * V-Pack Monitor - CamDongHang
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 */

import React from 'react';

interface MtxFallbackProps {
  onRetry?: () => void;
}

const MtxFallback: React.FC<MtxFallbackProps> = ({ onRetry }) => {
  return (
    <div className="w-full h-full flex items-center justify-center" style={{ background: '#09090b' }}>
      <div className="text-center">
        <div className="text-4xl mb-3">📡</div>
        <p className="text-slate-400 text-sm font-medium">MediaMTX chưa khởi động</p>
        <p className="text-slate-500 text-xs mt-1">Live view cần MediaMTX chạy ở port 8889</p>
        {onRetry && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRetry();
            }}
            className="mt-4 px-4 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-semibold transition-all"
          >
            Thử lại
          </button>
        )}
      </div>
    </div>
  );
};

export default MtxFallback;
