/**
 * V-Pack Monitor - CamDongHang
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import axios from 'axios';
import {
  Search,
  MonitorPlay,
  Video,
  Calendar,
  Box,
  PackageCheck,
  Settings,
  Trash2,
  HardDrive,
  Plus,
  Monitor,
  ShieldCheck,
  BarChart3,
  CloudUpload,
  LogOut,
  User,
  Users,
  LayoutGrid,
  Maximize2,
  Activity,
  RefreshCw,
} from 'lucide-react';
import SetupModal from './SetupModal';
import VideoPlayerModal from './VideoPlayerModal';
import UserManagementModal from './UserManagementModal';
import Dashboard from './Dashboard';
import AdminDashboard from './AdminDashboard';
import SystemHealth from './SystemHealth';
import MtxFallback from './MtxFallback';
import API_BASE from './config';

import { useToast, useConfirmDialog, useAuth, useRecords, useSSE, useBarcodeScanner } from './hooks';

const MTX_HOST = window.location.hostname;

// Named constants
const STATION_POLL_INTERVAL = 10000;
const BARCODE_TIMEOUT = 100;
const HEARTBEAT_INTERVAL = 30000;
const SEARCH_DEBOUNCE = 300;
const TOAST_DURATIONS = { info: 2000, error: 3000, warning: 5000 };

function StationSelectionScreen({ stations, stationStatusList, fetchStationStatus, acquireStation, currentUser }) {
  const [loading, setLoading] = useState(true);
  const [selecting, setSelecting] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await fetchStationStatus();
      setLoading(false);
    };
    load();
    const interval = setInterval(fetchStationStatus, STATION_POLL_INTERVAL);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: polling interval — adding fetchStationStatus would reset interval every render
  }, []);

  const getStatusForStation = (stationId) => {
    return stationStatusList.find((s) => s.station_id === stationId);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <div className="text-center mb-10">
        <div className="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center border border-blue-400/20 mx-auto mb-4">
          <Monitor className="text-blue-400 w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Chọn Trạm Làm Việc</h2>
        <p className="text-slate-400 text-sm">
          Xin chào <span className="text-blue-300 font-medium">{currentUser.full_name || currentUser.username}</span>,
          vui lòng chọn trạm để bắt đầu
        </p>
      </div>

      {loading ? (
        <div className="flex items-center gap-3 text-slate-400">
          <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
          <span>Đang tải trạng thái trạm...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 w-full max-w-5xl">
          {stations.length === 0 ? (
            <div className="col-span-full text-center py-16">
              <Monitor className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p className="text-slate-400">Chưa có trạm nào được cấu hình</p>
              <p className="text-slate-500 text-sm mt-1">Vui lòng liên hệ Administrator</p>
            </div>
          ) : (
            stations.map((station) => {
              const status = getStatusForStation(station.id);
              const isOccupied = status?.occupied && status?.occupied_by !== currentUser.username;
              const isHeldBySelf = status?.occupied && status?.occupied_by === currentUser.username;

              return (
                <button
                  key={station.id}
                  disabled={isOccupied || selecting !== null}
                  onClick={() => {
                    if (isOccupied) return;
                    setSelecting(station.id);
                    acquireStation(station.id);
                  }}
                  className={`
                    relative group p-6 rounded-3xl border backdrop-blur-sm shadow-xl transition-all duration-300 text-left
                    ${
                      isOccupied
                        ? 'bg-zinc-900/60 border-red-500/20 opacity-60 cursor-not-allowed'
                        : isHeldBySelf
                          ? 'bg-amber-500/5 border-amber-500/30 cursor-pointer hover:scale-[1.02] hover:border-amber-400/50'
                          : selecting === station.id
                            ? 'bg-blue-500/10 border-blue-500/40 scale-[0.98]'
                            : 'bg-zinc-900/80 border-white/10 cursor-pointer hover:scale-[1.02] hover:border-blue-400/40 hover:bg-blue-500/5'
                    }
                  `}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
                      <Monitor className="w-5 h-5 text-slate-300" />
                    </div>
                    <span
                      className={`
                      flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full
                      ${
                        isOccupied
                          ? 'bg-red-500/20 text-red-300 border border-red-500/20'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/20'
                      }
                    `}
                    >
                      <span className="text-base">{isOccupied ? '🔴' : '🟢'}</span>
                      {isOccupied ? 'Đang dùng' : 'Trống'}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white mb-1">{station.name}</h3>
                  <p className="text-xs text-slate-500 font-mono">ID: {station.id}</p>

                  {isOccupied && status?.occupied_by_name && (
                    <div className="mt-3 pt-3 border-t border-white/5">
                      <p className="text-xs text-red-300/80">
                        Đang dùng bởi <span className="font-semibold text-red-300">{status.occupied_by_name}</span>
                      </p>
                    </div>
                  )}
                  {isHeldBySelf && (
                    <div className="mt-3 pt-3 border-t border-white/5">
                      <p className="text-xs text-amber-300/80">Phiên của bạn đang giữ trạm này</p>
                    </div>
                  )}
                  {!isOccupied && !isHeldBySelf && (
                    <div className="mt-3 pt-3 border-t border-white/5">
                      <p className="text-xs text-emerald-300/60 group-hover:text-emerald-300 transition-colors">
                        {selecting === station.id ? 'Đang kết nối...' : 'Nhấn để chọn →'}
                      </p>
                    </div>
                  )}
                </button>
              );
            })
          )}
        </div>
      )}

      <p className="text-slate-600 text-xs mt-8">Trạng thái tự động cập nhật mỗi 10 giây</p>
    </div>
  );
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
          <div className="text-center">
            <p className="text-red-400 text-lg font-bold mb-2">Something went wrong</p>
            <button onClick={() => window.location.reload()} className="px-4 py-2 bg-blue-600 text-white rounded-lg">
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [stations, setStations] = useState([]);
  const [activeStationId, setActiveStationId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [initialSettings, setInitialSettings] = useState({});
  const [packingStatus, setPackingStatus] = useState('idle');
  const [currentWaybill, setCurrentWaybill] = useState('');
  const [storageInfo, setStorageInfo] = useState({ size_str: '0 MB', file_count: 0 });

  const [analytics, setAnalytics] = useState({ total_today: 0, station_today: 0 });
  const [reconnectInfo, setReconnectInfo] = useState(null);
  const [previousStationId, setPreviousStationId] = useState(null);

  // Grid View State
  const [viewMode, setViewMode] = useState('single'); // 'single' | 'grid'
  const [adminTab, setAdminTab] = useState('operations'); // 'operations' | 'overview'
  const [cameraMode, setCameraMode] = useState('single-cam'); // 'single-cam' | 'dual' | 'pip'
  const [showDashboard, setShowDashboard] = useState(false);
  const [stationStatuses, setStationStatuses] = useState({}); // { [stationId]: { status, waybill } }

  // Custom Video Player State
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState({ url: '', waybillCode: '' });
  const [showUserModal, setShowUserModal] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [changePasswordForm, setChangePasswordForm] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [changePasswordError, setChangePasswordError] = useState('');
  const [changePasswordSuccess, setChangePasswordSuccess] = useState('');
  const [mtxAvailable, setMtxAvailable] = useState(null);

  // Station Session State (OPERATOR)
  const [stationAssigned, setStationAssigned] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [pipCamSwap, setPipCamSwap] = useState(false);
  const [stationStatusList, setStationStatusList] = useState([]);
  const [recordStreamType, setRecordStreamType] = useState('sub');
  const [updateInfo, setUpdateInfo] = useState(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [updateProgress, setUpdateProgress] = useState(null);
  const [updating, setUpdating] = useState(false);
  const activeRecordIdRef = useRef(null);
  const packingStatusRef = useRef(packingStatus);
  packingStatusRef.current = packingStatus;
  const stationsRef = useRef(stations);
  useEffect(() => {
    stationsRef.current = stations;
  }, [stations]);
  const barcodeSimInputRef = useRef(null);

  // Confirm dialog state
  const { confirmDialog, setConfirmDialog, showConfirmDialog } = useConfirmDialog();

  // Station switch race guard
  const [switchingStation, setSwitchingStation] = useState(false);

  const { toast, showToast } = useToast();

  useEffect(() => {
    if (!currentUser) return;
    let active = true;
    axios
      .get(`${API_BASE}/api/mtx-status`)
      .then(() => {
        if (active) setMtxAvailable(true);
      })
      .catch(() => {
        if (active) setMtxAvailable(false);
      });
    return () => {
      active = false;
    };
  }, [currentUser]);

  useEffect(() => {
    if (!activeSessionId || currentUser?.role === 'ADMIN') return;
    const interval = setInterval(async () => {
      try {
        await axios.post(`${API_BASE}/api/sessions/heartbeat?session_id=${activeSessionId}`);
      } catch {
        // Expected failure during cleanup/unmount
      }
    }, HEARTBEAT_INTERVAL);
    return () => clearInterval(interval);
  }, [activeSessionId, currentUser]);

  const stationsIdStr = useMemo(() => stations.map((s) => s.id).join(','), [stations]);

  // Init fetch
  useEffect(() => {
    if (!currentUser) return;
    fetchStations();
    fetchStorageInfo();
    if (currentUser.role === 'ADMIN') {
      checkSettings();
      checkLiveQuality();
      checkForUpdate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: fetch on currentUser change only, not on fetchStations identity
  }, [currentUser]);

  const checkForUpdate = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/system/update-check`);
      if (res.data) {
        setUpdateInfo(res.data);
      }
    } catch {
      // Update check is optional
    }
  };

  const fetchStations = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/stations`);
      setStations(res.data.data);
      setStationStatuses((prev) => {
        const newStatuses = { ...prev };
        res.data.data.forEach((st) => {
          if (!newStatuses[st.id])
            newStatuses[st.id] = { status: 'idle', waybill: '', processingCount: st.processing_count || 0 };
          else newStatuses[st.id].processingCount = st.processing_count || 0;
        });
        return newStatuses;
      });
      if (res.data.data.length > 0 && !activeStationId) {
        if (currentUser?.role !== 'ADMIN') {
          setActiveStationId(res.data.data[0].id);
        }
      }
    } catch {
      showToast('Không thể tải danh sách trạm.', 'error');
    }
  };

  useEffect(() => {
    if (activeStationId) {
      fetchStatus(activeStationId);
    }
    if (currentUser) {
      fetchAnalytics(activeStationId || '');
    }
  }, [activeStationId, currentUser]);

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
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
      }
    };

    fetchReconnect();
    intervalId = setInterval(fetchReconnect, STATION_POLL_INTERVAL);
    return () => {
      active = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [activeStationId]);

  const fetchAnalytics = async (sid) => {
    try {
      const url = sid ? `${API_BASE}/api/analytics/today?station_id=${sid}` : `${API_BASE}/api/analytics/today`;
      const res = await axios.get(url);
      if (res.data.data) {
        setAnalytics(res.data.data);
      }
    } catch {
      // Analytics fetch is non-critical
    }
  };

  // Lấy trạng thái ghi hình ban đầu
  const fetchStatus = async (sid) => {
    try {
      const res = await axios.get(`${API_BASE}/api/status?station_id=${sid}`);
      if (res.data.status === 'recording') {
        setPackingStatus('packing');
        setCurrentWaybill(res.data.waybill || '');
      } else {
        setPackingStatus('idle');
        setCurrentWaybill('');
      }
    } catch {
      // Status fetch is non-critical
    }
  };

  useEffect(() => {
    if (viewMode !== 'grid' || stations.length === 0) return;
    setStationStatuses((prev) => ({
      ...prev,
      [activeStationId]: { status: packingStatus, waybill: currentWaybill },
    }));
    stations.forEach((st) => {
      axios
        .get(`${API_BASE}/api/status?station_id=${st.id}`)
        .then((res) => {
          const isPacking = res.data.status === 'recording';
          setStationStatuses((prev) => ({
            ...prev,
            [st.id]: { status: isPacking ? 'packing' : 'idle', waybill: res.data.waybill || '' },
          }));
        })
        .catch(() => {
          // Non-critical per-station status fetch
        });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: rebuilds on viewMode/stations change, reads latest state from setters
  }, [viewMode, stations]);

  const fetchStorageInfo = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/storage/info`);
      if (res.data.data) {
        setStorageInfo(res.data.data);
      }
    } catch {
      // Non-critical - storage info optional
    }
  };

  const acquireStation = async (stationId) => {
    try {
      const res = await axios.post(`${API_BASE}/api/sessions/acquire?station_id=${stationId}`);
      if (res.data.status === 'success') {
        setActiveSessionId(res.data.session_id);
        setActiveStationId(stationId);
        setStationAssigned(true);
      } else {
        showToast(res.data.message || 'Không thể chọn trạm.', 'error');
      }
    } catch (err) {
      showToast(err.response?.data?.message || 'Lỗi khi chọn trạm.', 'error');
    }
  };

  const releaseStation = async (stationId) => {
    if (!stationId) return;
    try {
      await axios.post(`${API_BASE}/api/sessions/release?station_id=${stationId}`);
    } catch {
      // Best-effort release
    }
    setActiveSessionId(null);
  };

  const fetchStationStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/sessions/station-status`);
      setStationStatusList(res.data.data || []);
      return res.data.data || [];
    } catch {
      setStationStatusList([]);
      return [];
    }
  };

  const checkSettings = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/settings`);
      setInitialSettings(response.data.data || {});
    } catch {
      // Settings fetch is non-critical
    }
  };

  const checkLiveQuality = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/live-stream-quality`);
      if (response.data.quality) {
        setRecordStreamType(response.data.quality);
      }
    } catch {
      // Live quality check is non-critical
    }
  };

  const toggleRecordStream = async () => {
    const newType = recordStreamType === 'main' ? 'sub' : 'main';
    try {
      const res = await axios.post(`${API_BASE}/api/live-stream-quality`, { quality: newType });
      setRecordStreamType(newType);
      showToast(res.data.message || (newType === 'main' ? 'Live: 1080p (Main)' : 'Live: 480p (Sub)'));
    } catch {
      showToast('Không thể đổi chất lượng live.', 'error');
    }
  };

  // --- Quản lý Bảo mật (Role Gateway) ---
  const requestAdminAccess = (action) => {
    if (currentUser?.role === 'ADMIN') {
      executeSecureAction(action);
    } else {
      showToast('Yêu cầu quyền Administrator.', 'error');
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

  // --- Hàm xoá bản ghi (Đã qua kiểm duyệt bảo mật) ---
  const handleDeleteRecord = (id, waybill_code) => {
    requestAdminAccess({ type: 'delete', id, waybill: waybill_code });
  };

  const doDeleteRecord = async (id, waybill_code) => {
    showConfirmDialog(`Bạn có chắc chắn muốn xoá bản ghi "${waybill_code}" không?`, async () => {
      try {
        await axios.delete(`${API_BASE}/api/records/${id}`);
        fetchRecords(searchTerm, activeStationId, recordsPage);
      } catch {
        showToast('Có lỗi xảy ra khi xoá.', 'error');
      }
    });
  };

  const doCloudSync = async () => {
    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/api/cloud-sync`);
      if (res.data.status === 'success') {
        showToast(res.data.message || 'Đồng bộ thành công.');
      } else {
        showToast('Lỗi Upload: ' + res.data.message, 'error');
      }
      setLoading(false);
    } catch {
      setLoading(false);
      showToast('Đã xảy ra lỗi khi đồng bộ Đám mây.', 'error');
    }
  };

  const activeStation = useMemo(
    () => stations.find((s) => s.id === activeStationId) || {},
    [stations, activeStationId],
  );

  const isDualCamStation = (station) => {
    if (!station) return false;
    const hasIp2 = station.ip_camera_2 && station.ip_camera_2.trim() !== '';
    const isDualMode = ['pip', 'dual_file'].includes(station.camera_mode?.toLowerCase());
    return hasIp2 || isDualMode;
  };

  const hasCam2 = isDualCamStation(activeStation);

  useSSE({
    activeStationId,
    viewMode,
    stationsIdStr,
    currentUser,
    stationsRef,
    setStationStatuses,
    setPackingStatus,
    setCurrentWaybill,
    activeRecordIdRef,
    fetchStorageInfo,
    fetchRecords,
    searchTermRef,
    recordsPageRef,
    setUpdateProgress,
    showToast,
  });

  const { sendScanAction } = useBarcodeScanner({
    currentUser,
    activeStationId,
    searchTerm,
    packingStatusRef,
    showToast,
    fetchRecords,
    recordsPageRef,
    setPackingStatus,
    setCurrentWaybill,
    activeRecordIdRef,
  });

  // Auth State
  const { currentUser, setCurrentUser, authLoading, loginError, loginForm, setLoginForm, handleLogin, handleLogout } =
    useAuth({
      onLoginAdmin: () => {
        setStationAssigned(true);
        setViewMode('grid');
      },
      onRequirePasswordChange: () => setShowChangePassword(true),
      onLogoutAction: async () => {
        if (activeSessionId) {
          await releaseStation(activeStationId);
        }
        setStationAssigned(false);
        setActiveSessionId(null);
        setAdminTab('operations');
      },
    });

  const {
    records,
    searchTerm,
    recordsPage,
    recordsTotal,
    recordsTotalPages,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    statusFilter,
    setStatusFilter,
    fetchRecords,
    handleSearch,
    searchTermRef,
    recordsPageRef,
  } = useRecords({ activeStationId, currentUser, setLoading, fetchAnalytics });

  const doChangePassword = useCallback(async () => {
    setChangePasswordError('');
    if (changePasswordForm.new_password.length < 6) {
      setChangePasswordError('Mật khẩu mới phải có ít nhất 6 ký tự.');
      return;
    }
    if (changePasswordForm.new_password !== changePasswordForm.confirm_password) {
      setChangePasswordError('Mật khẩu xác nhận không khớp.');
      return;
    }
    try {
      await axios.put(`${API_BASE}/api/auth/change-password`, {
        old_password: changePasswordForm.old_password,
        new_password: changePasswordForm.new_password,
      });
      setChangePasswordSuccess('Đổi mật khẩu thành công!');
      setChangePasswordForm({ old_password: '', new_password: '', confirm_password: '' });
      const updatedUser = { ...currentUser, must_change_password: 0 };
      setCurrentUser(updatedUser);
      localStorage.setItem('vpack_user', JSON.stringify(updatedUser));
    } catch (err) {
      setChangePasswordError(err.response?.data?.detail || 'Mật khẩu cũ không đúng.');
    }
  }, [changePasswordForm, currentUser]);

  useEffect(() => {
    if (!hasCam2) setCameraMode('single-cam');
  }, [activeStationId, hasCam2]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4 md:p-4">
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
          <form
            onSubmit={handleLogin}
            className="bg-white/5 border border-white/10 rounded-3xl p-4 md:p-8 backdrop-blur-md shadow-2xl"
          >
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
                onChange={(e) => setLoginForm((f) => ({ ...f, username: e.target.value }))}
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-base text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                placeholder="Nhập tên đăng nhập"
                autoFocus
              />
            </div>
            <div className="mb-6">
              <label className="block text-sm text-slate-400 mb-2">Mật khẩu</label>
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm((f) => ({ ...f, password: e.target.value }))}
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-xl text-base text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                placeholder="Nhập mật khẩu"
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 min-h-[44px] bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 rounded-xl font-semibold text-white shadow-lg transition-all"
            >
              Đăng Nhập
            </button>
          </form>
          <p className="text-center text-xs text-slate-500 mt-6">V-Pack Monitor • VDT</p>
        </div>
      </div>
    );
  }

  if (currentUser && !stationAssigned && currentUser.role !== 'ADMIN') {
    return (
      <div className="min-h-screen bg-[#09090b] text-white flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center border border-blue-400/30">
              <PackageCheck className="text-blue-400 w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                V-Pack Monitor
              </h1>
              <p className="text-xs text-slate-400">Chọn trạm làm việc</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-slate-400 hover:text-white transition-all"
          >
            <LogOut className="w-4 h-4" />
            Đăng xuất
          </button>
        </div>

        <StationSelectionScreen
          stations={stations}
          stationStatusList={stationStatusList}
          fetchStationStatus={fetchStationStatus}
          acquireStation={acquireStation}
          currentUser={currentUser}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-3 md:p-6 lg:p-10 font-sans">
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
        showConfirmDialog={showConfirmDialog}
      />

      {showChangePassword && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => {
            if (!currentUser?.must_change_password) setShowChangePassword(false);
            setChangePasswordError('');
            setChangePasswordSuccess('');
          }}
        >
          <div
            className="bg-slate-900 border border-white/10 rounded-3xl p-6 w-full max-w-sm shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-400" />
                Đổi Mật Khẩu
              </h3>
              <button
                onClick={() => {
                  if (!currentUser?.must_change_password) {
                    setShowChangePassword(false);
                    setChangePasswordError('');
                    setChangePasswordSuccess('');
                  }
                }}
                className="p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
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
                    onChange={(e) => setChangePasswordForm((f) => ({ ...f, old_password: e.target.value }))}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Mật khẩu mới</label>
                  <input
                    type="password"
                    value={changePasswordForm.new_password}
                    onChange={(e) => setChangePasswordForm((f) => ({ ...f, new_password: e.target.value }))}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Xác nhận mật khẩu mới</label>
                  <input
                    type="password"
                    value={changePasswordForm.confirm_password}
                    onChange={(e) => setChangePasswordForm((f) => ({ ...f, confirm_password: e.target.value }))}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        doChangePassword();
                      }
                    }}
                  />
                </div>
                <button
                  onClick={doChangePassword}
                  className="w-full py-2.5 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 rounded-xl font-semibold text-white shadow-lg transition-all text-sm"
                >
                  Xác Nhận Đổi Mật Khẩu
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {showUpdateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-white/10 rounded-3xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-blue-400" />
                Cập Nhật Hệ Thống
              </h3>
              {!updating && (
                <button
                  onClick={() => setShowUpdateModal(false)}
                  className="p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>

            <div className="space-y-3 mb-5">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Phiên bản hiện tại:</span>
                <span className="text-white font-mono">{updateInfo?.current_version}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Phiên bản mới:</span>
                <span className="text-amber-300 font-mono font-semibold">{updateInfo?.latest_version}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Chế độ:</span>
                <span className="text-slate-200">
                  {updateInfo?.mode === 'dev' ? 'Development (Git)' : 'Production (Release)'}
                </span>
              </div>
            </div>

            {updateInfo?.changelog && (
              <div className="mb-4 p-3 bg-black/30 border border-white/5 rounded-xl text-xs text-slate-300 max-h-32 overflow-y-auto whitespace-pre-wrap">
                {updateInfo.changelog}
              </div>
            )}

            {updateProgress && (
              <div className="mb-4 space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-blue-500"></div>
                  <span className="text-slate-300">{updateProgress.message}</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${updateProgress.progress}%` }}
                  />
                </div>
              </div>
            )}

            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-200 mb-4">
              Hệ thống sẽ khởi động lại sau khi cập nhật. Video đang ghi sẽ được lưu tự động.
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowUpdateModal(false)}
                disabled={updating}
                className="flex-1 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-slate-300 transition-all disabled:opacity-50"
              >
                Hủy
              </button>
              <button
                onClick={async () => {
                  setUpdating(true);
                  try {
                    const res = await axios.post(`${API_BASE}/api/system/update`);
                    if (res.data.status === 'error') {
                      setUpdating(false);
                      setUpdateProgress({ stage: 'error', message: res.data.message, progress: 0 });
                    }
                  } catch {
                    if (!updateProgress || updateProgress.stage !== 'restarting') {
                      setUpdating(false);
                      setUpdateProgress({ stage: 'error', message: 'Lỗi kết nối server.', progress: 0 });
                    }
                  }
                }}
                disabled={updating}
                className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 rounded-xl font-semibold text-white shadow-lg transition-all text-sm disabled:opacity-50"
              >
                {updating ? 'Đang cập nhật...' : 'Cập Nhật Ngay'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="flex flex-col mb-4 md:mb-8">
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

          <div className="mt-4 md:mt-6 flex items-center gap-2 md:gap-3 w-full md:w-auto flex-wrap">
            {/* Station Selector Dropdown */}
            {!(currentUser?.role === 'ADMIN' && viewMode === 'grid') && (
              <div className="relative group flex items-center border border-white/10 rounded-xl bg-white/5 h-10 min-h-[44px] px-2 md:px-3 shadow-lg">
                <Monitor className="w-5 h-5 text-indigo-400 mr-2" />
                <select
                  value={activeStationId}
                  onChange={async (e) => {
                    const newId = Number(e.target.value);
                    if (switchingStation) return;
                    if (currentUser?.role === 'OPERATOR' && activeStationId !== newId) {
                      setSwitchingStation(true);
                      try {
                        const statusRes = await axios.get(`${API_BASE}/api/sessions/station-status`);
                        const targetStatus = (statusRes.data.data || []).find((s) => s.station_id === newId);
                        if (targetStatus?.occupied && targetStatus?.occupied_by !== currentUser.username) {
                          showToast(
                            'Trạm này đang được sử dụng bởi ' +
                              (targetStatus.occupied_by_name || targetStatus.occupied_by),
                            'error',
                          );
                          return;
                        }
                        await releaseStation(activeStationId);
                        const acquireRes = await axios.post(`${API_BASE}/api/sessions/acquire?station_id=${newId}`);
                        if (acquireRes.data.status === 'success') {
                          setActiveSessionId(acquireRes.data.session_id);
                          setActiveStationId(newId);
                        } else {
                          showToast(acquireRes.data.message || 'Không thể chuyển trạm.', 'error');
                          const reacquireRes = await axios.post(
                            `${API_BASE}/api/sessions/acquire?station_id=${activeStationId}`,
                          );
                          if (reacquireRes.data.status === 'success') {
                            setActiveSessionId(reacquireRes.data.session_id);
                          }
                        }
                      } catch {
                        showToast('Lỗi khi chuyển trạm.', 'error');
                      } finally {
                        setSwitchingStation(false);
                      }
                    } else {
                      setActiveStationId(newId);
                    }
                  }}
                  disabled={switchingStation}
                  className="bg-transparent text-slate-200 focus:outline-none appearance-none font-semibold cursor-pointer pr-4 min-h-[44px]"
                >
                  {stations.map((st) => (
                    <option key={st.id} value={st.id} className="bg-slate-800">
                      Trạm: {st.name}
                    </option>
                  ))}
                  {stations.length === 0 && (
                    <option value={0} disabled>
                      Chưa có trạm nào
                    </option>
                  )}
                </select>
                {currentUser?.role === 'ADMIN' && (
                  <button
                    title="Thêm Trạm Mới"
                    onClick={() => requestAdminAccess({ type: 'setup', isNew: true })}
                    className="ml-2 h-8 w-8 flex items-center justify-center hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}

            {/* Admin Tab Navigation */}
            {currentUser?.role === 'ADMIN' && viewMode === 'grid' && (
              <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 border border-white/10">
                <button
                  onClick={() => setAdminTab('operations')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    adminTab === 'operations'
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  📹 Vận hành
                </button>
                <button
                  onClick={() => setAdminTab('overview')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    adminTab === 'overview'
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  📊 Tổng quan
                </button>
              </div>
            )}

            {/* Back to Tổng quan (Admin only) */}
            {viewMode === 'single' && currentUser?.role === 'ADMIN' && (
              <button
                onClick={() => {
                  setViewMode('grid');
                  setAdminTab('operations');
                }}
                className="hidden md:flex h-10 items-center justify-center px-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-blue-500/30 rounded-xl transition-all shadow-lg text-slate-400 hover:text-blue-400 font-medium text-sm gap-2"
                title="Quay lại giao diện tổng quan"
              >
                ← Tổng quan
              </button>
            )}

            {currentUser?.role === 'ADMIN' && updateInfo && (
              <button
                onClick={() => {
                  if (updateInfo.update_available) {
                    setUpdateProgress(null);
                    setUpdating(false);
                    setShowUpdateModal(true);
                  }
                }}
                className={`hidden md:flex items-center gap-1.5 px-3 h-10 rounded-xl border text-xs font-semibold transition-all shadow-lg ${
                  updateInfo.update_available
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20 cursor-pointer'
                    : 'bg-white/5 border-white/10 text-slate-500 cursor-default'
                }`}
                title={
                  updateInfo.update_available
                    ? `Có bản mới: ${updateInfo.latest_version}`
                    : `Phiên bản mới nhất: ${updateInfo.current_version}`
                }
              >
                <RefreshCw className="w-3.5 h-3.5" />
                {updateInfo.current_version}
                {updateInfo.update_available && <span className="text-amber-200">({updateInfo.latest_version})</span>}
              </button>
            )}

            {!(currentUser?.role === 'ADMIN' && viewMode === 'grid') && (
              <button
                onClick={() => setShowDashboard((prev) => !prev)}
                className={`hidden md:flex h-10 w-10 items-center justify-center border rounded-xl transition-all shadow-lg ${showDashboard ? 'bg-blue-500/20 border-blue-500/50 text-blue-400' : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-blue-500/30 text-slate-400 hover:text-blue-400'}`}
                title={showDashboard ? 'Quay lại giao diện chính' : 'Bảng điều khiển'}
              >
                <BarChart3 className="w-5 h-5" />
              </button>
            )}

            <div className="relative w-full md:w-64 group order-last md:order-none">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
              </div>
              <input
                type="text"
                className="block w-full pl-11 pr-4 h-10 min-h-[44px] bg-white/5 border border-white/10 rounded-xl text-base md:text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 backdrop-blur-md transition-all shadow-lg"
                placeholder="Tìm mã vận đơn..."
                value={searchTerm}
                onChange={handleSearch}
              />
            </div>

            <div className="relative">
              <button
                onClick={() => setShowUserDropdown(!showUserDropdown)}
                className="flex items-center gap-2.5 bg-white/5 border border-white/10 rounded-xl px-3 py-2 min-h-[44px] hover:bg-white/10 transition-all"
              >
                <User className="w-5 h-5 text-blue-400" />
                <div className="hidden sm:flex flex-col items-start">
                  <span className="text-sm text-slate-200 font-medium">
                    {currentUser.full_name || currentUser.username}
                  </span>
                  <span className="text-[10px] text-slate-400 uppercase">{currentUser.role}</span>
                </div>
                <span className="sm:hidden text-xs text-slate-300 font-medium">{currentUser.username}</span>
                <svg
                  className={`w-3.5 h-3.5 text-slate-400 transition-transform ${showUserDropdown ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showUserDropdown && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowUserDropdown(false)} />
                  <div className="absolute right-0 top-full mt-2 w-56 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-20 py-1 overflow-hidden">
                    {currentUser?.role === 'ADMIN' && (
                      <>
                        <button
                          onClick={() => {
                            setShowUserDropdown(false);
                            requestAdminAccess({ type: 'cloud_sync' });
                          }}
                          className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-indigo-300 hover:bg-indigo-500/10 hover:text-indigo-200 transition-colors text-left"
                        >
                          <CloudUpload className="w-4 h-4" />
                          Đẩy Video lên Cloud
                        </button>
                        <button
                          onClick={() => {
                            setShowUserDropdown(false);
                            requestAdminAccess({ type: 'setup' });
                          }}
                          className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-blue-300 hover:bg-blue-500/10 hover:text-blue-200 transition-colors text-left"
                        >
                          <Settings className="w-4 h-4" />
                          Cài đặt Trạm
                        </button>
                        <button
                          onClick={() => {
                            setShowUserDropdown(false);
                            setShowUserModal(true);
                          }}
                          className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-emerald-300 hover:bg-emerald-500/10 hover:text-emerald-200 transition-colors text-left"
                        >
                          <Users className="w-4 h-4" />
                          Quản lý người dùng
                        </button>
                        <div className="border-t border-white/5 my-1"></div>
                      </>
                    )}
                    <button
                      onClick={() => {
                        setShowUserDropdown(false);
                        setShowChangePassword(true);
                      }}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/10 hover:text-white transition-colors text-left"
                    >
                      <ShieldCheck className="w-4 h-4 text-slate-400" />
                      Đổi mật khẩu
                    </button>
                    <button
                      onClick={() => {
                        setShowUserDropdown(false);
                        handleLogout();
                      }}
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
      </header>

      {toast && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-6 py-3 bg-amber-500/90 backdrop-blur-md border border-amber-400/50 rounded-xl text-white text-sm font-medium shadow-2xl animate-pulse">
          {toast}
        </div>
      )}

      {/* Main Content */}
      {showDashboard && currentUser?.role !== 'ADMIN' ? (
        <Dashboard
          stations={stations}
          activeStationId={activeStationId}
          storageInfo={storageInfo}
          currentUser={currentUser}
          analytics={analytics}
        />
      ) : (
        <div
          className={`grid gap-4 md:gap-8 ${viewMode === 'grid' || currentUser?.role === 'ADMIN' ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-3'}`}
        >
          {/* Left Column: Live Camera / Grid */}
          <div
            className={`${viewMode === 'grid' || currentUser?.role === 'ADMIN' ? 'lg:col-span-1' : 'lg:col-span-2'} flex flex-col gap-4`}
          >
            {currentUser?.role === 'ADMIN' && viewMode === 'grid' ? (
              adminTab === 'operations' ? (
                <AdminDashboard
                  stations={stations}
                  stationStatuses={stationStatuses}
                  reconnectInfo={reconnectInfo}
                  mtxAvailable={mtxAvailable}
                  isDualCamStation={isDualCamStation}
                  MTX_HOST={MTX_HOST}
                  onStationClick={(id) => {
                    setActiveStationId(id);
                    setViewMode('single');
                  }}
                />
              ) : (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <Dashboard
                    stations={stations}
                    activeStationId={''}
                    storageInfo={storageInfo}
                    currentUser={currentUser}
                    analytics={analytics}
                  />
                </div>
              )
            ) : viewMode === 'grid' ? (
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
                  <div
                    className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                    style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))' }}
                  >
                    {stations.map((station) => {
                      const st = stationStatuses[station.id] || { status: 'idle', waybill: '' };
                      return (
                        <div
                          key={station.id}
                          onClick={() => {
                            setActiveStationId(station.id);
                            setViewMode('single');
                          }}
                          className="relative group rounded-3xl overflow-hidden bg-zinc-900 border border-white/10 hover:border-blue-400/30 shadow-2xl shadow-blue-900/20 aspect-video flex items-center justify-center cursor-pointer transition-all duration-300 hover:scale-[1.02]"
                        >
                          {mtxAvailable ? (
                            <iframe
                              key={`grid-${station.id}`}
                              src={`http://${MTX_HOST}:8889/station_${station.id}?controls=false&muted=true&autoplay=true`}
                              scrolling="no"
                              className="w-full h-full object-cover"
                              style={{ border: 'none', background: '#000' }}
                              allow="autoplay"
                            />
                          ) : (
                            <MtxFallback />
                          )}
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
                            {st.status === 'packing' && (
                              <div className="px-3 py-1.5 rounded-full bg-red-600/90 backdrop-blur-md border border-red-400 text-xs font-bold text-white flex items-center gap-2 animate-pulse">
                                <div className="w-2 h-2 rounded-full bg-white"></div>
                                Đang đóng: {st.waybill}
                              </div>
                            )}
                            {st.status === 'idle' && (
                              <div className="px-3 py-1.5 rounded-full bg-emerald-600/90 backdrop-blur-md border border-emerald-400 text-xs font-bold text-white flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-white"></div>
                                Sẵn sàng
                              </div>
                            )}
                          </div>
                          {isDualCamStation(station) && (
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
                    {currentUser?.role === 'ADMIN' && (
                      <button
                        onClick={() => setViewMode('grid')}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-sm text-slate-400 hover:text-white transition"
                      >
                        <LayoutGrid className="w-4 h-4" />
                        Tổng quan
                      </button>
                    )}
                    {hasCam2 && (
                      <div className="flex items-center gap-1 bg-white/5 border border-white/10 rounded-xl p-0.5">
                        <button
                          onClick={() => setCameraMode('single-cam')}
                          className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${cameraMode === 'single-cam' ? 'bg-blue-500/20 text-blue-300' : 'text-slate-400 hover:text-white'}`}
                        >
                          1 Cam
                        </button>
                        <button
                          onClick={() => setCameraMode('dual')}
                          className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${cameraMode === 'dual' ? 'bg-blue-500/20 text-blue-300' : 'text-slate-400 hover:text-white'}`}
                        >
                          Dual
                        </button>
                        <button
                          onClick={() => setCameraMode('pip')}
                          className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${cameraMode === 'pip' ? 'bg-blue-500/20 text-blue-300' : 'text-slate-400 hover:text-white'}`}
                        >
                          PIP
                        </button>
                      </div>
                    )}
                    {currentUser?.role === 'ADMIN' && (
                      <button
                        onClick={toggleRecordStream}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-medium border transition-all ${
                          recordStreamType === 'sub'
                            ? 'bg-amber-500/15 border-amber-500/30 text-amber-300'
                            : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
                        }`}
                        title={
                          recordStreamType === 'sub'
                            ? 'Đang xem sub-stream (480p). Bấm để chuyển 1080p.'
                            : 'Đang xem main-stream (1080p). Bấm để chuyển 480p.'
                        }
                      >
                        <Video className="w-3.5 h-3.5" />
                        Live: {recordStreamType === 'sub' ? '480p' : '1080p'}
                      </button>
                    )}
                  </div>
                  <span className="flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                  </span>
                </div>

                <div className="relative group rounded-3xl overflow-hidden bg-zinc-900 border border-white/10 shadow-2xl shadow-blue-900/20 aspect-[4/3] md:aspect-video flex items-center justify-center">
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

                      {!mtxAvailable ? (
                        <MtxFallback />
                      ) : hasCam2 && cameraMode === 'dual' ? (
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
                            <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-xs text-white/80 pointer-events-none">
                              Camera 1
                            </div>
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
                            <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-xs text-white/80 pointer-events-none">
                              Camera 2
                            </div>
                          </div>
                        </div>
                      ) : hasCam2 && cameraMode === 'pip' ? (
                        <div className="absolute inset-0">
                          <iframe
                            key={`live-${activeStationId}-${pipCamSwap}`}
                            src={`http://${MTX_HOST}:8889/station_${activeStationId}${pipCamSwap ? '_cam2' : ''}?controls=false&muted=true&autoplay=true`}
                            scrolling="no"
                            className="w-full h-full object-cover"
                            style={{ border: 'none', background: '#000' }}
                            allow="autoplay"
                          />
                          <div
                            onClick={() => setPipCamSwap(!pipCamSwap)}
                            className="absolute bottom-3 right-3 w-1/4 h-1/4 rounded-xl overflow-hidden border-2 border-white/20 shadow-2xl z-20 cursor-pointer hover:border-blue-400/50 transition-colors"
                          >
                            <iframe
                              key={`pip-cam2-${activeStationId}-${pipCamSwap}`}
                              src={`http://${MTX_HOST}:8889/station_${activeStationId}${pipCamSwap ? '' : '_cam2'}?controls=false&muted=true&autoplay=true`}
                              scrolling="no"
                              className="w-full h-full object-cover"
                              style={{ border: 'none', background: '#000' }}
                              allow="autoplay"
                            />
                            <div className="absolute bottom-1 left-1 px-1.5 py-0.5 bg-black/60 rounded text-[10px] text-white/80 pointer-events-none">
                              {pipCamSwap ? 'Camera 1' : 'Camera 2'}
                              <span className="ml-1 text-blue-300">⇄</span>
                            </div>
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
                            {activeStation?.name || 'Đang tải'}
                          </div>
                          {currentUser?.role !== 'ADMIN' && packingStatus === 'packing' && (
                            <div className="px-3 py-1.5 rounded-full bg-red-600/90 backdrop-blur-md border border-red-400 text-xs font-bold text-white flex items-center gap-2 animate-pulse transition-all">
                              <div className="w-2 h-2 rounded-full bg-white"></div>
                              Đang đóng hàng: {currentWaybill}
                            </div>
                          )}
                          {currentUser?.role !== 'ADMIN' && packingStatus === 'idle' && (
                            <div className="px-3 py-1.5 rounded-full bg-emerald-600/90 backdrop-blur-md border border-emerald-400 text-xs font-bold text-white flex items-center gap-2 transition-all">
                              <div className="w-2 h-2 rounded-full bg-white"></div>
                              Sẵn sàng
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
                        <button
                          onClick={() => requestAdminAccess({ type: 'setup', isNew: true })}
                          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg"
                        >
                          Cài đặt ngay
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {currentUser?.role !== 'ADMIN' && (
                  <div className="p-3 md:p-5 rounded-2xl bg-white/5 border border-purple-500/30 backdrop-blur-lg mt-2 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 bg-purple-500/20 text-purple-300 text-[10px] px-3 py-1 rounded-bl-xl font-mono border-l border-b border-purple-500/20 hidden md:block">
                      DEV MODE
                    </div>
                    <h3 className="font-medium text-slate-200 mb-3 md:mb-4 flex items-center gap-2">
                      <Box className="w-4 h-4 text-purple-400" />
                      <span className="md:hidden">Quét Mã Vạch</span>
                      <span className="hidden md:inline">Công Cụ Giả Lập Máy Quét (Manual Simulator)</span>
                    </h3>

                    <div className="flex flex-col sm:flex-row gap-3">
                      <input
                        type="text"
                        placeholder="Nhập mã vận đơn (VD: SPX12345)"
                        className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 md:py-2.5 text-base md:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500/50 font-mono min-h-[44px]"
                        ref={barcodeSimInputRef}
                        inputMode="text"
                        enterKeyHint="send"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && e.target.value.trim()) {
                            sendScanAction(e.target.value.trim());
                            e.target.value = '';
                          }
                        }}
                      />
                      <div className="flex gap-2 sm:gap-3">
                        <button
                          onClick={() => {
                            const inputUI = barcodeSimInputRef.current;
                            if (inputUI && inputUI.value.trim()) {
                              sendScanAction(inputUI.value.trim());
                              inputUI.value = '';
                            }
                          }}
                          className="flex-1 sm:flex-none px-4 md:px-6 py-3.5 md:py-2.5 bg-purple-600 hover:bg-purple-500 rounded-xl font-medium text-white shadow-lg transition-colors border border-purple-400/20 min-h-[44px] text-base md:text-sm"
                        >
                          <span className="md:hidden">Ghi</span>
                          <span className="hidden md:inline">Bắt Đầu Ghi</span>
                        </button>
                        <button
                          onClick={() => sendScanAction('STOP')}
                          className="flex-1 sm:flex-none px-4 md:px-6 py-3.5 md:py-2.5 bg-slate-800 hover:bg-rose-600 rounded-xl font-medium text-white shadow-lg transition-colors border border-white/10 min-h-[44px] text-base md:text-sm"
                        >
                          STOP
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 mt-3 md:mt-4 leading-relaxed italic">
                      * Sử dụng thanh công cụ này nếu bạn không có súng bắn mã vạch. Hệ thống sẽ kết nối với Camera ở
                      Trạm đang chọn.
                    </p>
                  </div>
                )}
              </>
            )}
          </div>

          {(viewMode !== 'grid' || (currentUser?.role === 'ADMIN' && adminTab === 'operations')) && (
            <div className="flex flex-col gap-4 h-[calc(100vh-160px)] md:h-[calc(100vh-200px)]">
              <div className="flex items-center justify-between pointer-events-none">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-emerald-400" />
                  Lịch sử ghi hình
                </h2>
                <div className="px-3 py-1 bg-white/10 rounded-full text-xs font-semibold">{recordsTotal} video</div>
              </div>

              {/* Filter Bar */}
              <div className="flex flex-wrap items-center gap-2 px-4 py-2 bg-white/5 border-b border-white/10 rounded-xl">
                {currentUser?.role === 'ADMIN' && (
                  <select
                    value={activeStationId || ''}
                    onChange={(e) => {
                      const val = e.target.value;
                      setActiveStationId(val === '' || val === 'orphaned' ? val : Number(val));
                    }}
                    className="bg-white/10 text-white text-xs rounded px-2 py-1 border border-white/20 focus:outline-none focus:border-blue-400"
                    style={{ colorScheme: 'dark' }}
                  >
                    <option value="" className="bg-slate-800">
                      Tất cả trạm
                    </option>
                    <option value="orphaned" className="bg-slate-800">
                      (trạm đã xoá)
                    </option>
                    {stations.map((st) => (
                      <option key={st.id} value={st.id} className="bg-slate-800">
                        {st.name}
                      </option>
                    ))}
                  </select>
                )}
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="bg-white/10 text-white text-xs rounded px-2 py-1 border border-white/20 focus:outline-none focus:border-blue-400"
                  style={{ colorScheme: 'dark' }}
                />
                <span className="text-white/50 text-xs">→</span>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="bg-white/10 text-white text-xs rounded px-2 py-1 border border-white/20 focus:outline-none focus:border-blue-400"
                  style={{ colorScheme: 'dark' }}
                />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-white/10 text-white text-xs rounded px-2 py-1 border border-white/20 focus:outline-none focus:border-blue-400"
                  style={{ colorScheme: 'dark' }}
                >
                  <option value="" className="bg-slate-800">
                    Tất cả trạng thái
                  </option>
                  <option value="READY" className="bg-slate-800">
                    ✅ READY
                  </option>
                  <option value="RECORDING" className="bg-slate-800">
                    🔴 RECORDING
                  </option>
                  <option value="PROCESSING" className="bg-slate-800">
                    ⏳ PROCESSING
                  </option>
                  <option value="FAILED" className="bg-slate-800">
                    ❌ FAILED
                  </option>
                </select>
                {(dateFrom || dateTo || statusFilter) && (
                  <button
                    onClick={() => {
                      setDateFrom('');
                      setDateTo('');
                      setStatusFilter('');
                    }}
                    className="text-xs text-red-400 hover:text-red-300 px-2 py-1"
                  >
                    ✕ Xóa bộ lọc
                  </button>
                )}
                <div className="ml-auto text-xs text-white/50">{recordsTotal} video</div>
              </div>

              <div className="flex-1 overflow-y-auto pr-0 md:pr-2 space-y-3 md:space-y-4">
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
                  <>
                    {records.map((record) => (
                      <div
                        key={record.id}
                        className="group p-3 md:p-5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-blue-400/30 backdrop-blur-md transition-all duration-300 shadow-lg cursor-pointer min-h-[44px]"
                      >
                        <div className="flex justify-between items-start mb-2 md:mb-3">
                          <div className="flex items-center gap-2 md:gap-3 flex-wrap">
                            <h3 className="text-base md:text-lg font-bold text-white group-hover:text-blue-300 transition-colors">
                              {record.waybill_code}
                            </h3>
                            <span className="px-2 py-1 bg-white/10 rounded uppercase text-[10px] font-bold tracking-wider text-slate-300">
                              {record.record_mode}
                            </span>
                            {record.status && record.status !== 'READY' && (
                              <span
                                className={`px-2 py-1 rounded text-[10px] font-bold tracking-wider ${
                                  record.status === 'RECORDING'
                                    ? 'bg-red-500/30 text-red-300 animate-pulse'
                                    : record.status === 'PROCESSING'
                                      ? 'bg-amber-500/30 text-amber-300 animate-pulse'
                                      : record.status === 'FAILED'
                                        ? 'bg-red-500/30 text-red-300'
                                        : 'bg-white/10 text-slate-300'
                                }`}
                              >
                                {record.status === 'RECORDING'
                                  ? 'Đang ghi hình'
                                  : record.status === 'PROCESSING'
                                    ? 'Đang xử lý'
                                    : record.status === 'FAILED'
                                      ? 'Lỗi'
                                      : record.status === 'DELETED'
                                        ? 'Đã xoá'
                                        : record.status}
                              </span>
                            )}
                            <span className="px-2 py-1 bg-blue-500/20 border border-blue-500/30 text-blue-300 rounded text-[10px] font-bold">
                              Trạm:{' '}
                              {record.station_name
                                ? record.station_name
                                : record.station_id
                                  ? '(trạm đã xoá)'
                                  : 'Mặc định'}
                            </span>
                          </div>
                          {currentUser?.role === 'ADMIN' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteRecord(record.id, record.waybill_code);
                              }}
                              className="p-2 -mr-2 -mt-2 text-slate-500 hover:text-rose-400 hover:bg-rose-400/10 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                              title="Xoá bản ghi lưu trữ dọn ổ đĩa"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>

                        <div className="flex items-center gap-3 mb-3 md:mb-4 text-xs text-slate-400 font-mono">
                          <span>{new Date(record.recorded_at).toLocaleString('vi-VN')}</span>
                          {record.duration > 0 && (
                            <span className="px-2 py-0.5 bg-white/5 rounded text-emerald-400 border border-emerald-500/20">
                              ⏱ {Math.floor(record.duration / 60)}:
                              {Math.floor(record.duration % 60)
                                .toString()
                                .padStart(2, '0')}
                            </span>
                          )}
                        </div>

                        {/* Danh sách các file video lưu trữ */}
                        <div className="space-y-2">
                          {record.video_paths.map((path, idx) => {
                            const fileName = path.split(/[/\\]/).pop();
                            const videoUrl = `${API_BASE}/api/records/${record.id}/download/${idx}?token=${encodeURIComponent(localStorage.getItem('vpack_token') || '')}`;
                            return (
                              <div
                                key={idx}
                                role="button"
                                onClick={() => {
                                  if (record.status && record.status !== 'READY' && record.status !== 'FAILED') return;
                                  setSelectedVideo({ url: videoUrl, waybillCode: record.waybill_code });
                                  setVideoModalOpen(true);
                                }}
                                className={`flex items-center gap-2 p-2 rounded-lg bg-black/20 border border-white/5 text-sm min-h-[44px] ${
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
                    ))}
                    {/* Pagination */}
                    {recordsTotalPages > 1 && (
                      <div className="flex items-center justify-center gap-3 py-3 border-t border-white/10">
                        <button
                          onClick={() => fetchRecords(searchTermRef.current, activeStationId, recordsPage - 1)}
                          disabled={recordsPage <= 1}
                          className="px-3 py-1 text-xs rounded bg-white/10 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white/20"
                        >
                          ← Trước
                        </button>
                        <span className="text-xs text-white/70">
                          Trang {recordsPage}/{recordsTotalPages}
                        </span>
                        <button
                          onClick={() => fetchRecords(searchTermRef.current, activeStationId, recordsPage + 1)}
                          disabled={recordsPage >= recordsTotalPages}
                          className="px-3 py-1 text-xs rounded bg-white/10 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white/20"
                        >
                          Sau →
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Confirm Dialog */}
      {confirmDialog.show && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-zinc-800 rounded-lg p-6 max-w-sm">
            <p className="text-white mb-4">{confirmDialog.message}</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmDialog({ show: false })}
                className="px-4 py-2 text-zinc-400 hover:text-white"
              >
                Huỷ
              </button>
              <button
                onClick={() => {
                  confirmDialog.onConfirm?.();
                  setConfirmDialog({ show: false });
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg"
              >
                Xác nhận
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const AppWithErrorBoundary = () => (
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);
export default AppWithErrorBoundary;
