/**
 * V-Pack Monitor - CamDongHang v3.3.0
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart3,
  HardDrive,
  Download,
  TrendingUp,
  Clock,
  PieChart as PieChartIcon,
  Calendar,
  Activity,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

import SystemHealth from './SystemHealth';
import API_BASE from './config';

const CHART_COLORS = ['#60a5fa', '#34d399', '#fbbf24', '#c084fc', '#fb7185', '#38bdf8', '#a3e635'];

const CustomTooltipStyle = {
  backgroundColor: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '12px',
  padding: '10px 14px',
  color: '#e2e8f0',
  fontSize: '13px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
};

function StatCard({ label, value, subValue, subLabel, icon: Icon, gradient }) {
  return (
    <div className={`relative overflow-hidden rounded-2xl p-5 border border-white/10 ${gradient}`}>
      <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-white/5 -translate-y-8 translate-x-8" />
      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-3">
          <Icon className="w-5 h-5 text-white/80" />
          <span className="text-sm font-medium text-white/70">{label}</span>
        </div>
        <div className="text-3xl font-bold text-white tracking-tight">{value}</div>
        {subValue !== undefined && (
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-lg font-semibold text-white/90">{subValue}</span>
            <span className="text-xs text-white/50">{subLabel}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function ChartCard({ title, icon: Icon, children, controls }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-slate-200">{title}</h3>
        </div>
        {controls}
      </div>
      {children}
    </div>
  );
}

export default function Dashboard({ stations, activeStationId, storageInfo, currentUser, analytics }) {
  const [hourlyData, setHourlyData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [stationsComparison, setStationsComparison] = useState([]);
  const [loading, setLoading] = useState({ hourly: true, trend: true, comparison: true });
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedStation, setSelectedStation] = useState('all');

  const [dashTab, setDashTab] = useState('analytics');

  const todayAnalytics = analytics || { total_today: 0, station_today: 0 };

  const fetchHourly = useCallback(async () => {
    setLoading((prev) => ({ ...prev, hourly: true }));
    try {
      const stationParam = selectedStation === 'all' ? '' : `&station_id=${selectedStation}`;
      const res = await axios.get(`${API_BASE}/api/analytics/hourly?date=${selectedDate}${stationParam}`);
      setHourlyData(res.data?.data || []);
    } catch {
      setHourlyData([]);
    } finally {
      setLoading((prev) => ({ ...prev, hourly: false }));
    }
  }, [selectedDate, selectedStation]);

  const fetchTrend = useCallback(async () => {
    setLoading((prev) => ({ ...prev, trend: true }));
    try {
      const res = await axios.get(`${API_BASE}/api/analytics/trend?days=7`);
      setTrendData(
        (res.data?.data || []).map((d) => ({
          ...d,
          date: d.date ? d.date.slice(5) : d.date,
        })),
      );
    } catch {
      setTrendData([]);
    } finally {
      setLoading((prev) => ({ ...prev, trend: false }));
    }
  }, []);

  const fetchStationsComparison = useCallback(async () => {
    setLoading((prev) => ({ ...prev, comparison: true }));
    try {
      const res = await axios.get(`${API_BASE}/api/analytics/stations-comparison`);
      setStationsComparison(res.data?.data || []);
    } catch {
      setStationsComparison([]);
    } finally {
      setLoading((prev) => ({ ...prev, comparison: false }));
    }
  }, []);

  useEffect(() => {
    fetchHourly();
  }, [fetchHourly]);
  useEffect(() => {
    fetchTrend();
  }, [fetchTrend]);
  useEffect(() => {
    fetchStationsComparison();
  }, [fetchStationsComparison]);

  const handleExportCSV = async () => {
    try {
      const params = new URLSearchParams();
      params.set('date', selectedDate);
      if (selectedStation !== 'all') params.set('station_id', selectedStation);
      const res = await axios.get(`${API_BASE}/api/export/csv?${params.toString()}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vpack_export_${selectedDate}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export CSV failed:', err);
    }
  };

  const stationSelect = (
    <div className="flex items-center gap-2">
      <select
        value={selectedStation}
        onChange={(e) => setSelectedStation(e.target.value)}
        className="bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer"
      >
        <option value="all" className="bg-slate-800">
          Tất cả trạm
        </option>
        {stations.map((s) => (
          <option key={s.id} value={s.id} className="bg-slate-800">
            {s.name}
          </option>
        ))}
      </select>
      <input
        type="date"
        value={selectedDate}
        onChange={(e) => setSelectedDate(e.target.value)}
        className="bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500/50"
      />
    </div>
  );

  const activeStationName = stations.find((s) => s.id === activeStationId)?.name || 'Trạm hiện tại';

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        <button
          onClick={() => setDashTab('analytics')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${dashTab === 'analytics' ? 'bg-blue-500/20 border border-blue-500/50 text-blue-300' : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10'}`}
        >
          <BarChart3 className="w-4 h-4" />
          Thống kê
        </button>
        {currentUser?.role === 'ADMIN' && (
          <button
            onClick={() => setDashTab('health')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${dashTab === 'health' ? 'bg-amber-500/20 border border-amber-500/50 text-amber-300' : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10'}`}
          >
            <Activity className="w-4 h-4" />
            Sức khỏe hệ thống
          </button>
        )}
      </div>

      {dashTab === 'health' ? (
        <SystemHealth currentUser={currentUser} />
      ) : (
        <>
          <div className="flex flex-col lg:flex-row gap-4 items-stretch">
            <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <StatCard
                label="Tổng Đơn Hôm Nay"
                value={`${todayAnalytics.total_today}`}
                subValue={`${todayAnalytics.station_today}`}
                subLabel={activeStationName}
                icon={BarChart3}
                gradient="bg-gradient-to-br from-blue-600/20 to-emerald-600/20"
              />
              <StatCard
                label="Lưu Trữ"
                value={storageInfo?.size_str || '0 MB'}
                subValue={`${storageInfo?.file_count || 0}`}
                subLabel="tệp tin"
                icon={HardDrive}
                gradient="bg-gradient-to-br from-slate-700/40 to-slate-600/20"
              />
              <button
                onClick={handleExportCSV}
                className="flex items-center justify-center gap-3 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-emerald-500/30 rounded-2xl p-5 transition-all group"
              >
                <Download className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
                <div className="flex flex-col items-start">
                  <span className="text-sm font-medium text-slate-200">Xuất CSV</span>
                  <span className="text-xs text-slate-400">Tải dữ liệu {selectedDate}</span>
                </div>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title="Sản Xuất Theo Giờ" icon={Clock} controls={stationSelect}>
              {loading.hourly ? (
                <div className="h-[280px] flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500" />
                </div>
              ) : hourlyData.length === 0 ? (
                <div className="h-[280px] flex items-center justify-center text-slate-500 text-sm">
                  Không có dữ liệu
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={hourlyData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="hour"
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      axisLine={{ stroke: '#334155' }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      axisLine={{ stroke: '#334155' }}
                      tickLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={CustomTooltipStyle}
                      formatter={(value) => [`${value} đơn`, 'Số lượng']}
                      labelFormatter={(label) => `Giờ ${label}:00`}
                      cursor={{ fill: 'rgba(96, 165, 250, 0.08)' }}
                    />
                    <Bar dataKey="count" fill="#60a5fa" radius={[6, 6, 0, 0]} maxBarSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Xu Hướng 7 Ngày" icon={TrendingUp}>
              {loading.trend ? (
                <div className="h-[280px] flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-emerald-500" />
                </div>
              ) : trendData.length === 0 ? (
                <div className="h-[280px] flex items-center justify-center text-slate-500 text-sm">
                  Không có dữ liệu
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={trendData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      axisLine={{ stroke: '#334155' }}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      axisLine={{ stroke: '#334155' }}
                      tickLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip contentStyle={CustomTooltipStyle} formatter={(value) => [`${value} đơn`, 'Số lượng']} />
                    <Line
                      type="monotone"
                      dataKey="count"
                      stroke="#34d399"
                      strokeWidth={2.5}
                      dot={{ fill: '#34d399', r: 4, strokeWidth: 0 }}
                      activeDot={{ r: 6, fill: '#34d399', stroke: '#fff', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
          </div>

          <ChartCard title="So Sánh Trạm" icon={PieChartIcon}>
            {loading.comparison ? (
              <div className="h-[300px] flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500" />
              </div>
            ) : stationsComparison.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center text-slate-500 text-sm">Không có dữ liệu</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={stationsComparison}
                    dataKey="count"
                    nameKey="station_name"
                    cx="50%"
                    cy="50%"
                    outerRadius={110}
                    innerRadius={55}
                    paddingAngle={3}
                    label={({ station_name, count }) => `${station_name}: ${count}`}
                    labelLine={{ stroke: '#475569', strokeWidth: 1 }}
                  >
                    {stationsComparison.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={CustomTooltipStyle} formatter={(value, name) => [`${value} đơn`, name]} />
                  <Legend formatter={(value) => <span style={{ color: '#94a3b8', fontSize: '13px' }}>{value}</span>} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </>
      )}
    </div>
  );
}
