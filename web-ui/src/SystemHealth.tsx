/**
 * V-Pack Monitor - CamDongHang
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Monitor, HardDrive, Clock, Activity, Wifi, Cpu, Server } from 'lucide-react';
import API_BASE from './config';

import { SystemHealthProps } from './types/props';

export interface HealthData {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  cpu_temp?: number;
  db_size_mb: number;
  uptime_str: string;
  uptime?: string;
  cpu?: { percent: number; count?: number; status: 'ok' | 'warning' | 'critical' };
  memory?: { percent: number; used_gb: number; total_gb: number; status: 'ok' | 'warning' | 'critical' };
  disk?: { percent: number; used_gb: number; total_gb: number; status: 'ok' | 'warning' | 'critical' };
  db?: { size_mb: string | number; status: 'ok' | 'warning' | 'critical' };
}

export interface FfmpegProcess {
  pid: number;
  cmdline_short: string;
  cpu_percent: number;
  memory_percent: number;
}

export interface ProcessData {
  cpu_percent: number;
  memory_mb: number;
  threads: number;
  open_files: number;
  ffmpeg_count: number;
  ffmpeg_processes: FfmpegProcess[];
}

export interface CameraData {
  station_id: number;
  station_name: string;
  ip: string;
  reachable: boolean;
}

export interface NetworkData {
  bytes_sent: number;
  bytes_recv: number;
  hostname: string;
  local_ip: string;
  cameras: CameraData[];
}

const STATUS_CONFIG = {
  ok: { color: '#34d399', bar: 'bg-emerald-500', dot: '🟢', label: 'Bình thường' },
  warning: { color: '#fbbf24', bar: 'bg-amber-500', dot: '🟡', label: 'Cảnh báo' },
  critical: { color: '#f87171', bar: 'bg-red-500', dot: '🔴', label: 'Nguy hiểm' },
};

interface StatusCardProps {
  title: string;
  icon: React.ElementType;
  value: string;
  subtitle?: string;
  status: 'ok' | 'warning' | 'critical';
  percent?: number;
}

const StatusCard: React.FC<StatusCardProps> = ({ title, icon: Icon, value, subtitle, status, percent }) => {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.ok;
  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-slate-400" />
          <span className="text-sm font-medium text-slate-300">{title}</span>
        </div>
        <span className="text-xs">
          {cfg.dot} <span style={{ color: cfg.color }}>{cfg.label}</span>
        </span>
      </div>
      <div className="text-3xl font-bold text-white tracking-tight">{value}</div>
      {subtitle && <div className="text-sm text-slate-400 mt-1">{subtitle}</div>}
      {percent !== undefined && (
        <div className="w-full bg-black/30 rounded-full h-2 mt-3">
          <div
            className="h-2 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(percent, 100)}%`, background: cfg.color }}
          />
        </div>
      )}
    </div>
  );
};

const SystemHealth: React.FC<SystemHealthProps> = ({ currentUser: _currentUser }) => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [processes, setProcesses] = useState<ProcessData | null>(null);
  const [network, setNetwork] = useState<NetworkData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [healthRes, procRes, netRes] = await Promise.allSettled([
        axios.get(`${API_BASE}/api/system/health`),
        axios.get(`${API_BASE}/api/system/processes`),
        axios.get(`${API_BASE}/api/system/network-info`),
      ]);

      if (healthRes.status === 'fulfilled') setHealth(healthRes.value.data);
      if (procRes.status === 'fulfilled') setProcesses(procRes.value.data);
      if (netRes.status === 'fulfilled') setNetwork(netRes.value.data);
      setError(null);
    } catch {
      setError('Không thể tải dữ liệu hệ thống');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-slate-400 text-sm">Đang tải dữ liệu hệ thống...</span>
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center">
          <Activity className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-slate-300 font-medium">{error}</p>
          <button
            onClick={fetchData}
            className="mt-4 px-4 py-2 bg-amber-500/20 text-amber-400 rounded-xl text-sm hover:bg-amber-500/30 transition-colors"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  const cpu = health?.cpu || { percent: 0, count: 0, status: 'ok' };
  const memory = health?.memory || { total_gb: 0, used_gb: 0, percent: 0, status: 'ok' };
  const disk = health?.disk || { total_gb: 0, used_gb: 0, percent: 0, status: 'ok' };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded-xl">
          <Activity className="w-6 h-6 text-amber-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Sức Khỏe Hệ Thống</h2>
          <p className="text-sm text-slate-400">Giám sát tài nguyên và tiến trình theo thời gian thực</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusCard
          title="CPU"
          icon={Monitor}
          value={`${cpu.percent}%`}
          subtitle={`${cpu.count} lõi`}
          status={cpu.status}
          percent={cpu.percent}
        />
        <StatusCard
          title="Bộ Nhớ RAM"
          icon={HardDrive}
          value={`${memory.used_gb} / ${memory.total_gb} GB`}
          subtitle={`${memory.percent}% đã sử dụng`}
          status={memory.status}
          percent={memory.percent}
        />
        <StatusCard
          title="Ổ Đĩa"
          icon={HardDrive}
          value={`${disk.used_gb} / ${disk.total_gb} GB`}
          subtitle={`${disk.percent}% đã sử dụng`}
          status={disk.status}
          percent={disk.percent}
        />
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-4">
          <Server className="w-5 h-5 text-amber-400" />
          <h3 className="font-semibold text-slate-200">Thông Tin Máy Chủ</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center gap-3 bg-black/20 rounded-xl p-3 border border-white/5">
            <Clock className="w-5 h-5 text-emerald-400" />
            <div>
              <div className="text-xs text-slate-400">Thời gian hoạt động</div>
              <div className="text-sm font-semibold text-white">{health?.uptime || '—'}</div>
            </div>
          </div>
          <div className="flex items-center gap-3 bg-black/20 rounded-xl p-3 border border-white/5">
            <Wifi className="w-5 h-5 text-blue-400" />
            <div>
              <div className="text-xs text-slate-400">Tên máy chủ</div>
              <div className="text-sm font-semibold text-white">{network?.hostname || '—'}</div>
            </div>
          </div>
          <div className="flex items-center gap-3 bg-black/20 rounded-xl p-3 border border-white/5">
            <Cpu className="w-5 h-5 text-purple-400" />
            <div>
              <div className="text-xs text-slate-400">Địa chỉ IP</div>
              <div className="text-sm font-semibold text-white">{network?.local_ip || '—'}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Monitor className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-slate-200">Tiến Trình FFmpeg</h3>
          </div>
          {(processes?.ffmpeg_count ?? 0) > 0 && (
            <span className="px-3 py-1 bg-blue-500/15 text-blue-400 rounded-full text-xs font-medium border border-blue-500/20">
              {processes?.ffmpeg_count} tiến trình
            </span>
          )}
        </div>
        {(processes?.ffmpeg_processes?.length ?? 0) > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-2 px-3 text-slate-400 font-medium">PID</th>
                  <th className="text-left py-2 px-3 text-slate-400 font-medium">Lệnh</th>
                  <th className="text-right py-2 px-3 text-slate-400 font-medium">CPU%</th>
                  <th className="text-right py-2 px-3 text-slate-400 font-medium">RAM%</th>
                </tr>
              </thead>
              <tbody>
                {processes?.ffmpeg_processes?.map((proc, idx: number) => (
                  <tr key={proc.pid || idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-2.5 px-3 text-slate-300 font-mono text-xs">{proc.pid}</td>
                    <td className="py-2.5 px-3 text-slate-300 max-w-xs truncate" title={proc.cmdline_short}>
                      {proc.cmdline_short || '—'}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-300">{proc.cpu_percent?.toFixed(1) || '0.0'}%</td>
                    <td className="py-2.5 px-3 text-right text-slate-300">
                      {proc.memory_percent?.toFixed(1) || '0.0'}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400 text-sm">
            <Monitor className="w-8 h-8 mx-auto mb-2 text-slate-500" />
            Không có FFmpeg nào đang chạy
          </div>
        )}
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-4">
          <Wifi className="w-5 h-5 text-emerald-400" />
          <h3 className="font-semibold text-slate-200">Trạng Thái Camera</h3>
        </div>
        {(network?.cameras?.length ?? 0) > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-2 px-3 text-slate-400 font-medium">Trạm</th>
                  <th className="text-left py-2 px-3 text-slate-400 font-medium">Địa chỉ IP</th>
                  <th className="text-left py-2 px-3 text-slate-400 font-medium">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {network?.cameras?.map((cam, idx: number) => (
                  <tr
                    key={cam.station_id || idx}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="py-2.5 px-3 text-slate-300">{cam.station_name || `Trạm ${cam.station_id}`}</td>
                    <td className="py-2.5 px-3 text-slate-300 font-mono text-xs">{cam.ip || '—'}</td>
                    <td className="py-2.5 px-3">
                      <span className="flex items-center gap-1.5">
                        <span
                          className={`inline-block w-2 h-2 rounded-full ${cam.reachable ? 'bg-emerald-400' : 'bg-red-400'}`}
                        />
                        <span className={cam.reachable ? 'text-emerald-400' : 'text-red-400'}>
                          {cam.reachable ? 'Kết nối' : 'Mất kết nối'}
                        </span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400 text-sm">
            <Wifi className="w-8 h-8 mx-auto mb-2 text-slate-500" />
            Chưa có thông tin camera
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemHealth;
