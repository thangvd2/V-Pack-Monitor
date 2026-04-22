/**
 * V-Pack Monitor - CamDongHang
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 */

import React from 'react';

export default function MtxFallback() {
  return (
    <div className="w-full h-full flex items-center justify-center" style={{ background: '#09090b' }}>
      <div className="text-center">
        <div className="text-4xl mb-3">📡</div>
        <p className="text-slate-400 text-sm font-medium">MediaMTX chưa khởi động</p>
        <p className="text-slate-500 text-xs mt-1">Live view cần MediaMTX chạy ở port 8889</p>
      </div>
    </div>
  );
}
