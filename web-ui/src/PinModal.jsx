/**
 * V-Pack Monitor - CamDongHang v1.5.0
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useState } from 'react';
import axios from 'axios';
import { Lock, ShieldAlert } from 'lucide-react';

const API_BASE = window.location.hostname === 'localhost' && ['3000', '3001', '5173'].includes(window.location.port) 
  ? 'http://localhost:8001' 
  : window.location.origin;

export default function PinModal({ isOpen, onSuccess, onCancel }) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!pin) return;
    
    setLoading(true);
    setError('');
    
    try {
      const res = await axios.post(`${API_BASE}/api/verify-pin`, { pin });
      if (res.data.status === 'success') {
        setPin(''); // Xóa trắng PIN sau khi login thành công
        onSuccess();
      } else {
        setError(res.data.message || 'Mã PIN sai!');
        setPin(''); // Reset
      }
    } catch (err) {
      setError('Lỗi kết nối Server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="bg-[#0f172a] border border-red-500/30 rounded-2xl shadow-2xl shadow-red-900/20 w-full max-w-sm p-6 relative overflow-hidden">
        {/* Đèn nháy cảnh báo */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-8 bg-gradient-to-b from-red-500/20 to-transparent pointer-events-none"></div>

        <button 
          onClick={onCancel}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
        >
          ✕
        </button>
        
        <div className="flex flex-col items-center text-center mt-2 mb-6">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4 border border-red-500/30">
            <ShieldAlert className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Quyền Quản Trị Hệ Thống</h2>
          <p className="text-sm text-slate-400">Bạn đang tiến hành thao tác cần bảo mật. Vui lòng nhập mã PIN để cấp quyền.</p>
        </div>

        {error && (
          <div className="mb-4 text-sm font-semibold text-center text-red-400 bg-red-500/10 py-2 rounded-lg border border-red-500/20">
            {error}
          </div>
        )}

        <form onSubmit={handleVerify}>
          <div className="mb-6 relative">
            <Lock className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input 
              type="password" 
              autoFocus
              placeholder="Nhập mã PIN..." 
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="w-full bg-black/50 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-white text-center tracking-[0.5em] text-lg font-mono focus:outline-none focus:border-red-500/50"
            />
          </div>

          <button 
            type="submit"
            disabled={loading || !pin}
            className="w-full bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-xl transition-colors disabled:opacity-50"
          >
            {loading ? 'ĐANG KIỂM TRA...' : 'MỞ KHÓA'}
          </button>
        </form>
      </div>
    </div>
  );
}
