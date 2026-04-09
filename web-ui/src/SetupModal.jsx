/**
 * V-Pack Monitor - CamDongHang v1.9.0
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useState } from 'react';
import axios from 'axios';
import { Settings, Save, AlertCircle, Trash2 } from 'lucide-react';

const API_BASE = window.location.hostname === 'localhost' && ['3000', '3001', '5173'].includes(window.location.port) 
  ? 'http://localhost:8001' 
  : window.location.origin;

export default function SetupModal({ isOpen, onSaved, onCancel, currentStation = {}, isNewStation = false, initialSettings = {} }) {
  const [name, setName] = useState(currentStation.name || 'Bàn Gói Hàng ' + Math.floor(Math.random() * 100));
  const [ip1, setIp1] = useState(currentStation.ip_camera_1 || '');
  const [ip2, setIp2] = useState(currentStation.ip_camera_2 || '');
  const [safetyCode, setSafetyCode] = useState(currentStation.safety_code || '');
  const [cameraBrand, setCameraBrand] = useState(currentStation.camera_brand || 'imou');
  const [cameraMode, setCameraMode] = useState(currentStation.camera_mode || 'single');
  const [macAddress, setMacAddress] = useState(currentStation.mac_address || '');
  const [discovering, setDiscovering] = useState(false);
  const [discoverResult, setDiscoverResult] = useState('');
  const [keepDays, setKeepDays] = useState(initialSettings.RECORD_KEEP_DAYS || 7);
  
  // Cloud Sync Settings
  const [cloudProvider, setCloudProvider] = useState(initialSettings.CLOUD_PROVIDER || 'NONE');
  const [gDriveFolderId, setGDriveFolderId] = useState(initialSettings.GDRIVE_FOLDER_ID || '');
  const [gDriveCreds, setGDriveCreds] = useState('');
  const [s3Endpoint, setS3Endpoint] = useState(initialSettings.S3_ENDPOINT || '');
  const [s3Access, setS3Access] = useState(initialSettings.S3_ACCESS_KEY || '');
  const [s3Secret, setS3Secret] = useState(initialSettings.S3_SECRET_KEY || '');
  const [s3Bucket, setS3Bucket] = useState(initialSettings.S3_BUCKET_NAME || '');

  // Telegram Settings
  const [tgBotToken, setTgBotToken] = useState(initialSettings.TELEGRAM_BOT_TOKEN || '');
  const [tgChatId, setTgChatId] = useState(initialSettings.TELEGRAM_CHAT_ID || '');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSave = async () => {
    if (!name || !ip1 || !safetyCode) {
      setError('Tên trạm, IP Camera 1 và Safety Code không được để trống.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // 1. Lưu Global Settings
      await axios.post(`${API_BASE}/api/settings`, {
        RECORD_KEEP_DAYS: parseInt(keepDays),
        CLOUD_PROVIDER: cloudProvider,
        GDRIVE_FOLDER_ID: gDriveFolderId,
        S3_ENDPOINT: s3Endpoint,
        S3_ACCESS_KEY: s3Access,
        S3_SECRET_KEY: s3Secret,
        S3_BUCKET_NAME: s3Bucket,
        TELEGRAM_BOT_TOKEN: tgBotToken,
        TELEGRAM_CHAT_ID: tgChatId
      });

      // Nếu có nhập credentials.json thì API up lên
      if (cloudProvider === 'GDRIVE' && gDriveCreds.trim()) {
        const blob = new Blob([gDriveCreds], { type: 'application/json' });
        const formData = new FormData();
        formData.append('file', blob, 'credentials.json');
        await axios.post(`${API_BASE}/api/credentials`, formData);
      }

      // 2. Lưu Station
      const payload = {
        name,
        ip_camera_1: ip1,
        ip_camera_2: ip2,
        safety_code: safetyCode,
        camera_mode: cameraMode,
        camera_brand: cameraBrand,
        mac_address: macAddress
      };

      if (isNewStation) {
        await axios.post(`${API_BASE}/api/stations`, payload);
      } else {
        await axios.put(`${API_BASE}/api/stations/${currentStation.id}`, payload);
      }

      onSaved(); 
    } catch (err) {
      console.error(err);
      setError('Lỗi kết nối tới Server. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
      if (window.confirm("Xóa trạm này khỏi hệ thống? Các video cũ vẫn sẽ được giữ lại theo mã vận đơn.")) {
          try {
              setLoading(true);
              await axios.delete(`${API_BASE}/api/stations/${currentStation.id}`);
              onSaved();
          } catch (err) {
              setLoading(false);
              setError("Không thể xóa trạm lúc này!");
          }
      }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0f172a] border border-white/10 rounded-2xl shadow-2xl w-full max-w-lg p-6 relative overflow-hidden">
        {/* Glow background effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-32 bg-blue-500/20 blur-3xl opacity-50 rounded-full pointer-events-none"></div>
        
        {onCancel && (
          <button 
            onClick={onCancel}
            className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        )}
        
        <div className="relative z-10 flex items-center gap-3 mb-6">
          <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-400/30">
            <Settings className="w-6 h-6 text-blue-400" />
          </div>
          <div className="flex-1 flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white">{isNewStation ? "Thêm Trạm Ghi Hình Mới" : "Cài đặt Trạm này"}</h2>
              <p className="text-sm text-slate-400">Thiết lập kết nối Camera và Hệ thống</p>
            </div>
            {!isNewStation && (
                 <button onClick={handleDelete} className="p-2 bg-rose-500/20 text-rose-400 rounded-lg hover:bg-rose-500 hover:text-white transition">
                    <Trash2 className="w-5 h-5"/>
                 </button>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center gap-2 text-sm text-red-200">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          
          <div className="p-4 bg-white/5 rounded-xl border border-white/10 space-y-4">
              <h3 className="text-sm font-semibold text-blue-300 uppercase tracking-wider">Cấu hình Trạm</h3>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Tên Trạm Đóng Hàng</label>
                <input 
                  type="text" 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">IP Camera Chính (Luồng Web)</label>
                <input 
                  type="text" 
                  placeholder="VD: 192.168.1.10" 
                  value={ip1}
                  onChange={(e) => setIp1(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">IP Camera Phụ (Chỉ dành cho chế độ DUAL / PIP từ 2 thiết bị)</label>
                <input 
                  type="text" 
                  placeholder="Bỏ trống nếu không dùng 2 camera" 
                  value={ip2}
                  onChange={(e) => setIp2(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Hãng Camera / RTSP Profile</label>
                <select 
                  value={cameraBrand}
                  onChange={(e) => setCameraBrand(e.target.value)}
                  className="w-full bg-[#1e293b] border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 appearance-none mb-4"
                >
                  <option value="imou">Imou / Dahua (Mặc định)</option>
                  <option value="tenda">Tenda (Series CH/TD)</option>
                  <option value="ezviz">EZVIZ (Hikvision)</option>
                  <option value="tapo">TP-Link Tapo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Mật khẩu RTSP / Safety Code / Verification Code</label>
                <input 
                  type="password" 
                  placeholder="Mật khẩu thiết bị (Tuỳ theo hãng)" 
                  value={safetyCode}
                  onChange={(e) => setSafetyCode(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 "
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">MAC Address (Tự động tìm lại Camera khi đổi IP)</label>
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    placeholder="VD: AA:BB:CC:DD:EE:FF (in trên tem đáy Camera)" 
                    value={macAddress}
                    onChange={(e) => setMacAddress(e.target.value)}
                    onBlur={(e) => {
                      const raw = e.target.value.replace(/[\s:\-\.]/g, '').toUpperCase();
                      if (raw.length === 12) {
                        setMacAddress(raw.match(/.{2}/g).join(':'));
                      }
                    }}
                    className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50"
                  />
                  {macAddress && (
                    <button 
                      type="button"
                      onClick={async () => {
                        const raw = macAddress.replace(/[\s:\-\.]/g, '').toUpperCase();
                        if (raw.length !== 12) {
                          setDiscoverResult('❌ MAC Address không hợp lệ (cần 12 ký tự hex).');
                          return;
                        }
                        setDiscovering(true);
                        setDiscoverResult('');
                        try {
                          const formattedMac = raw.match(/.{2}/g).join(':');
                          const res = await axios.get(`${API_BASE}/api/discover-mac?mac=${encodeURIComponent(formattedMac)}`);
                          const data = res.data;
                          if (data.status === 'found') {
                            setDiscoverResult(`✅ Tìm thấy IP: ${data.ip}`);
                            setIp1(data.ip);
                          } else {
                            setDiscoverResult(`❌ Không tìm thấy camera trên mạng.`);
                          }
                        } catch {
                          setDiscoverResult('❌ Lỗi khi quét mạng.');
                        } finally {
                          setDiscovering(false);
                        }
                      }}
                      disabled={discovering}
                      className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50 whitespace-nowrap"
                    >
                      {discovering ? '⏳ Đang quét...' : '🔍 Quét IP'}
                    </button>
                  )}
                </div>
                {discoverResult && (
                  <p className="mt-1 text-xs text-slate-300">{discoverResult}</p>
                )}
                <p className="mt-1 text-xs text-slate-500">Để trống nếu không cần tự động tìm lại IP khi mạng thay đổi.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Chế độ ghi Video</label>
                <select 
                  value={cameraMode}
                  onChange={(e) => setCameraMode(e.target.value)}
                  className="w-full bg-[#1e293b] border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 appearance-none"
                >
                  <option value="single">SINGLE (Chỉ ghi 1 luồng chuẩn)</option>
                  <option value="pip">PIP (Ghép 2 Máy - Picture In Picture)</option>
                  <option value="pip_sim">PIP SIMULATION (Ghép thử nghiệm từ 1 Mắt làm 2 khung hình)</option>
                  <option value="dual_file">DUAL_FILE (Ghi 2 File mp4 độc lập từ 2 Máy)</option>
                  <option value="dual_file_sim">DUAL SIMULATION (Ghi 2 File mp4 độc lập từ 1 Mắt)</option>
                </select>
              </div>
          </div>

          <div className="p-4 bg-white/5 rounded-xl border border-white/10 space-y-4">
              <h3 className="text-sm font-semibold text-emerald-300 uppercase tracking-wider">Hệ thống chung</h3>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Tự động xoá Video cũ hơn</label>
                <select 
                  value={keepDays}
                  onChange={(e) => setKeepDays(e.target.value)}
                  className="w-full bg-[#1e293b] border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none appearance-none"
                >
                  <option value="3">3 Ngày</option>
                  <option value="7">7 Ngày</option>
                  <option value="15">15 Ngày</option>
                  <option value="30">30 Ngày</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Dịch vụ Lưu Trữ Đám Mây (Cloud Sync)</label>
                <select 
                  value={cloudProvider}
                  onChange={(e) => setCloudProvider(e.target.value)}
                  className="w-full bg-[#1e293b] border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none appearance-none"
                >
                  <option value="NONE">Chưa Kích Hoạt</option>
                  <option value="GDRIVE">Google Drive (Khuyên Dùng)</option>
                  <option value="S3">S3 / R2 (Amazon / Cloudflare)</option>
                </select>
              </div>

              {cloudProvider === 'GDRIVE' && (
                <div className="space-y-4 pt-2 border-t border-white/5">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">ID Thư Mục Google Drive (Bỏ trống = Root)</label>
                    <input 
                      type="text" 
                      value={gDriveFolderId}
                      onChange={(e) => setGDriveFolderId(e.target.value)}
                      className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500/50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Nội dung tệp Service Account (credentials.json)</label>
                    <textarea 
                      placeholder="Mở file credentials.json bằng Notepad, copy toàn bộ chữ dán vào đây..." 
                      value={gDriveCreds}
                      onChange={(e) => setGDriveCreds(e.target.value)}
                      rows={4}
                      className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-xs font-mono focus:outline-none focus:border-blue-500/50"
                    ></textarea>
                  </div>
                </div>
              )}

              {cloudProvider === 'S3' && (
                <div className="space-y-4 pt-2 border-t border-white/5">
                  <input type="text" placeholder="Endpoint URL (VD: https://xxx.r2.cloudflarestorage.com)" value={s3Endpoint} onChange={(e) => setS3Endpoint(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm" />
                  <input type="text" placeholder="Access Key" value={s3Access} onChange={(e) => setS3Access(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm" />
                  <input type="password" placeholder="Secret Key" value={s3Secret} onChange={(e) => setS3Secret(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm" />
                  <input type="text" placeholder="Bucket Name" value={s3Bucket} onChange={(e) => setS3Bucket(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm" />
                </div>
              )}
          </div>

          <div className="p-4 bg-white/5 rounded-xl border border-white/10 space-y-4 mt-4">
              <h3 className="text-sm font-semibold text-blue-300 uppercase tracking-wider">Thông Báo Telegram (Cảnh báo lỗi mạng / Năng suất)</h3>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Bot Token</label>
                <input 
                  type="text" 
                  placeholder="VD: 123456789:ABCdefGHIjklmNOPqrstuv" 
                  value={tgBotToken}
                  onChange={(e) => setTgBotToken(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Chat ID (Sẽ gửi cảnh báo vào nhóm này)</label>
                <input 
                  type="text" 
                  placeholder="VD: -4029419241" 
                  value={tgChatId}
                  onChange={(e) => setTgChatId(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50"
                />
              </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          {onCancel && (
            <button 
              onClick={onCancel}
              disabled={loading}
              className="flex-1 bg-white/5 hover:bg-white/10 text-white font-semibold py-3 px-4 rounded-xl transition-colors disabled:opacity-50"
            >
              HỦY BỎ
            </button>
          )}
          
          <button 
            onClick={handleSave}
            disabled={loading}
            className="flex-[2] bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
            ) : (
              <>
                <Save className="w-5 h-5" />
                LƯU TRẠM NÀY
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
