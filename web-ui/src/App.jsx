import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, MonitorPlay, Video, Calendar, Box, PackageCheck, Settings, Trash2, HardDrive, Plus, Monitor, ShieldCheck, BarChart3, CloudUpload } from 'lucide-react';
import SetupModal from './SetupModal';
import PinModal from './PinModal';
import VideoPlayerModal from './VideoPlayerModal';

const API_BASE = window.location.hostname === 'localhost' && ['3000', '3001', '5173'].includes(window.location.port) 
  ? 'http://localhost:8001' 
  : window.location.origin;

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
  
  // Security & Analytics State
  const [isAdminAuth, setIsAdminAuth] = useState(false);
  const [showPinModal, setShowPinModal] = useState(false);
  const [pendingAction, setPendingAction] = useState(null); // 'setup' or {type: 'delete', id: ...}
  const [analytics, setAnalytics] = useState({ total_today: 0, station_today: 0 });
  const [previousStationId, setPreviousStationId] = useState(null);
  
  // Custom Video Player State
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState({ url: '', waybillCode: '' });

  // Init fetch
  useEffect(() => {
    fetchStations();
    checkSettings();
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
        setRecordingStatus('recording');
        setCurrentWaybill(finalBarcode);
      } else if (res.data.status === 'stopped' || res.data.status === 'exit') {
        setRecordingStatus('idle');
        setCurrentWaybill('');
        fetchRecords(searchTerm, activeStationId); 
      }
    } catch (err) {
      console.error("Barcode Lỗi", err);
    }
  };

  // --- Quản lý Bảo mật (PIN Gateway) ---
  const requestAdminAccess = (action) => {
    if (isAdminAuth) {
      executeSecureAction(action);
    } else {
      setPendingAction(action);
      setShowPinModal(true);
    }
  };

  const executeSecureAction = (action) => {
    if (action.type === 'setup') {
      if (action.isNew) {
        setPreviousStationId(activeStationId);
        setActiveStationId(0);
      }
      setShowSetupModal(true);
    } else if (action.type === 'delete') {
      doDeleteRecord(action.id, action.waybill);
    } else if (action.type === 'cloud_sync') {
      doCloudSync();
    }
  };

  const handlePinSuccess = () => {
    setIsAdminAuth(true);
    setShowPinModal(false);
    if (pendingAction) {
      executeSecureAction(pendingAction);
      setPendingAction(null);
    }
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
        setIsAdminAuth(false); // Khoá lại sau khi xoá
      } catch (err) {
        alert("Có lỗi xảy ra khi xoá.");
      }
    } else {
      setIsAdminAuth(false); // Khoá lại nếu huỷ
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
      setIsAdminAuth(false); // Khoá lại
    } catch (e) {
      setLoading(false);
      setIsAdminAuth(false);
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

  return (
    <div className="min-h-screen p-6 md:p-10 font-sans">
      <PinModal 
        isOpen={showPinModal} 
        onSuccess={handlePinSuccess} 
        onCancel={() => { setShowPinModal(false); setPendingAction(null); }} 
      />
      
      {showSetupModal && (
        <SetupModal 
          isOpen={showSetupModal}
          initialSettings={initialSettings} 
          currentStation={activeStation}
          isNewStation={!activeStation.id}
          onSaved={() => {
            setShowSetupModal(false);
            setIsAdminAuth(false);
            window.location.reload(); 
          }} 
          onCancel={() => {
            setShowSetupModal(false);
            setIsAdminAuth(false);
            if (activeStationId === 0 && previousStationId) {
              setActiveStationId(previousStationId);
            } else if (activeStationId === 0 && stations.length > 0) {
              setActiveStationId(stations[0].id);
            }
          }}
        />
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
             <button title="Thêm Trạm Mới" onClick={() => requestAdminAccess({ type: 'setup', isNew: true })} className="ml-2 p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition">
                <Plus className="w-4 h-4" />
             </button>
          </div>

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
          
          <button 
            onClick={() => requestAdminAccess({ type: 'cloud_sync' })}
            className="p-3 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 rounded-2xl transition-all shadow-lg hidden md:flex text-indigo-400"
            title="Đẩy Video lên Cloud"
          >
            <CloudUpload className="w-6 h-6" />
          </button>
          
          <button 
            onClick={() => requestAdminAccess({ type: 'setup' })}
            className={`p-3 border rounded-2xl transition-all shadow-lg hidden md:flex ${isAdminAuth ? 'bg-blue-600/30 border-blue-500 text-blue-300' : 'bg-white/5 hover:bg-blue-500/20 border-white/10 hover:border-blue-500/50 text-slate-400 hover:text-blue-400'}`}
            title="Cài đặt Camera & Hệ thống cho Trạm này"
          >
            {isAdminAuth ? <ShieldCheck className="w-6 h-6" /> : <Settings className="w-6 h-6" />}
          </button>
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Live Camera */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <MonitorPlay className="w-5 h-5 text-red-400" />
              Chế Độ Quan Sát Live
            </h2>
            <span className="flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
          </div>
          
          <div className="relative group rounded-3xl overflow-hidden bg-zinc-900 border border-white/10 shadow-2xl shadow-blue-900/20 aspect-video flex items-center justify-center">
            {activeStationId ? (
                <>
                {/* API MJPEG LIVE STREAM */}
                <img 
                  key={`camera-stream-${activeStationId}`}
                  src={`${API_BASE}/api/live?station_id=${activeStationId}`} 
                  alt="Không kết nối được Camera" 
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
                {/* Glass Overlay status */}
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
                  </div>
                </div>
                </>
            ) : (
                <div className="text-slate-500 flex flex-col items-center">
                    <Settings className="w-12 h-12 mb-2 opacity-50" />
                    <p>Vui lòng tạo Trạm Đóng Hàng đầu tiên</p>
                    <button onClick={() => requestAdminAccess({ type: 'setup', isNew: true })} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg">Cài đặt ngay</button>
                </div>
            )}
          </div>
          
          <div className="p-5 rounded-2xl bg-white/5 border border-purple-500/30 backdrop-blur-lg mt-2 relative overflow-hidden group">
            <div className="absolute top-0 right-0 bg-purple-500/20 text-purple-300 text-[10px] px-3 py-1 rounded-bl-xl font-mono border-l border-b border-purple-500/20">
              DEV MODE
            </div>
            <h3 className="font-medium text-slate-200 mb-4 flex items-center gap-2">
              <Box className="w-4 h-4 text-purple-400" />
              Công Cụ Giả Lập Máu Quét (Manual Simulator)
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
                       <span className="px-2 py-1 bg-blue-500/20 border border-blue-500/30 text-blue-300 rounded text-[10px] font-bold">
                         Trạm: {record.station_name || 'Mặc định'}
                       </span>
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleDeleteRecord(record.id, record.waybill_code); }}
                      className="p-2 -mr-2 -mt-2 text-slate-500 hover:text-rose-400 hover:bg-rose-400/10 rounded-lg transition-colors"
                      title="Xoá bản ghi lưu trữ dọn ổ đĩa"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <p className="text-xs text-slate-400 mb-4 font-mono">
                    {new Date(record.recorded_at).toLocaleString('vi-VN')}
                  </p>
                  
                  {/* Danh sách các file video lưu trữ */}
                  <div className="space-y-2">
                    {record.video_paths.map((path, idx) => {
                      const fileName = path.split('/').pop() || path.split('\\').pop();
                      const videoUrl = `${API_BASE}/${path}`;
                      return (
                        <div 
                          key={idx}
                          role="button"
                          onClick={() => {
                            setSelectedVideo({ url: videoUrl, waybillCode: record.waybill_code });
                            setVideoModalOpen(true);
                          }}
                          className="flex items-center gap-2 p-2 rounded-lg bg-black/20 hover:bg-black/40 border border-white/5 transition-colors text-sm"
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
    </div>
  );
}

export default App;
