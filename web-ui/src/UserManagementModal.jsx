/**
 * V-Pack Monitor - CamDongHang v2.4.2
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { X, Users, Activity, FileText, Key, Shield, Clock, Filter, UserPlus, Trash2, Lock, Unlock, Edit3, AlertCircle, Search, ChevronDown } from 'lucide-react';
import API_BASE from './config';

const ACTION_LABELS = {
  LOGIN: 'Đăng nhập',
  LOGOUT: 'Đăng xuất',
  START_RECORD: 'Bắt đầu ghi',
  STOP_RECORD: 'Dừng ghi',
  CREATE_USER: 'Tạo user',
  UPDATE_USER: 'Sửa user',
  DELETE_USER: 'Xoá user',
  CHANGE_PASSWORD: 'Đổi mật khẩu',
  LOCK_USER: 'Khoá user',
  UNLOCK_USER: 'Mở khoá user',
  FORCE_LOGOUT: 'Buộc đăng xuất',
  SETTINGS_UPDATE: 'Cập nhật cài đặt',
  STATION_CREATE: 'Tạo trạm',
  STATION_UPDATE: 'Sửa trạm',
  STATION_DELETE: 'Xoá trạm',
};

const timeAgo = (dateStr) => {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return `${seconds} giây trước`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} phút trước`;
  return `${Math.floor(seconds / 3600)} giờ trước`;
};

export default function UserManagementModal({ isOpen, onClose, currentUser }) {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Users tab state
  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState({ username: '', password: '', full_name: '', role: 'OPERATOR' });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ full_name: '', role: '' });
  const [passwordModalId, setPasswordModalId] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState('');

  // Audit log filters
  const [logFilterUser, setLogFilterUser] = useState('');
  const [logFilterAction, setLogFilterAction] = useState('');
  const [logOffset, setLogOffset] = useState(0);
  const [logHasMore, setLogHasMore] = useState(true);

  const logIntervalRef = useRef(null);

  const fetchUsers = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/users`);
      if (res.data.data) setUsers(res.data.data);
    } catch (err) {
      console.error('Fetch users error', err);
    }
  }, []);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/sessions/active`);
      if (res.data.data) setSessions(res.data.data);
    } catch (err) {
      console.error('Fetch sessions error', err);
    }
  }, []);

  const fetchLogs = useCallback(async (offset = 0, append = false) => {
    try {
      setLoading(true);
      const params = new URLSearchParams({ limit: '200', offset: String(offset) });
      if (logFilterUser) params.set('user_id', logFilterUser);
      if (logFilterAction) params.set('action', logFilterAction);
      const res = await axios.get(`${API_BASE}/api/audit-logs?${params}`);
      const data = res.data.data || [];
      if (append) {
        setLogs(prev => [...prev, ...data]);
      } else {
        setLogs(data);
      }
      setLogHasMore(data.length >= 200);
    } catch (err) {
      console.error('Fetch logs error', err);
    } finally {
      setLoading(false);
    }
  }, [logFilterUser, logFilterAction]);

  useEffect(() => {
    if (!isOpen) return;
    if (activeTab === 'users') fetchUsers();
    else if (activeTab === 'sessions') fetchSessions();
    else if (activeTab === 'logs') {
      setLogOffset(0);
      fetchLogs(0, false);
    }
  }, [isOpen, activeTab, fetchUsers, fetchSessions, fetchLogs]);

  // Auto-refresh sessions & logs
  useEffect(() => {
    if (!isOpen) return;
    logIntervalRef.current = setInterval(() => {
      if (activeTab === 'sessions') fetchSessions();
      if (activeTab === 'logs') fetchLogs(0, false);
    }, 30000);
    return () => {
      if (logIntervalRef.current) clearInterval(logIntervalRef.current);
    };
  }, [isOpen, activeTab, fetchSessions, fetchLogs]);

  // Reset form states on close
  useEffect(() => {
    if (!isOpen) {
      setShowAddForm(false);
      setEditingId(null);
      setPasswordModalId(null);
      setError('');
      setPasswordMsg('');
      setLogFilterUser('');
      setLogFilterAction('');
      setLogOffset(0);
    }
  }, [isOpen]);

  // --- Users handlers ---
  const handleAddUser = async () => {
    if (!addForm.username || !addForm.password || !addForm.full_name) {
      setError('Vui lòng điền đầy đủ thông tin.');
      return;
    }
    if (addForm.password.length < 6) {
      setError('Mật khẩu phải có ít nhất 6 ký tự.');
      return;
    }
    try {
      setError('');
      await axios.post(`${API_BASE}/api/users`, addForm);
      setShowAddForm(false);
      setAddForm({ username: '', password: '', full_name: '', role: 'OPERATOR' });
      fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi khi tạo user.');
    }
  };

  const handleDeleteUser = async (user) => {
    if (user.id === currentUser?.id) {
      alert('Không thể xoá tài khoản của chính bạn.');
      return;
    }
    if (window.confirm(`Xoá user "${user.username}"?`)) {
      try {
        await axios.delete(`${API_BASE}/api/users/${user.id}`);
        fetchUsers();
      } catch {
        alert('Lỗi khi xoá user.');
      }
    }
  };

  const handleToggleActive = async (user) => {
    try {
      await axios.put(`${API_BASE}/api/users/${user.id}`, { is_active: user.is_active ? 0 : 1 });
      fetchUsers();
    } catch {
      alert('Lỗi khi cập nhật trạng thái.');
    }
  };

  const handleStartEdit = (user) => {
    setEditingId(user.id);
    setEditForm({ full_name: user.full_name, role: user.role });
  };

  const handleSaveEdit = async (userId) => {
    try {
      await axios.put(`${API_BASE}/api/users/${userId}`, editForm);
      setEditingId(null);
      fetchUsers();
    } catch {
      alert('Lỗi khi cập nhật user.');
    }
  };

  const handleChangePassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      setPasswordMsg('Mật khẩu phải có ít nhất 6 ký tự.');
      return;
    }
    try {
      await axios.put(`${API_BASE}/api/users/${passwordModalId}/password`, {
        password: newPassword
      });
      setPasswordMsg('');
      setPasswordModalId(null);
      setNewPassword('');
      alert('Đổi mật khẩu thành công!');
    } catch {
      setPasswordMsg('Lỗi khi đổi mật khẩu.');
    }
  };

  // --- Sessions handlers ---
  const handleKillSession = async (sessionId, username) => {
    if (window.confirm(`Kết thúc phiên của "${username}"?`)) {
      try {
        await axios.delete(`${API_BASE}/api/sessions/${sessionId}`);
        fetchSessions();
      } catch {
        alert('Lỗi khi kết thúc phiên.');
      }
    }
  };

  // --- Logs handlers ---
  const handleLoadMoreLogs = () => {
    const newOffset = logOffset + 200;
    setLogOffset(newOffset);
    fetchLogs(newOffset, true);
  };

  if (!isOpen) return null;

  const tabs = [
    { key: 'users', label: 'Người Dùng', icon: Users },
    { key: 'sessions', label: 'Phiên Hoạt Động', icon: Activity },
    { key: 'logs', label: 'Nhật Ký Hệ Thống', icon: FileText },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-white/10 rounded-3xl w-full max-w-4xl max-h-[85vh] overflow-hidden shadow-2xl flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-32 bg-emerald-500/10 blur-3xl opacity-50 rounded-full pointer-events-none"></div>

        {/* Header */}
        <div className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-white/10 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/20 rounded-xl border border-emerald-400/30">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Quản Lý Người Dùng</h2>
              <p className="text-xs text-slate-400">Phân quyền & giám sát hệ thống</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="relative z-10 flex gap-1 px-6 pt-3 shrink-0">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-xl transition-all ${
                  isActive
                    ? 'bg-white/10 text-white border-b-2 border-emerald-400'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="relative z-10 overflow-y-auto p-6 flex-1">

          {error && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-xl flex items-center gap-2 text-sm text-red-200">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <p>{error}</p>
            </div>
          )}

          {/* ========== TAB: USERS ========== */}
          {activeTab === 'users' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">{users.length} người dùng</span>
                <button
                  onClick={() => { setShowAddForm(!showAddForm); setError(''); }}
                  className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-sm font-semibold text-white transition-colors"
                >
                  <UserPlus className="w-4 h-4" />
                  Thêm người dùng
                </button>
              </div>

              {/* Add User Form */}
              {showAddForm && (
                <div className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-3">
                  <h4 className="text-sm font-semibold text-emerald-300 uppercase tracking-wider">Tạo User Mới</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      placeholder="Tên đăng nhập"
                      value={addForm.username}
                      onChange={e => setAddForm(f => ({ ...f, username: e.target.value }))}
                      className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
                    />
                    <input
                      type="password"
                      placeholder="Mật khẩu (≥ 6 ký tự)"
                      value={addForm.password}
                      onChange={e => setAddForm(f => ({ ...f, password: e.target.value }))}
                      className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
                    />
                    <input
                      type="text"
                      placeholder="Họ tên"
                      value={addForm.full_name}
                      onChange={e => setAddForm(f => ({ ...f, full_name: e.target.value }))}
                      className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
                    />
                    <select
                      value={addForm.role}
                      onChange={e => setAddForm(f => ({ ...f, role: e.target.value }))}
                      className="bg-[#1e293b] border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500/50 appearance-none"
                    >
                      <option value="OPERATOR">OPERATOR</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                  </div>
                  <div className="flex justify-end gap-2">
                    <button onClick={() => { setShowAddForm(false); setError(''); }} className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-sm text-slate-300 transition-colors">
                      Hủy
                    </button>
                    <button onClick={handleAddUser} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-sm font-semibold text-white transition-colors">
                      Tạo User
                    </button>
                  </div>
                </div>
              )}

              {/* Users Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-white/10">
                      <th className="pb-3 font-medium">Username</th>
                      <th className="pb-3 font-medium">Họ tên</th>
                      <th className="pb-3 font-medium">Vai trò</th>
                      <th className="pb-3 font-medium">Trạng thái</th>
                      <th className="pb-3 font-medium text-right">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {users.map(user => (
                      <tr key={user.id} className="hover:bg-white/5 transition-colors">
                        <td className="py-3 text-slate-200 font-mono">{user.username}</td>
                        <td className="py-3">
                          {editingId === user.id ? (
                            <input
                              type="text"
                              value={editForm.full_name}
                              onChange={e => setEditForm(f => ({ ...f, full_name: e.target.value }))}
                              className="bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500/50 w-full"
                            />
                          ) : (
                            <span className="text-slate-200">{user.full_name}</span>
                          )}
                        </td>
                        <td className="py-3">
                          {editingId === user.id ? (
                            <select
                              value={editForm.role}
                              onChange={e => setEditForm(f => ({ ...f, role: e.target.value }))}
                              className="bg-[#1e293b] border border-white/10 rounded-lg px-2 py-1 text-white text-sm focus:outline-none appearance-none"
                            >
                              <option value="OPERATOR">OPERATOR</option>
                              <option value="ADMIN">ADMIN</option>
                            </select>
                          ) : (
                            <span className={`px-2 py-0.5 rounded text-xs font-bold tracking-wider ${
                              user.role === 'ADMIN'
                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                            }`}>
                              {user.role}
                            </span>
                          )}
                        </td>
                        <td className="py-3">
                          <span className="flex items-center gap-1.5">
                            <span className={`w-2.5 h-2.5 rounded-full ${user.is_active ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50' : 'bg-red-500'}`}></span>
                            <span className={`text-xs ${user.is_active ? 'text-emerald-400' : 'text-red-400'}`}>
                              {user.is_active ? 'Hoạt động' : 'Bị khoá'}
                            </span>
                          </span>
                        </td>
                        <td className="py-3">
                          <div className="flex items-center justify-end gap-1">
                            {editingId === user.id ? (
                              <>
                                <button onClick={() => handleSaveEdit(user.id)} className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-xs font-semibold text-white transition-colors">
                                  Lưu
                                </button>
                                <button onClick={() => setEditingId(null)} className="px-3 py-1 bg-white/5 hover:bg-white/10 rounded-lg text-xs text-slate-300 transition-colors">
                                  Hủy
                                </button>
                              </>
                            ) : (
                              <>
                                <button onClick={() => handleStartEdit(user)} className="p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-blue-400 transition" title="Sửa">
                                  <Edit3 className="w-4 h-4" />
                                </button>
                                <button onClick={() => { setPasswordModalId(user.id); setNewPassword(''); setPasswordMsg(''); }} className="p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-amber-400 transition" title="Đổi mật khẩu">
                                  <Key className="w-4 h-4" />
                                </button>
                                <button onClick={() => handleToggleActive(user)} className="p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-orange-400 transition" title={user.is_active ? 'Khoá' : 'Mở khoá'}>
                                  {user.is_active ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                                </button>
                                <button onClick={() => handleDeleteUser(user)} className="p-1.5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-red-400 transition" title="Xoá">
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {users.length === 0 && (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-500">Chưa có user nào</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Change Password Mini-Modal */}
              {passwordModalId && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setPasswordModalId(null)}>
                  <div className="bg-slate-900 border border-white/10 rounded-2xl p-5 w-full max-w-sm shadow-2xl" onClick={e => e.stopPropagation()}>
                    <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                      <Key className="w-4 h-4 text-amber-400" />
                      Đổi Mật Khẩu
                    </h4>
                    <input
                      type="password"
                      placeholder="Mật khẩu mới (≥ 6 ký tự)"
                      value={newPassword}
                      onChange={e => { setNewPassword(e.target.value); setPasswordMsg(''); }}
                      className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-amber-500/50 mb-2"
                      autoFocus
                      onKeyDown={e => { if (e.key === 'Enter') handleChangePassword(); }}
                    />
                    {passwordMsg && <p className="text-xs text-red-300 mb-2">{passwordMsg}</p>}
                    <div className="flex justify-end gap-2 mt-3">
                      <button onClick={() => setPasswordModalId(null)} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-slate-300 transition-colors">
                        Hủy
                      </button>
                      <button onClick={handleChangePassword} className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 rounded-lg text-sm font-semibold text-white transition-colors">
                        Đổi mật khẩu
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ========== TAB: SESSIONS ========== */}
          {activeTab === 'sessions' && (
            <div className="space-y-4">
              <span className="text-sm text-slate-400">{sessions.length} phiên hoạt động</span>

              {sessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 bg-white/5 border border-white/10 rounded-2xl">
                  <Activity className="w-12 h-12 text-slate-500 mb-3" />
                  <p className="text-slate-400">Không có phiên hoạt động nào</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-400 border-b border-white/10">
                        <th className="pb-3 font-medium">Người dùng</th>
                        <th className="pb-3 font-medium">Trạm</th>
                        <th className="pb-3 font-medium">Bắt đầu</th>
                        <th className="pb-3 font-medium">Hoạt động cuối</th>
                        <th className="pb-3 font-medium text-right">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {sessions.map(session => (
                        <tr key={session.id} className="hover:bg-white/5 transition-colors">
                          <td className="py-3">
                            <span className="text-slate-200 font-medium">{session.full_name || session.username}</span>
                          </td>
                          <td className="py-3">
                            <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-500/30 text-blue-300 rounded text-xs font-bold">
                              {session.station_name || '—'}
                            </span>
                          </td>
                          <td className="py-3 text-slate-300 text-xs">
                            {new Date(session.started_at).toLocaleString('vi-VN')}
                          </td>
                          <td className="py-3 text-slate-400 text-xs">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {session.last_heartbeat ? timeAgo(session.last_heartbeat) : '—'}
                            </span>
                          </td>
                          <td className="py-3 text-right">
                            <button
                              onClick={() => handleKillSession(session.id, session.full_name || session.username)}
                              className="px-3 py-1 bg-red-500/20 hover:bg-red-500/40 border border-red-500/30 text-red-300 rounded-lg text-xs font-semibold transition-colors"
                            >
                              Kết thúc
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ========== TAB: AUDIT LOGS ========== */}
          {activeTab === 'logs' && (
            <div className="space-y-4">
              {/* Filter bar */}
              <div className="flex flex-wrap items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-xl">
                <Filter className="w-4 h-4 text-slate-400" />
                <select
                  value={logFilterUser}
                  onChange={e => { setLogFilterUser(e.target.value); setLogOffset(0); }}
                  className="bg-[#1e293b] border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none appearance-none"
                >
                  <option value="">Tất cả người dùng</option>
                  {users.map(u => (
                    <option key={u.id} value={u.id}>{u.full_name || u.username}</option>
                  ))}
                </select>
                <select
                  value={logFilterAction}
                  onChange={e => { setLogFilterAction(e.target.value); setLogOffset(0); }}
                  className="bg-[#1e293b] border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none appearance-none"
                >
                  <option value="">Tất cả hành động</option>
                  {Object.entries(ACTION_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
                <span className="text-xs text-slate-500">{logs.length} bản ghi</span>
              </div>

              {/* Logs Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-white/10">
                      <th className="pb-3 font-medium">Thời gian</th>
                      <th className="pb-3 font-medium">Người dùng</th>
                      <th className="pb-3 font-medium">Hành động</th>
                      <th className="pb-3 font-medium">Chi tiết</th>
                      <th className="pb-3 font-medium">Trạm</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {logs.map(log => (
                      <tr key={log.id} className="hover:bg-white/5 transition-colors">
                        <td className="py-2.5 text-slate-400 text-xs whitespace-nowrap">
                          {new Date(log.created_at).toLocaleString('vi-VN')}
                        </td>
                        <td className="py-2.5 text-slate-200 text-xs">
                          {log.username}
                        </td>
                        <td className="py-2.5">
                          <span className="px-2 py-0.5 bg-blue-500/15 border border-blue-500/25 text-blue-300 rounded text-xs font-medium">
                            {ACTION_LABELS[log.action] || log.action}
                          </span>
                        </td>
                        <td className="py-2.5 text-slate-400 text-xs max-w-[200px] truncate">
                          {log.details || '—'}
                        </td>
                        <td className="py-2.5 text-slate-400 text-xs">
                          {log.station_id || '—'}
                        </td>
                      </tr>
                    ))}
                    {logs.length === 0 && !loading && (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-500">Không có nhật ký nào</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Load More */}
              {loading && (
                <div className="flex justify-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              )}
              {logHasMore && !loading && logs.length > 0 && (
                <div className="flex justify-center">
                  <button
                    onClick={handleLoadMoreLogs}
                    className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-slate-300 transition-colors"
                  >
                    Tải thêm
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
