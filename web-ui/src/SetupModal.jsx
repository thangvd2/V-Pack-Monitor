/**
 * V-Pack Monitor - CamDongHang v2.3.1
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import axios from 'axios';
import { Settings, Save, AlertCircle, Trash2, Eye, EyeOff, ChevronDown, ChevronUp, Wifi, WifiOff, Loader2 } from 'lucide-react';

const API_BASE = window.location.hostname === 'localhost' && ['3000', '3001', '5173'].includes(window.location.port)
  ? 'http://localhost:8001'
  : window.location.origin;

const isValidIPv4 = (ip) => {
  const m = ip.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
  if (!m) return false;
  return [m[1], m[2], m[3], m[4]].every(o => { const n = parseInt(o); return n >= 0 && n <= 255; });
};

const isValidIPv6 = (ip) => {
  const s = ip.trim();
  if (!s) return false;
  const parts = s.split(':');
  const hasDoubleColon = s.includes('::');
  if (hasDoubleColon && s.split('::').length - 1 > 1) return false;
  const maxParts = hasDoubleColon ? 9 : 8;
  if (parts.length < 2 || parts.length > maxParts) return false;
  for (const part of parts) {
    if (part === '') continue;
    if (!/^[0-9a-fA-F]{1,4}$/.test(part)) return false;
  }
  return true;
};

const isValidIP = (ip) => isValidIPv4(ip) || isValidIPv6(ip);

const isLANIPv4 = (ip) => {
  if (!isValidIPv4(ip)) return false;
  const [a, b] = ip.split('.').map(Number);
  return a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
};

const isLANIPv6 = (ip) => {
  const l = ip.toLowerCase();
  return l.startsWith('fd') || l.startsWith('fc') || l.startsWith('fe80') || l === '::1';
};

const isLANIP = (ip) => isLANIPv4(ip) || isLANIPv6(ip);

const isReservedIP = (ip) => {
  if (isValidIPv4(ip)) {
    const [a] = ip.split('.').map(Number);
    return ip === '0.0.0.0' || a === 127 || ip === '255.255.255.255';
  }
  return ip === '::' || ip === '::1';
};

const isValidMAC = (mac) => {
  const raw = mac.replace(/[\s:\-\.]/g, '').toUpperCase();
  if (raw.length !== 12 || !/^[0-9A-F]{12}$/.test(raw)) return false;
  if (raw === '000000000000' || raw === 'FFFFFFFFFFFF') return false;
  return true;
};

const CAMERA_MODE_DESC = {
  single: 'Ghi 1 luồng từ 1 camera',
  pip: 'Ghép hình-in-picture từ 2 camera (hoặc 1 camera 2 mắt)',
  pip_sim: 'Ghép PIP thử nghiệm từ 1 camera',
  dual_file: 'Ghi 2 file riêng từ 2 camera (hoặc 1 camera 2 mắt)',
  dual_file_sim: 'Ghi 2 file riêng từ 1 camera',
};

const MODES_NEED_IP2 = ['dual_file', 'pip'];

function ErrorHint({ show, msg }) {
  if (!show) return null;
  return <p className="mt-1 text-xs text-red-400">{msg}</p>;
}

function WarningHints({ warnings }) {
  if (!warnings || warnings.length === 0) return null;
  return (
    <div className="mt-2 p-2 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-300 space-y-0.5">
      {warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
    </div>
  );
}

export default function SetupModal({ isOpen, onSaved, onCancel, currentStation = {}, isNewStation = false, initialSettings = {} }) {
  const [name, setName] = useState(currentStation.name || '');
  const [ip1, setIp1] = useState(currentStation.ip_camera_1 || '');
  const [ip2, setIp2] = useState(currentStation.ip_camera_2 || '');
  const [safetyCode, setSafetyCode] = useState(currentStation.safety_code || '');
  const [cameraBrand, setCameraBrand] = useState(currentStation.camera_brand || 'imou');
  const [cameraMode, setCameraMode] = useState(currentStation.camera_mode || 'single');
  const [macAddress, setMacAddress] = useState(currentStation.mac_address || '');
  const [discovering, setDiscovering] = useState(false);
  const [discoverResult, setDiscoverResult] = useState('');
  const [keepDays, setKeepDays] = useState(initialSettings.RECORD_KEEP_DAYS || 7);
  const [cloudProvider, setCloudProvider] = useState(initialSettings.CLOUD_PROVIDER || 'NONE');
  const [gDriveFolderId, setGDriveFolderId] = useState(initialSettings.GDRIVE_FOLDER_ID || '');
  const [gDriveCreds, setGDriveCreds] = useState('');
  const [s3Endpoint, setS3Endpoint] = useState(initialSettings.S3_ENDPOINT || '');
  const [s3Access, setS3Access] = useState(initialSettings.S3_ACCESS_KEY || '');
  const [s3Secret, setS3Secret] = useState(initialSettings.S3_SECRET_KEY || '');
  const [s3Bucket, setS3Bucket] = useState(initialSettings.S3_BUCKET_NAME || '');
  const [tgBotToken, setTgBotToken] = useState(initialSettings.TELEGRAM_BOT_TOKEN || '');
  const [tgChatId, setTgChatId] = useState(initialSettings.TELEGRAM_CHAT_ID || '');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSafetyCode, setShowSafetyCode] = useState(false);
  const [testingIp, setTestingIp] = useState(false);
  const [testIpResult, setTestIpResult] = useState(null);
  const [collapsed, setCollapsed] = useState({ system: false, telegram: false });
  const [dirty, setDirty] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [touched, setTouched] = useState({});
  const conflictTimerRef = useRef(null);

  useEffect(() => {
    if (!isOpen) {
      if (conflictTimerRef.current) clearTimeout(conflictTimerRef.current);
      return;
    }
    const handler = (e) => { if (e.key === 'Escape') handleCancel(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, dirty]);

  const markDirty = useCallback(() => setDirty(true), []);

  const touch = useCallback((field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  }, []);

  if (!isOpen) return null;

  const excludeId = currentStation?.id || 0;
  const showIp2 = MODES_NEED_IP2.includes(cameraMode);

  const validate = () => {
    const errs = [];
    if (!name || !name.trim()) errs.push('name');
    else if (name.trim().length < 2 || name.trim().length > 50) errs.push('name_len');
    if (!ip1 || !ip1.trim()) errs.push('ip1');
    else if (!isValidIP(ip1.trim())) errs.push('ip1_fmt');
    else if (isReservedIP(ip1.trim())) errs.push('ip1_reserved');
    if (ip2 && ip2.trim() && !isValidIP(ip2.trim())) errs.push('ip2_fmt');
    if (!safetyCode || !safetyCode.trim()) errs.push('safety');
    else if (safetyCode.trim().length < 4) errs.push('safety_len');
    if (macAddress && macAddress.trim() && !isValidMAC(macAddress.trim())) errs.push('mac_fmt');
    if (cloudProvider === 'GDRIVE' && gDriveCreds.trim()) {
      try { JSON.parse(gDriveCreds); } catch { errs.push('gdrive_json'); }
    }
    if (cloudProvider === 'S3' && s3Endpoint.trim() && !/^https?:\/\//.test(s3Endpoint.trim())) errs.push('s3_url');
    return errs;
  };

  const errors = validate();
  const hasErrors = errors.length > 0;

  const fieldBorder = (fieldName, hasError) => {
    if (!touched[fieldName]) return 'border-white/10';
    return hasError ? 'border-red-500/60' : 'border-emerald-500/40';
  };

  const checkConflicts = useCallback(() => {
    if (conflictTimerRef.current) clearTimeout(conflictTimerRef.current);
    conflictTimerRef.current = setTimeout(async () => {
      try {
        const params = new URLSearchParams();
        if (ip1) params.set('ip', ip1);
        if (ip2 && ip2.trim()) params.set('ip2', ip2);
        if (macAddress) params.set('mac', macAddress);
        if (name) params.set('name', name);
        params.set('exclude_id', excludeId);
        const res = await axios.get(`${API_BASE}/api/stations/check-conflict?${params}`);
        setWarnings(res.data.warnings || []);
      } catch { setWarnings([]); }
    }, 300);
  }, [ip1, ip2, macAddress, name, excludeId]);

  const handleTestIp = async () => {
    if (!ip1 || !isValidIP(ip1)) return;
    setTestingIp(true);
    setTestIpResult(null);
    try {
      const res = await axios.get(`${API_BASE}/api/ping?ip=${encodeURIComponent(ip1)}`);
      if (res.data.reachable) {
        setTestIpResult({ ok: true, msg: `Reachable (${ip1})` });
      } else {
        setTestIpResult({ ok: false, msg: 'Unreachable — camera không phản hồi' });
      }
    } catch {
      setTestIpResult({ ok: false, msg: 'Lỗi kết nối server' });
    } finally {
      setTestingIp(false);
    }
  };

  const handleSave = async () => {
    setTouched({ name: true, ip1: true, ip2: true, safety: true, mac: true });
    if (hasErrors) {
      setError('Vui lòng sửa các lỗi trước khi lưu.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams();
      if (ip1) params.set('ip', ip1);
      if (ip2 && ip2.trim()) params.set('ip2', ip2);
      if (macAddress) params.set('mac', macAddress);
      if (name) params.set('name', name);
      params.set('exclude_id', excludeId);
      const conflictRes = await axios.get(`${API_BASE}/api/stations/check-conflict?${params}`);
      const freshWarnings = conflictRes.data.warnings || [];
      setWarnings(freshWarnings);

      if (freshWarnings.length > 0) {
        const confirmed = window.confirm('Cảnh báo:\n' + freshWarnings.join('\n') + '\n\nTiếp tục lưu?');
        if (!confirmed) { setLoading(false); return; }
      }

      await axios.post(`${API_BASE}/api/settings`, {
        RECORD_KEEP_DAYS: parseInt(keepDays),
        CLOUD_PROVIDER: cloudProvider,
        GDRIVE_FOLDER_ID: gDriveFolderId,
        S3_ENDPOINT: s3Endpoint,
        S3_ACCESS_KEY: s3Access,
        S3_SECRET_KEY: s3Secret,
        S3_BUCKET_NAME: s3Bucket,
        TELEGRAM_BOT_TOKEN: tgBotToken,
        TELEGRAM_CHAT_ID: tgChatId,
      });

      if (cloudProvider === 'GDRIVE' && gDriveCreds.trim()) {
        const blob = new Blob([gDriveCreds], { type: 'application/json' });
        const formData = new FormData();
        formData.append('file', blob, 'credentials.json');
        await axios.post(`${API_BASE}/api/credentials`, formData);
      }

      const payload = {
        name: name.trim(),
        ip_camera_1: ip1.trim(),
        ip_camera_2: showIp2 ? ip2.trim() : '',
        safety_code: safetyCode.trim(),
        camera_mode: cameraMode,
        camera_brand: cameraBrand,
        mac_address: macAddress.trim(),
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
      } catch {
        setLoading(false);
        setError("Không thể xóa trạm lúc này!");
      }
    }
  };

  const handleCancel = () => {
    if (dirty) {
      const confirmed = window.confirm('Bạn có thay đổi chưa lưu. Thoát?');
      if (!confirmed) return;
    }
    onCancel();
  };

  const formatMac = (val) => {
    const raw = val.replace(/[\s:\-\.]/g, '').toUpperCase();
    if (raw.length === 12) return raw.match(/.{2}/g).join(':');
    return val;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === e.currentTarget) handleCancel(); }}
    >
      <div className="bg-[#0f172a] border border-white/10 rounded-2xl shadow-2xl w-full max-w-lg relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-32 bg-blue-500/20 blur-3xl opacity-50 rounded-full pointer-events-none"></div>

        <div className="relative z-10 flex items-center gap-3 p-6 pb-0">
          <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-400/30">
            <Settings className="w-6 h-6 text-blue-400" />
          </div>
          <div className="flex-1 flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white">{isNewStation ? "Thêm Trạm Ghi Hình Mới" : "Cài đặt Trạm này"}</h2>
              <p className="text-sm text-slate-400">Thiết lập kết nối Camera và Hệ thống</p>
            </div>
            <div className="flex items-center gap-2">
              {!isNewStation && (
                <button onClick={handleDelete} className="p-2 bg-rose-500/20 text-rose-400 rounded-lg hover:bg-rose-500 hover:text-white transition">
                  <Trash2 className="w-5 h-5" />
                </button>
              )}
              <button onClick={handleCancel} className="p-2 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-white/5">✕</button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center gap-2 text-sm text-red-200">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <div className="space-y-4 max-h-[62vh] overflow-y-auto p-6 pt-4">

          {/* SECTION: Cấu hình Trạm */}
          <div className="p-4 bg-white/5 rounded-xl border border-white/10 space-y-4">
            <h3 className="text-sm font-semibold text-blue-300 uppercase tracking-wider">Cấu hình Trạm</h3>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Tên Trạm Đóng Hàng</label>
              <input
                type="text"
                value={name}
                onChange={(e) => { setName(e.target.value); markDirty(); }}
                onBlur={() => { touch('name'); checkConflicts(); }}
                className={`w-full bg-black/40 border rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 ${fieldBorder('name', !name?.trim() || name.trim().length < 2 || name.trim().length > 50)}`}
              />
              <ErrorHint show={touched.name && !name?.trim()} msg="Tên trạm không được để trống" />
              <ErrorHint show={touched.name && name?.trim() && name.trim().length < 2} msg="Tên trạm cần ít nhất 2 ký tự" />
              <ErrorHint show={touched.name && name?.trim() && name.trim().length > 50} msg="Tên trạm tối đa 50 ký tự" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">IP Camera Chính (Luồng Web)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="VD: 192.168.1.10 hoặc fe80::1"
                  value={ip1}
                  onChange={(e) => { setIp1(e.target.value); markDirty(); setTestIpResult(null); }}
                  onBlur={() => { touch('ip1'); checkConflicts(); }}
                  className={`flex-1 bg-black/40 border rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 ${fieldBorder('ip1', !ip1?.trim() || !isValidIP(ip1?.trim()) || isReservedIP(ip1?.trim()))}`}
                />
                <button
                  onClick={handleTestIp}
                  disabled={testingIp || !ip1 || !isValidIP(ip1)}
                  className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-30 whitespace-nowrap flex items-center gap-1.5"
                >
                  {testingIp ? <Loader2 className="w-4 h-4 animate-spin" /> : (testIpResult?.ok ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />)}
                  {testingIp ? 'Testing...' : 'Test'}
                </button>
              </div>
              <ErrorHint show={touched.ip1 && !ip1?.trim()} msg="IP Camera không được để trống" />
              <ErrorHint show={touched.ip1 && ip1?.trim() && !isValidIP(ip1)} msg="IP không hợp lệ (cần IPv4 hoặc IPv6)" />
              <ErrorHint show={touched.ip1 && ip1?.trim() && isValidIP(ip1) && isReservedIP(ip1)} msg="IP này không hợp lệ (reserved/loopback)" />
              {testIpResult && (
                <p className={`mt-1 text-xs ${testIpResult.ok ? 'text-emerald-400' : 'text-red-400'}`}>
                  {testIpResult.ok ? '✅' : '❌'} {testIpResult.msg}
                </p>
              )}
            </div>

            {showIp2 && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">IP Camera Phụ (Để trống nếu dùng 1 camera có 2 mắt)</label>
                <input
                  type="text"
                  placeholder="Bỏ trống = dùng cùng camera chính"
                  value={ip2}
                  onChange={(e) => { setIp2(e.target.value); markDirty(); }}
                  onBlur={() => { touch('ip2'); checkConflicts(); }}
                  className={`w-full bg-black/40 border rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 ${fieldBorder('ip2', ip2 && ip2.trim() && !isValidIP(ip2))}`}
                />
                <ErrorHint show={touched.ip2 && ip2?.trim() && !isValidIP(ip2)} msg="IP không hợp lệ (cần IPv4 hoặc IPv6)" />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Hãng Camera / RTSP Profile</label>
              <select
                value={cameraBrand}
                onChange={(e) => { setCameraBrand(e.target.value); markDirty(); }}
                className="w-full bg-[#1e293b] border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 appearance-none"
              >
                <option value="imou">Imou / Dahua (Mặc định)</option>
                <option value="tenda">Tenda (Series CH/TD)</option>
                <option value="ezviz">EZVIZ (Hikvision)</option>
                <option value="tapo">TP-Link Tapo</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Mật khẩu RTSP / Safety Code</label>
              <div className="flex gap-2">
                <input
                  type={showSafetyCode ? "text" : "password"}
                  placeholder="Mật khẩu thiết bị"
                  value={safetyCode}
                  onChange={(e) => { setSafetyCode(e.target.value); markDirty(); }}
                  onBlur={() => touch('safety')}
                  className={`flex-1 bg-black/40 border rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 ${fieldBorder('safety', !safetyCode?.trim() || safetyCode.trim().length < 4)}`}
                />
                <button
                  type="button"
                  onClick={() => setShowSafetyCode(!showSafetyCode)}
                  className="px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-slate-400 hover:text-white transition"
                >
                  {showSafetyCode ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <ErrorHint show={touched.safety && !safetyCode?.trim()} msg="Safety Code không được để trống" />
              <ErrorHint show={touched.safety && safetyCode?.trim() && safetyCode.trim().length < 4} msg="Safety Code cần ít nhất 4 ký tự" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">MAC Address (Tự động tìm lại Camera khi đổi IP)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="VD: AA:BB:CC:DD:EE:FF"
                  value={macAddress}
                  onChange={(e) => { setMacAddress(e.target.value); markDirty(); }}
                  onBlur={(e) => {
                    touch('mac');
                    const formatted = formatMac(e.target.value);
                    if (formatted !== e.target.value) setMacAddress(formatted);
                    checkConflicts();
                  }}
                  className={`flex-1 bg-black/40 border rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 ${fieldBorder('mac', macAddress && macAddress.trim() && !isValidMAC(macAddress))}`}
                />
                {macAddress && (
                  <button
                    type="button"
                    onClick={async () => {
                      const raw = macAddress.replace(/[\s:\-\.]/g, '').toUpperCase();
                      if (raw.length !== 12) {
                        setDiscoverResult('❌ MAC không hợp lệ (cần 12 ký tự hex).');
                        return;
                      }
                      setDiscovering(true);
                      setDiscoverResult('');
                      try {
                        const formattedMac = raw.match(/.{2}/g).join(':');
                        const res = await axios.get(`${API_BASE}/api/discover-mac?mac=${encodeURIComponent(formattedMac)}`);
                        if (res.data.status === 'found') {
                          setDiscoverResult(`✅ Tìm thấy IP: ${res.data.ip}`);
                          setIp1(res.data.ip);
                          markDirty();
                        } else {
                          setDiscoverResult('❌ Không tìm thấy camera trên mạng.');
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
                    {discovering ? '⏳ Quét...' : '🔍 Quét IP'}
                  </button>
                )}
              </div>
              <ErrorHint show={touched.mac && macAddress?.trim() && !isValidMAC(macAddress)} msg="MAC không hợp lệ (VD: AA:BB:CC:DD:EE:FF)" />
              {discoverResult && <p className="mt-1 text-xs text-slate-300">{discoverResult}</p>}
              <p className="mt-1 text-xs text-slate-500">Để trống nếu không cần tự động tìm lại IP khi mạng thay đổi.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Chế độ ghi Video</label>
              <select
                value={cameraMode}
                onChange={(e) => { setCameraMode(e.target.value); markDirty(); }}
                className="w-full bg-[#1e293b] border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50 appearance-none"
              >
                <option value="single">SINGLE — Ghi 1 luồng</option>
                <option value="pip">PIP — Ghép 2 camera (hoặc 1 camera 2 mắt)</option>
                <option value="pip_sim">PIP SIM — Ghép thử từ 1 camera</option>
                <option value="dual_file">DUAL FILE — 2 file từ 2 camera</option>
                <option value="dual_file_sim">DUAL SIM — 2 file từ 1 camera</option>
              </select>
              <p className="mt-1 text-xs text-slate-500">{CAMERA_MODE_DESC[cameraMode]}</p>
            </div>
          </div>

          <WarningHints warnings={warnings} />

          {/* SECTION: Hệ thống chung */}
          <div className="rounded-xl border border-white/10 overflow-hidden">
            <button
              onClick={() => setCollapsed(p => ({ ...p, system: !p.system }))}
              className="w-full flex items-center justify-between p-4 bg-white/5 hover:bg-white/[0.07] transition"
            >
              <h3 className="text-sm font-semibold text-emerald-300 uppercase tracking-wider">Hệ thống chung</h3>
              {collapsed.system ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronUp className="w-4 h-4 text-slate-400" />}
            </button>
            {!collapsed.system && (
              <div className="p-4 bg-white/5 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Tự động xoá Video cũ hơn</label>
                  <select
                    value={keepDays}
                    onChange={(e) => { setKeepDays(e.target.value); markDirty(); }}
                    className="w-full bg-[#1e293b] border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none appearance-none"
                  >
                    <option value="3">3 Ngày</option>
                    <option value="7">7 Ngày</option>
                    <option value="15">15 Ngày</option>
                    <option value="30">30 Ngày</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Dịch vụ Lưu Trữ Đám Mây</label>
                  <select
                    value={cloudProvider}
                    onChange={(e) => { setCloudProvider(e.target.value); markDirty(); }}
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
                      <label className="block text-xs font-medium text-slate-400 mb-1">ID Thư Mục Google Drive</label>
                      <input
                        type="text"
                        placeholder="Bỏ trống = Root"
                        value={gDriveFolderId}
                        onChange={(e) => { setGDriveFolderId(e.target.value); markDirty(); }}
                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500/50"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Service Account (credentials.json)</label>
                      <textarea
                        placeholder="Mở file credentials.json bằng Notepad, copy toàn bộ dán vào đây..."
                        value={gDriveCreds}
                        onChange={(e) => { setGDriveCreds(e.target.value); markDirty(); }}
                        onBlur={() => {
                          if (gDriveCreds.trim()) {
                            try { JSON.parse(gDriveCreds); } catch { /* validation shows on save */ }
                          }
                        }}
                        rows={4}
                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-xs font-mono focus:outline-none focus:border-blue-500/50"
                      />
                      <ErrorHint show={gDriveCreds.trim() && (() => { try { JSON.parse(gDriveCreds); return false; } catch { return true; } })()} msg="credentials.json không hợp lệ (cần JSON)" />
                    </div>
                  </div>
                )}

                {cloudProvider === 'S3' && (
                  <div className="space-y-3 pt-2 border-t border-white/5">
                    <input type="text" placeholder="Endpoint URL (VD: https://xxx.r2.cloudflarestorage.com)" value={s3Endpoint} onChange={(e) => { setS3Endpoint(e.target.value); markDirty(); }} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500/50" />
                    <ErrorHint show={s3Endpoint.trim() && !/^https?:\/\//.test(s3Endpoint.trim())} msg="Endpoint phải bắt đầu bằng http:// hoặc https://" />
                    <input type="text" placeholder="Access Key" value={s3Access} onChange={(e) => { setS3Access(e.target.value); markDirty(); }} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500/50" />
                    <input type="password" placeholder="Secret Key" value={s3Secret} onChange={(e) => { setS3Secret(e.target.value); markDirty(); }} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500/50" />
                    <input type="text" placeholder="Bucket Name" value={s3Bucket} onChange={(e) => { setS3Bucket(e.target.value); markDirty(); }} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500/50" />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* SECTION: Telegram */}
          <div className="rounded-xl border border-white/10 overflow-hidden">
            <button
              onClick={() => setCollapsed(p => ({ ...p, telegram: !p.telegram }))}
              className="w-full flex items-center justify-between p-4 bg-white/5 hover:bg-white/[0.07] transition"
            >
              <h3 className="text-sm font-semibold text-blue-300 uppercase tracking-wider">Thông Báo Telegram</h3>
              {collapsed.telegram ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronUp className="w-4 h-4 text-slate-400" />}
            </button>
            {!collapsed.telegram && (
              <div className="p-4 bg-white/5 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Bot Token</label>
                  <input
                    type="text"
                    placeholder="VD: 123456789:ABCdefGHIjklmNOPqrstuv"
                    value={tgBotToken}
                    onChange={(e) => { setTgBotToken(e.target.value); markDirty(); }}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Chat ID</label>
                  <input
                    type="text"
                    placeholder="VD: -4029419241"
                    value={tgChatId}
                    onChange={(e) => { setTgChatId(e.target.value); markDirty(); }}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-blue-500/50"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3 p-6 pt-3">
          {onCancel && (
            <button
              onClick={handleCancel}
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
