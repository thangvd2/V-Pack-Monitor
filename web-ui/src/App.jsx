/**
 * V-Pack Monitor - CamDongHang v1.10.0
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, MonitorPlay, Video, Calendar, Box, PackageCheck, Settings, Trash2, HardDrive, Plus, Monitor, ShieldCheck, BarChart3, CloudUpload, LogOut, User, Users, LayoutGrid, Maximize2 } from 'lucide-react';
import SetupModal from './SetupModal';
import VideoPlayerModal from './VideoPlayerModal';
import UserManagementModal from './UserManagementModal';
import Dashboard from './Dashboard';

const API_BASE = window.location.hostname === 'localhost' && ['3000', '3001', '5173'].includes(window.location.port) 
  ? 'http://localhost:8001' 
  : window.location.origin;

const MTX_HOST = window.location.hostname;

function App() {
  const [stations, setStations] = useState([]);
  const [activeStationId, setActiveStationId] = useState(1);
  const [records, setRecords] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [initialSettings, setInitialSettings] = useState({});
  const [recordingStatus, setRecordingStatus] = useState('idle');
  const [currentWaybill, setCurrentWaybill] = useState('');
  const [storageInfo, setStorageInfo] = useState({ size_str: '0 MB', file_count: 0 });
  const [diskHealth, setDiskHealth] = useState(null);
  
  // Auth State
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [loginError, setLoginError] = useState('');
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [analytics, setAnalytics] = useState({ total_today: 0, station_today: 0 });
  const [reconnectInfo, setReconnectInfo] = useState(null);
  const [previousStationId, setPreviousStationId] = useState(null);
  
  // Grid View State
  const [viewMode, setViewMode] = useState('single'); // 'single' | 'grid'
  const [cameraMode, setCameraMode] = useState('single-cam'); // 'single-cam' | 'dual' | 'pip'
  const [showDashboard, setShowDashboard] = useState(false);
  const [stationStatuses, setStationStatuses] = useState({}); // { [stationId]: { status, waybill } }
  
  // Custom Video Player State
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState({ url: '', waybillCode: '' });
  const [showUserModal, setShowUserModal] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [changePasswordForm, setChangePasswordForm] = useState({ old_password: '', new_password: '', confirm_password: '' });
  const [changePasswordError, setChangePasswordError] = useState('');
  const [changePasswordSuccess, setChangePasswordSuccess] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('vpack_token');
    const savedUser = localStorage.getItem('vpack_user');
    if (token && savedUser) {
      try {
        setCurrentUser(JSON.parse(savedUser));
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch {
        localStorage.removeItem('vpack_token');
        localStorage.removeItem('vpack_user');
      }
    }
    setAuthLoading(false);
  }, []);

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('vpack_token');
          localStorage.removeItem('vpack_user');
          setCurrentUser(null);
          delete axios.defaults.headers.common['Authorization'];
        }
        return Promise.reject(error);
      }
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  useEffect(() => {
    const stationIds = viewMode === 'grid'
      ? stations.map(s => s.id).join(',')
      : String(activeStationId);
    const es = new EventSource(`${API_BASE}/api/events?stations=${stationIds}`);
    
    es.addEventListener('video_status', (evt) => {
      try {
        const data = JSON.parse(evt.data);
        
        if (viewMode === 'grid') {
          const stationStatus = data.status === 'RECORDING' ? 'recording'
            : data.status === 'PROCESSING' ? 'processing' : 'idle';
          const waybill = data.waybill || '';
          setStationStatuses(prev => ({
            ...prev,
            [data.station_id]: { status: stationStatus, waybill }
          }));
          if (data.station_id === activeStationId) {
            setRecordingStatus(stationStatus);
            setCurrentWaybill(waybill);
          }
          if ((data.status === 'READY' || data.status === 'FAILED' || data.status === 'DELETED') && data.station_id === activeStationId) {
            fetchRecords(searchTerm, activeStationId);
          }
        } else {
          if (data.station_id !== activeStationId) return;
          
          if (data.status === 'RECORDING') {
            setRecordingStatus('recording');
            setCurrentWaybill(data.waybill || '');
          } else if (data.status === 'PROCESSING') {
            setRecordingStatus('processing');
          } else if (data.status === 'READY' || data.status === 'FAILED' || data.status === 'DELETED') {
            setRecordingStatus('idle');
            setCurrentWaybill('');
            fetchRecords(searchTerm, activeStationId);
          }
        }
      } catch {}
    });

    es.onerror = () => {};

    return () => es.close();
  }, [activeStationId, viewMode, stations]);

  // Init fetch
  useEffect(() => {
    fetchStations();
    fetchDiskHealth();
    
    // Refresh disk health every 60 seconds
    const intervalId = setInterval(fetchDiskHealth, 60000);
    return () => clearInterval(intervalId);
  }, []);

  const fetchDiskHealth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/system/disk`);
      if (res.data.status === 'success') {
        setDiskHealth(res.data);
      }
    } catch (e) {
      console.error('Disk health error', e);
    }
  };

  const fetchStations = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/stations`);
      setStations(res.data.data);
      if (res.data.data.length > 0 && !activeStationId) {
        setActiveStationId(res.data.data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (activeStationId) {
      fetchStatus(activeStationId);
      fetchAnalytics(activeStationId);
    }
  }, [activeStationId]);

  useEffect(() => {
    if (!activeStationId) return;
    let active = true;
    let intervalId = null;

    const fetchReconnect = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/reconnect-status?station_id=${activeStationId}`);
        if (!active) return;
        const data = res.data.data;
        setReconnectInfo(data);
        if (data === null && intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
      } catch {
        if (!active) return;
        setReconnectInfo(null);
        if (intervalId) { clearInterval(intervalId); intervalId = null; }
      }
    };

    fetchReconnect();
    intervalId = setInterval(fetchReconnect, 10000);
    return () => { active = false; if (intervalId) clearInterval(intervalId); };
  }, [activeStationId]);

  const fetchAnalytics = async (sid) => {
    try {
      const res = await axios.get(`${API_BASE}/api/analytics/today?station_id=${sid}`);
      if (res.data.data) {
         setAnalytics(res.data.data);
      }
    } catch (error) {
      console.log('Analytics not ready');
    }
  };

  // Lấy trạng thái ghi hình ban đầu 
  const fetchStatus = async (sid) => {
    try {
      const res = await axios.get(`${API_BASE}/api/status?station_id=${sid}`);
      setRecordingStatus(res.data.status);
      setCurrentWaybill(res.data.waybill || '');
    } catch (error) {
      console.log('Status not ready', error);
    }
  };

  useEffect(() => {
    if (viewMode !== 'grid' || stations.length === 0) return;
    setStationStatuses(prev => ({
      ...prev,
      [activeStationId]: { status: recordingStatus, waybill: currentWaybill }
    }));
    stations.forEach(st => {
      axios.get(`${API_BASE}/api/status?station_id=${st.id}`).then(res => {
        setStationStatuses(prev => ({
          ...prev,
          [st.id]: { status: res.data.status, waybill: res.data.waybill || '' }
        }));
      }).catch(() => {});
    });
  }, [viewMode, stations]);

  // Fetch records
  useEffect(() => {
    if (activeStationId) {
      fetchRecords(searchTerm, activeStationId);
    }
  }, [searchTerm, activeStationId]);

  const fetchRecords = async (query = '', sid = activeStationId) => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_BASE}/api/records?search=${query}&station_id=${sid}`);
      setRecords(res.data.data);
      setLoading(false);
      fetchStorageInfo();
      fetchAnalytics(sid);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const fetchStorageInfo = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/storage/info`);
      if (res.data.data) {
        setStorageInfo(res.data.data);
      }
    } catch (err) {
      console.error('Storage info error:', err);
    }
  };

  const checkSettings = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/settings`);
      setInitialSettings(response.data.data || {});
    } catch (error) {
      console.log('API not reachable yet', error);
    }
  };

  // --- Hàm gọi API Scan ---
  const sendScanAction = async (finalBarcode) => {
    if (!activeStationId) return;
    try {
      const res = await axios.post(`${API_BASE}/api/scan`, { 
        barcode: finalBarcode,
        station_id: activeStationId
      });
      if (res.data.status === 'recording') {
        if (recordingStatus === 'recording') {
          alert(res.data.message);
        } else {
          setRecordingStatus('recording');
          setCurrentWaybill(finalBarcode);
        }
      } else if (res.data.status === 'stopped' || res.data.status === 'exit') {
        setRecordingStatus('idle');
        setCurrentWaybill('');
        fetchRecords(searchTerm, activeStationId); 
      } else if (res.data.status === 'busy' || res.data.status === 'processing') {
        setRecordingStatus('processing');
        if (res.data.message) alert(res.data.message);
      }
    } catch (err) {
      console.error("Barcode Lỗi", err);
    }
  };

  // --- Quản lý Bảo mật (Role Gateway) ---
  const requestAdminAccess = (action) => {
    if (currentUser?.role === 'ADMIN') {
      executeSecureAction(action);
    } else {
      alert('Yêu cầu quyền Administrator.');
    }
  };

  const executeSecureAction = async (action) => {
    if (action.type === 'setup') {
      if (action.isNew) {
        setPreviousStationId(activeStationId);
        setActiveStationId(0);
      }
      await checkSettings();
      setShowSetupModal(true);
    } else if (action.type === 'delete') {
      doDeleteRecord(action.id, action.waybill);
    } else if (action.type === 'cloud_sync') {
      doCloudSync();
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    try {
      const res = await axios.post(`${API_BASE}/api/auth/login`, loginForm);
      if (res.data.status === 'success') {
        const { access_token, user } = res.data;
        localStorage.setItem('vpack_token', access_token);
        localStorage.setItem('vpack_user', JSON.stringify(user));
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        setCurrentUser(user);
        setLoginForm({ username: '', password: '' });
      } else {
        setLoginError(res.data.message || 'Đăng nhập thất bại.');
      }
    } catch (err) {
      setLoginError('Lỗi kết nối server.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('vpack_token');
    localStorage.removeItem('vpack_user');
    delete axios.defaults.headers.common['Authorization'];
    setCurrentUser(null);
  };
   
  // --- Hàm xoá bản ghi (Đã qua kiểm duyệt bảo mật) ---
  const handleDeleteRecord = (id, waybill_code) => {
    requestAdminAccess({ type: 'delete', id, waybill: waybill_code });
  };

  const doDeleteRecord = async (id, waybill_code) => {
    if (window.confirm(`Bạn có chắc chắn muốn xoá bản ghi "${waybill_code}" không?`)) {
      try {
        await axios.delete(`${API_BASE}/api/records/${id}`);
        fetchRecords(searchTerm, activeStationId);
      } catch (err) {
        alert("Có lỗi xảy ra khi xoá.");
      }
    }
  };

  const doCloudSync = async () => {
    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/api/cloud-sync`);
      if (res.data.status === 'success') {
        alert(res.data.message);
      } else {
        alert("Lỗi Upload: " + res.data.message);
      }
      setLoading(false);
    } catch (e) {
      setLoading(false);
      alert("Đã xảy ra lỗi khi đồng bộ Đám mây.");
    }
  };

  // --- BARCODE SCANNER LISTENER ---
  useEffect(() => {
    let barcodeBuffer = '';
    let timeoutId = null;

    const handleKeyDown = async (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        const finalBarcode = barcodeBuffer.trim();
        barcodeBuffer = ''; 
        
        if (finalBarcode.length > 0) {
           await sendScanAction(finalBarcode);
        }
      } else {
        if (e.key.length === 1) {
          barcodeBuffer += e.key;
        }
        
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          barcodeBuffer = '';
        }, 100); 
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [searchTerm, activeStationId]); 

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };
  
  const activeStation = stations.find(s => s.id === activeStationId) || {};
  const hasCam2 = activeStation?.ip_camera_2 && activeStation.ip_camera_2.trim() !== '';

  useEffect(() => {
    if (!hasCam2) setCameraMode('single-cam');
  }, [activeStationId]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-blue-500/20 flex items-center justify-center border border-blue-400/30 mx-auto mb-4">
              <PackageCheck className="text-blue-400 w-9 h-9" />
            </div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
              V-Pack Monitor
            </h1>
            <p className="text-slate-400 mt-2">Đăng nhập để tiếp tục</p>
          </div>
          <form onSubmit={handleLogin} className="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-md shadow-2xl">
            {loginError && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-300 text-sm">
                {loginError}
              </div>
            )}
            <div className="mb-4">
              <label className="block text-sm text-slate-400 mb-2">Tên đăng nhập</label>
              <input
                type="text"
                value={loginForm.username}
                onChange={(e) => setLoginForm(f => ({ ...f, username: e.target.value }))}
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                placeholder="Nhập tên đăng nhập"
                autoFocus
              />
            </div>
            <div className="mb-6">
              <label className="block text-sm text-slate-400 mb-2">Mật khẩu</label>
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm(f => ({ ...f, password: e.target.value }))}
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                placeholder="Nhập mật khẩu"
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 rounded-xl font-semibold text-white shadow-lg transition-all"
            >
              Đăng Nhập
            </button>
          </form>
          <p className="text-center text-xs text-slate-500 mt-6">
            V-Pack Monitor v1.10.0 • VDT
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 md:p-10 font-sans">
      {showSetupModal && (
        <SetupModal 
          isOpen={showSetupModal}
          initialSettings={initialSettings} 
          currentStation={activeStation}
          isNewStation={!activeStation.id}
          onSaved={() => {
            setShowSetupModal(false);
            window.location.reload(); 
          }} 
          onCancel={() => {
            setShowSetupModal(false);
            if (activeStationId === 0 && previousStationId) {
              setActiveStationId(previousStationId);
            } else if (activeStationId === 0 && stations.length > 0) {
              setActiveStationId(stations[0].id);
            }
          }}
        />
      )}
      
      <VideoPlayerModal
        isOpen={videoModalOpen}
        videoUrl={selectedVideo.url}
        waybillCode={selectedVideo.waybillCode}
        onClose={() => setVideoModalOpen(false)}
      />

      <UserManagementModal
        isOpen={showUserModal}
        onClose={() => setShowUserModal(false)}
        currentUser={currentUser}
      />

      {showChangePassword && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={() => setShowChangePassword(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-3xl p-6 w-full max-w-sm shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-400" />
                Đổi Mật Khẩu
              </h3>
              <button onClick={() => { setShowChangePassword(false); setChangePasswordError(''); setChangePasswordSuccess(''); }} className="p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            {changePasswordSuccess ? (
              <div className="p-4 bg-emerald-500/20 border border-emerald-500/30 rounded-xl text-emerald-200 text-sm text-center">
                {changePasswordSuccess}
              </div>
            ) : (
              <div className="space-y-3">
                {changePasswordError && (
                  <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-200 text-sm">
                    {changePasswordError}
                  </div>
                )}
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Mật khẩu hiện tại</label>
                  <input
                    type="password"
                    value={changePasswordForm.old_password}
                    onChange={e => setChangePasswordForm(f => ({ ...f, old_password: e.target.value }))}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Mật khẩu mới</label>
                  <input
                    type="password"
                    value={changePasswordForm.new_password}
                    onChange={e => setChangePasswordForm(f => ({ ...f, new_password: e.target.value }))}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Xác nhận mật khẩu mới</label>
                  <input
                    type="password"
                    value={changePasswordForm.confirm_password}
                    onChange={e => setChangePasswordForm(f => ({ ...f, confirm_password: e.target.value }))}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        setChangePasswordError('');
                        if (changePasswordForm.new_password.length < 6) { setChangePasswordError('Mật khẩu mới phải có ít nhất 6 ký tự.'); return; }
                        if (changePasswordForm.new_password !== changePasswordForm.confirm_password) { setChangePasswordError('Mật khẩu xác nhận không khớp.'); return; }
                        axios.put(`${API_BASE}/api/auth/change-password`, { old_password: changePasswordForm.old_password, new_password: changePasswordForm.new_password })
                          .then(() => { setChangePasswordSuccess('Đổi mật khẩu thành công!'); setChangePasswordForm({ old_password: '', new_password: '', confirm_password: '' }); })
                          .catch(err => { setChangePasswordError(err.response?.data?.detail || 'Mật khẩu cũ không đúng.'); });
                      }
                    }}
                  />
                </div>
                <button
                  onClick={() => {
                    setChangePasswordError('');
                    if (changePasswordForm.new_password.length < 6) { setChangePasswordError('Mật khẩu mới phải có ít nhất 6 ký tự.'); return; }
                    if (changePasswordForm.new_password !== changePasswordForm.confirm_password) { setChangePasswordError('Mật khẩu xác nhận không khớp.'); return; }
                    axios.put(`${API_BASE}/api/auth/change-password`, { old_password: changePasswordForm.old_password, new_password: changePasswordForm.new_password })
                      .then(() => { setChangePasswordSuccess('Đổi mật khẩu thành công!'); setChangePasswordForm({ old_password: '', new_password: '', confirm_password: '' }); })
                      .catch(err => { setChangePasswordError(err.response?.data?.detail || 'Mật khẩu cũ không đúng.'); });
                  }}
                  className="w-full py-2.5 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 rounded-xl font-semibold text-white shadow-lg transition-all text-sm"
                >
                  Xác Nhận Đổi Mật Khẩu
                </button>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Header */}
      <header className="flex flex-col mb-8">
        <div className="flex flex-col md:flex-row items-center justify-between pb-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center border border-blue-400/30">
              <PackageCheck className="text-blue-400 w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                V-Pack Monitor
              </h1>
              <p className="text-sm text-slate-400">Hệ thống Camera Đóng hàng E-Commerce</p>
            </div>
          </div>
          
          <div className="mt-6 md:mt-0 flex items-center gap-4 w-full md:w-auto">
          {/* Station Selector Dropdown */}
          {!(viewMode === 'grid' && stations.length >= 2) && (
          <div className="relative group flex items-center border border-white/10 rounded-2xl bg-white/5 py-2 px-3 shadow-lg">
             <Monitor className="w-5 h-5 text-indigo-400 mr-2" />
             <select 
               value={activeStationId} 
               onChange={(e) => setActiveStationId(Number(e.target.value))}
               className="bg-transparent text-slate-200 focus:outline-none appearance-none font-semibold cursor-pointer pr-4"
             >
               {stations.map(st => (
                 <option key={st.id} value={st.id} className="bg-slate-800">
                   Trạm: {st.name}
                 </option>
               ))}
               {stations.length === 0 && <option value={0} disabled>Chưa có trạm nào</option>}
             </select>
               {currentUser?.role === 'ADMIN' && (
                 <button title="Thêm Trạm Mới" onClick={() => requestAdminAccess({ type: 'setup', isNew: true })} className="ml-2 p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition">
                    <Plus className="w-4 h-4" />
                 </button>
               )}
          </div>
          )}

          {/* View Mode Toggle */}
          {stations.length >= 2 && (
            <button
              onClick={() => setViewMode(prev => prev === 'single' ? 'grid' : 'single')}
              className="p-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-blue-500/30 rounded-2xl transition-all shadow-lg text-slate-400 hover:text-blue-400"
              title={viewMode === 'single' ? 'Xem tổng quan tất cả trạm' : 'Xem trạm đơn lẻ'}
            >
              {viewMode === 'single' ? <LayoutGrid className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>
          )}

          <button
            onClick={() => setShowDashboard(prev => !prev)}
            className={`p-3 border rounded-2xl transition-all shadow-lg ${showDashboard ? 'bg-blue-500/20 border-blue-500/50 text-blue-400' : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-blue-500/30 text-slate-400 hover:text-blue-400'}`}
            title={showDashboard ? 'Quay lại giao diện chính' : 'Bảng điều khiển'}
          >
            <BarChart3 className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-2xl px-4 py-3 hidden xl:flex">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            <div className="flex flex-col">
              <span className="text-xs text-slate-400 font-medium">Hôm nay</span>
              <div className="flex gap-2 items-center text-sm">
                <span className="text-blue-300 font-bold" title="Trạm hiện tại">{analytics.station_today} đơn</span>
                <span className="text-slate-500">/</span>
                <span className="text-slate-200 font-bold" title="Tổng TOÀN KHO">{analytics.total_today} đơn</span>
              </div>
            </div>
          </div>

          <div className="relative w-full md:w-64 group hidden lg:block">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
            </div>
            <input
              type="text"
              className="block w-full pl-11 pr-4 py-3 bg-white/5 border border-white/10 rounded-2xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 backdrop-blur-md transition-all shadow-lg"
              placeholder="Tìm mã vận đơn..."
              value={searchTerm}
              onChange={handleSearch}
            />
          </div>
          
          <div className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-2xl px-4 py-3 hidden md:flex">
            <HardDrive className="w-5 h-5 text-emerald-400" />
            <div className="flex flex-col">
              <span className="text-xs text-slate-400 font-medium">Đã Sử Dụng</span>
              <span className="text-sm text-slate-200 font-bold">{storageInfo.size_str} ({storageInfo.file_count} file)</span>
            </div>
          </div>
          
          {currentUser?.role === 'ADMIN' && (
            <button 
              onClick={() => requestAdminAccess({ type: 'cloud_sync' })}
              className="p-3 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 rounded-2xl transition-all shadow-lg hidden md:flex text-indigo-400"
              title="Đẩy Video lên Cloud"
            >
              <CloudUpload className="w-6 h-6" />
            </button>
          )}
          
          {currentUser?.role === 'ADMIN' && (
            <button 
              onClick={() => requestAdminAccess({ type: 'setup' })}
              className="p-3 bg-white/5 hover:bg-blue-500/20 border border-white/10 hover:border-blue-500/50 rounded-2xl transition-all shadow-lg hidden md:flex text-slate-400 hover:text-blue-400"
              title="Cài đặt Camera & Hệ thống cho Trạm này"
            >
              <Settings className="w-6 h-6" />
            </button>
          )}

          {currentUser?.role === 'ADMIN' && (
            <button 
              onClick={() => setShowUserModal(true)}
              className="p-3 bg-white/5 hover:bg-emerald-500/20 border border-white/10 hover:border-emerald-500/50 rounded-2xl transition-all shadow-lg hidden md:flex text-slate-400 hover:text-emerald-400"
              title="Quản lý người dùng"
            >
              <Users className="w-6 h-6" />
            </button>
          )}

          <div className="relative">
            <button
              onClick={() => setShowUserDropdown(!showUserDropdown)}
              className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-2xl px-4 py-2.5 hover:bg-white/10 transition-all"
            >
              <User className="w-5 h-5 text-blue-400" />
              <div className="flex flex-col items-start">
                <span className="text-sm text-slate-200 font-medium">{currentUser.full_name || currentUser.username}</span>
                <span className="text-[10px] text-slate-400 uppercase">{currentUser.role}</span>
              </div>
              <svg className={`w-3.5 h-3.5 text-slate-400 transition-transform ${showUserDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showUserDropdown && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowUserDropdown(false)} />
                <div className="absolute right-0 top-full mt-2 w-56 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-20 py-1 overflow-hidden">
                  <button
                    onClick={() => { setShowUserDropdown(false); setShowChangePassword(true); }}
                    className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/10 hover:text-white transition-colors text-left"
                  >
                    <Settings className="w-4 h-4 text-slate-400" />
                    Đổi mật khẩu
                  </button>
                  <button
                    onClick={() => { setShowUserDropdown(false); handleLogout(); }}
                    className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-300 hover:bg-red-500/10 hover:text-red-200 transition-colors text-left border-t border-white/5"
                  >
                    <LogOut className="w-4 h-4" />
                    Đăng xuất
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
        </div>

        {/* Cảnh Báo Bình Xăng Ổ Cứng */}
        {diskHealth && (
          <div className="mt-6 bg-white/5 border border-white/10 rounded-2xl p-4 w-full">
            <div className="flex justify-between items-center mb-2">
              <div className="flex items-center gap-2">
                <HardDrive className={`w-5 h-5 ${diskHealth.percentage > 90 ? 'text-red-500 animate-pulse' : 'text-emerald-400'}`} />
                <span className="font-semibold text-slate-200">
                  {diskHealth.percentage > 90 ? 'Cảnh Báo: Ổ Cứng Sắp Đầy!' : 'Dung lượng máy tính'}
                </span>
              </div>
              <span className="text-sm text-slate-400">
                {(diskHealth.used / 1024 / 1024 / 1024).toFixed(1)} GB / {(diskHealth.total / 1024 / 1024 / 1024).toFixed(1)} GB
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-3">
              <div 
                className={`h-3 rounded-full ${diskHealth.percentage > 90 ? 'bg-red-500 animate-pulse box-shadow-red' : 'bg-gradient-to-r from-emerald-500 to-blue-500'}`}
                style={{ width: `${Math.min(diskHealth.percentage, 100)}%` }}
              ></div>
            </div>
            <div className="flex justify-end mt-1">
              <span className="text-xs text-slate-500">Đã dùng: {diskHealth.percentage}%</span>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      {showDashboard ? (
        <Dashboard
          stations={stations}
          activeStationId={activeStationId}
          storageInfo={storageInfo}
          currentUser={currentUser}
          analytics={analytics}
        />
      ) : (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Live Camera / Grid */}
        <div className="lg:col-span-2 flex flex-col gap-4">

          {viewMode === 'grid' ? (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <LayoutGrid className="w-5 h-5 text-blue-400" />
                  Tổng Quan Toàn Kho
                </h2>
                <span className="flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
              </div>

              {stations.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-16 bg-white/5 border border-white/10 rounded-3xl backdrop-blur-sm">
                  <Monitor className="w-12 h-12 text-slate-500 mb-3" />
                  <p className="text-slate-400">Chưa có trạm nào</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))' }}>
                  {stations.map(station => {
                    const st = stationStatuses[station.id] || { status: 'idle', waybill: '' };
                    return (
                      <div
                        key={station.id}
                        onClick={() => { setActiveStationId(station.id); setViewMode('single'); }}
                        className="relative group rounded-3xl overflow-hidden bg-zinc-900 border border-white/10 hover:border-blue-400/30 shadow-2xl shadow-blue-900/20 aspect-video flex items-center justify-center cursor-pointer transition-all duration-300 hover:scale-[1.02]"
                      >
                        <iframe
                          key={`grid-${station.id}`}
                          src={`http://${MTX_HOST}:8889/station_${station.id}?controls=false&muted=true&autoplay=true`}
                          scrolling="no"
                          className="w-full h-full object-cover"
                          style={{ border: 'none', background: '#000' }}
                          allow="autoplay"
                        />
                        {station.id === activeStationId && reconnectInfo && reconnectInfo.status === 'searching' && (
                          <div className="absolute top-2 left-1/2 -translate-x-1/2 z-10 bg-amber-500/90 text-white text-xs font-semibold px-3 py-1 rounded-full animate-pulse">
                            🔄 Tìm lại Camera...
                          </div>
                        )}
                        {station.id === activeStationId && reconnectInfo && reconnectInfo.status === 'found' && (
                          <div className="absolute top-2 left-1/2 -translate-x-1/2 z-10 bg-emerald-500/90 text-white text-xs font-semibold px-3 py-1 rounded-full">
                            ✅ IP mới: {reconnectInfo.new_ip}
                          </div>
                        )}
                        <div className="absolute top-3 left-3 right-3 flex items-start gap-2 pointer-events-none">
                          <div className="px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-xs font-mono text-white/90">
                            {station.name}
                          </div>
                          {st.status === 'recording' && (
                            <div className="px-3 py-1.5 rounded-full bg-red-600/90 backdrop-blur-md border border-red-400 text-xs font-bold text-white flex items-center gap-2 animate-pulse">
                              <div className="w-2 h-2 rounded-full bg-white"></div>
                              ĐANG GHI: {st.waybill}
                            </div>
                          )}
                          {st.status === 'processing' && (
                            <div className="px-3 py-1.5 rounded-full bg-amber-500/90 backdrop-blur-md border border-amber-300 text-xs font-bold text-white flex items-center gap-2 animate-pulse">
                              <div className="w-2 h-2 rounded-full bg-white"></div>
                              ĐANG XỬ LÝ
                            </div>
                          )}
                          {st.status === 'idle' && (
                            <div className="px-3 py-1.5 rounded-full bg-emerald-600/90 backdrop-blur-md border border-emerald-400 text-xs font-bold text-white flex items-center gap-2">
                              <div className="w-2 h-2 rounded-full bg-white"></div>
                              SẴN SÀNG
                            </div>
                          )}
                        </div>
                        {station.ip_camera_2 && station.ip_camera_2.trim() !== '' && (
                          <div className="absolute top-3 right-3 px-2 py-0.5 bg-blue-500/30 border border-blue-400/40 rounded text-[10px] text-blue-200 font-bold pointer-events-none z-10">
                            2 CAM
                          </div>
                        )}
                        <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 transition-all duration-300 pointer-events-none" />
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <MonitorPlay className="w-5 h-5 text-red-400" />
                    Chế Độ Quan Sát Live
                  </h2>
                  {stations.length >= 2 && (
                    <button onClick={() => setViewMode('grid')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-sm text-slate-400 hover:text-white transition">
                      <LayoutGrid className="w-4 h-4" />
                      Tổng quan
                    </button>
                  )}
                  {hasCam2 && (
                    <div className="flex items-center gap-1 bg-white/5 border border-white/10 rounded-xl p-0.5">
                      <button
                        onClick={() => setCameraMode('single-cam')}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${cameraMode === 'single-cam' ? 'bg-blue-500/20 text-blue-300' : 'text-slate-400 hover:text-white'}`}
                      >1 Cam</button>
                      <button
                        onClick={() => setCameraMode('dual')}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${cameraMode === 'dual' ? 'bg-blue-500/20 text-blue-300' : 'text-slate-400 hover:text-white'}`}
                      >Dual</button>
                      <button
                        onClick={() => setCameraMode('pip')}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${cameraMode === 'pip' ? 'bg-blue-500/20 text-blue-300' : 'text-slate-400 hover:text-white'}`}
                      >PIP</button>
                    </div>
                  )}
                </div>
                <span className="flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
              </div>
              
              <div className="relative group rounded-3xl overflow-hidden bg-zinc-900 border border-white/10 shadow-2xl shadow-blue-900/20 aspect-video flex items-center justify-center">
                {activeStationId ? (
                    <>
                    {reconnectInfo && reconnectInfo.status === 'searching' && (
                      <div className="absolute top-2 left-1/2 -translate-x-1/2 z-10 bg-amber-500/90 text-white text-xs font-semibold px-3 py-1 rounded-full animate-pulse">
                        🔄 Đang tìm lại Camera...
                      </div>
                    )}
                    {reconnectInfo && reconnectInfo.status === 'found' && (
                      <div className="absolute top-2 left-1/2 -translate-x-1/2 z-10 bg-emerald-500/90 text-white text-xs font-semibold px-3 py-1 rounded-full">
                        ✅ Đã tìm thấy IP mới: {reconnectInfo.new_ip}
                      </div>
                    )}

                    {hasCam2 && cameraMode === 'dual' ? (
                      <div className="flex gap-1 w-full h-full">
                        <div className="flex-1 relative">
                          <iframe
                            key={`live-${activeStationId}`}
                            src={`http://${MTX_HOST}:8889/station_${activeStationId}?controls=false&muted=true&autoplay=true`}
                            scrolling="no"
                            className="w-full h-full object-cover"
                            style={{ border: 'none', background: '#000' }}
                            allow="autoplay"
                          />
                          <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-xs text-white/80 pointer-events-none">Camera 1</div>
                        </div>
                        <div className="flex-1 relative">
                          <iframe
                            key={`live-cam2-${activeStationId}`}
                            src={`http://${MTX_HOST}:8889/station_${activeStationId}_cam2?controls=false&muted=true&autoplay=true`}
                            scrolling="no"
                            className="w-full h-full object-cover"
                            style={{ border: 'none', background: '#000' }}
                            allow="autoplay"
                          />
                          <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-xs text-white/80 pointer-events-none">Camera 2</div>
                        </div>
                      </div>
                    ) : hasCam2 && cameraMode === 'pip' ? (
                      <div className="w-full h-full relative">
                        <iframe
                          key={`live-${activeStationId}`}
                          src={`http://${MTX_HOST}:8889/station_${activeStationId}?controls=false&muted=true&autoplay=true`}
                          scrolling="no"
                          className="w-full h-full object-cover"
                          style={{ border: 'none', background: '#000' }}
                          allow="autoplay"
                        />
                        <div className="absolute bottom-3 right-3 w-1/4 h-1/4 rounded-xl overflow-hidden border-2 border-white/20 shadow-2xl z-20">
                          <iframe
                            key={`pip-cam2-${activeStationId}`}
                            src={`http://${MTX_HOST}:8889/station_${activeStationId}_cam2?controls=false&muted=true&autoplay=true`}
                            scrolling="no"
                            className="w-full h-full object-cover"
                            style={{ border: 'none', background: '#000' }}
                            allow="autoplay"
                          />
                          <div className="absolute bottom-1 left-1 px-1.5 py-0.5 bg-black/60 rounded text-[10px] text-white/80 pointer-events-none">Camera 2</div>
                        </div>
                      </div>
                    ) : (
                      <iframe
                        key={`live-${activeStationId}`}
                        src={`http://${MTX_HOST}:8889/station_${activeStationId}?controls=false&muted=true&autoplay=true`}
                        scrolling="no"
                        className="w-full h-full object-cover"
                        style={{ border: 'none', background: '#000' }}
                        allow="autoplay"
                      />
                    )}
                    <div className="absolute top-4 left-4 right-4 flex justify-between items-start pointer-events-none">
                      <div className="flex gap-2">
                        <div className="px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-xs font-mono text-white/90">
                           {activeStation?.name || "Đang tải"}
                        </div>
                        {recordingStatus === 'recording' && (
                          <div className="px-3 py-1.5 rounded-full bg-red-600/90 backdrop-blur-md border border-red-400 text-xs font-bold text-white flex items-center gap-2 animate-pulse transition-all">
                            <div className="w-2 h-2 rounded-full bg-white"></div>
                            ĐANG GHI ĐƠN: {currentWaybill}
                          </div>
                        )}
                        {recordingStatus === 'processing' && (
                          <div className="px-3 py-1.5 rounded-full bg-amber-500/90 backdrop-blur-md border border-amber-300 text-xs font-bold text-white flex items-center gap-2 animate-pulse transition-all">
                            <div className="w-2 h-2 rounded-full bg-white"></div>
                            ĐANG XỬ LÝ VIDEO: {currentWaybill}
                          </div>
                        )}
                        {recordingStatus === 'idle' && (
                          <div className="px-3 py-1.5 rounded-full bg-emerald-600/90 backdrop-blur-md border border-emerald-400 text-xs font-bold text-white flex items-center gap-2 transition-all">
                            <div className="w-2 h-2 rounded-full bg-white"></div>
                            SAN SANG CHO DON HANG TIEP THEO
                          </div>
                        )}
                      </div>
                    </div>
                    </>
                ) : (
                    <div className="text-slate-500 flex flex-col items-center">
                        <Settings className="w-12 h-12 mb-2 opacity-50" />
                        <p>Vui lòng tạo Trạm Đóng Hàng đầu tiên</p>
                        {currentUser?.role === 'ADMIN' && (
                          <button onClick={() => requestAdminAccess({ type: 'setup', isNew: true })} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg">Cài đặt ngay</button>
                        )}
                    </div>
                )}
              </div>
              
              <div className="p-5 rounded-2xl bg-white/5 border border-purple-500/30 backdrop-blur-lg mt-2 relative overflow-hidden group">
                <div className="absolute top-0 right-0 bg-purple-500/20 text-purple-300 text-[10px] px-3 py-1 rounded-bl-xl font-mono border-l border-b border-purple-500/20">
                  DEV MODE
                </div>
                <h3 className="font-medium text-slate-200 mb-4 flex items-center gap-2">
                  <Box className="w-4 h-4 text-purple-400" />
                  Công Cụ Giả Lập Máy Quét (Manual Simulator)
                </h3>
                
                <div className="flex flex-col sm:flex-row gap-3">
                   <input
                     type="text"
                     placeholder="Nhập mã vận đơn (VD: SPX12345)"
                     className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500/50 font-mono text-sm"
                     id="simulated-barcode-input"
                     onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.target.value.trim()) {
                            sendScanAction(e.target.value.trim());
                            e.target.value = '';
                        }
                     }}
                   />
                   <button 
                     onClick={() => {
                       const inputUI = document.getElementById('simulated-barcode-input');
                       if(inputUI.value.trim()) {
                         sendScanAction(inputUI.value.trim());
                         inputUI.value = '';
                       }
                     }}
                     className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 rounded-xl font-medium text-white shadow-lg transition-colors border border-purple-400/20"
                   >
                     Bắt Đầu Ghi
                   </button>
                   <button 
                     onClick={() => sendScanAction('STOP')}
                     className="px-6 py-2.5 bg-slate-800 hover:bg-rose-600 rounded-xl font-medium text-white shadow-lg transition-colors border border-white/10"
                   >
                     STOP (Chốt Đơn)
                   </button>
                </div>
                <p className="text-xs text-slate-500 mt-4 leading-relaxed italic">
                  * Sử dụng thanh công cụ này nếu bạn không có súng bắn mã vạch. Hệ thống sẽ kết nối với Camera ở Trạm đang chọn.
                </p>
              </div>
            </>
          )}

        </div>

        {/* Right Column: History Records List */}
        <div className="flex flex-col gap-4 h-[calc(100vh-200px)]">
          <div className="flex items-center justify-between pointer-events-none">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Calendar className="w-5 h-5 text-emerald-400" />
              Lịch sử ghi hình
            </h2>
            <div className="px-3 py-1 bg-white/10 rounded-full text-xs font-semibold">
              {records.length} videos
            </div>
          </div>

          <div className="flex-1 overflow-y-auto pr-2 space-y-4">
            {loading ? (
              <div className="flex items-center justify-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : records.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-10 text-center bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm">
                <Box className="w-12 h-12 text-slate-500 mb-3" />
                <p className="text-slate-400">Chưa có mã vận đơn nào được ghi lại tại Trạm này.</p>
              </div>
            ) : (
              records.map((record) => (
                <div 
                  key={record.id} 
                  className="group p-5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-blue-400/30 backdrop-blur-md transition-all duration-300 shadow-lg cursor-pointer"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-3">
                       <h3 className="text-lg font-bold text-white group-hover:text-blue-300 transition-colors">
                         {record.waybill_code}
                       </h3>
                        <span className="px-2 py-1 bg-white/10 rounded uppercase text-[10px] font-bold tracking-wider text-slate-300">
                          {record.record_mode}
                        </span>
                        {record.status && record.status !== 'READY' && (
                          <span className={`px-2 py-1 rounded uppercase text-[10px] font-bold tracking-wider ${
                            record.status === 'RECORDING' ? 'bg-red-500/30 text-red-300 animate-pulse' :
                            record.status === 'PROCESSING' ? 'bg-amber-500/30 text-amber-300 animate-pulse' :
                            record.status === 'FAILED' ? 'bg-red-500/30 text-red-300' :
                            'bg-white/10 text-slate-300'
                          }`}>
                            {record.status}
                          </span>
                        )}
                       <span className="px-2 py-1 bg-blue-500/20 border border-blue-500/30 text-blue-300 rounded text-[10px] font-bold">
                         Trạm: {record.station_name || 'Mặc định'}
                       </span>
                    </div>
                    {currentUser?.role === 'ADMIN' && (
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleDeleteRecord(record.id, record.waybill_code); }}
                        className="p-2 -mr-2 -mt-2 text-slate-500 hover:text-rose-400 hover:bg-rose-400/10 rounded-lg transition-colors"
                        title="Xoá bản ghi lưu trữ dọn ổ đĩa"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                  
                  <p className="text-xs text-slate-400 mb-4 font-mono">
                    {new Date(record.recorded_at).toLocaleString('vi-VN')}
                  </p>
                  
                  {/* Danh sách các file video lưu trữ */}
                  <div className="space-y-2">
                    {record.video_paths.map((path, idx) => {
                      const fileName = path.split('/').pop() || path.split('\\').pop();
                      const videoUrl = `${API_BASE}/${path.replace(/\\/g, '/')}`;
                      return (
                        <div 
                          key={idx}
                          role="button"
                          onClick={() => {
                            if (record.status && record.status !== 'READY' && record.status !== 'FAILED') return;
                            setSelectedVideo({ url: videoUrl, waybillCode: record.waybill_code });
                            setVideoModalOpen(true);
                          }}
                          className={`flex items-center gap-2 p-2 rounded-lg bg-black/20 border border-white/5 text-sm ${
                            record.status === 'RECORDING' || record.status === 'PROCESSING' 
                              ? 'opacity-50 cursor-wait' 
                              : 'hover:bg-black/40 cursor-pointer transition-colors'
                          }`}
                        >
                          <Video className="w-4 h-4 text-emerald-400" />
                          <span className="truncate flex-1 text-slate-300">{fileName}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
      </div>
      )}
    </div>
  );
}

export default App;
