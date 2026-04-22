/**
 * V-Pack Monitor - CamDongHang
 * Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
 * All rights reserved. Unauthorized copying or distribution is prohibited.
 */

import React from 'react';
import { MonitorPlay, LayoutGrid } from 'lucide-react';
import MtxFallback from './MtxFallback';

export default function AdminDashboard({
  stations,
  stationStatuses,
  reconnectInfo,
  mtxAvailable,
  isDualCamStation,
  MTX_HOST,
  onStationClick,
}) {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Live Cameras Grid (Luôn hiện cho admin) */}
      <section className="bg-white/5 border border-white/10 rounded-2xl md:rounded-3xl p-4 md:p-6 backdrop-blur-md shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <LayoutGrid className="w-5 h-5 text-blue-400" />
            Live Cameras Toàn Hệ Thống
          </h2>
          <span className="flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        </div>

        {stations.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-16 bg-black/20 border border-white/5 rounded-3xl">
            <MonitorPlay className="w-12 h-12 text-slate-500 mb-3" />
            <p className="text-slate-400">Chưa có trạm nào</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {stations.map((station) => {
              const st = stationStatuses[station.id] || { status: 'idle', waybill: '' };
              const hasCam2 = isDualCamStation(station);

              return (
                <div
                  key={station.id}
                  onClick={() => onStationClick && onStationClick(station.id)}
                  className="relative group rounded-3xl overflow-hidden bg-zinc-900 border border-white/10 shadow-lg aspect-[4/3] md:aspect-video flex items-center justify-center cursor-pointer hover:ring-2 hover:ring-blue-500 transition-all duration-200"
                >
                  {reconnectInfo && reconnectInfo.station_id === station.id && reconnectInfo.status === 'searching' && (
                    <div className="absolute top-2 left-1/2 -translate-x-1/2 z-10 bg-amber-500/90 text-white text-xs font-semibold px-3 py-1 rounded-full animate-pulse">
                      🔄 Tìm lại Camera...
                    </div>
                  )}
                  {reconnectInfo && reconnectInfo.station_id === station.id && reconnectInfo.status === 'found' && (
                    <div className="absolute top-2 left-1/2 -translate-x-1/2 z-10 bg-emerald-500/90 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      ✅ IP mới: {reconnectInfo.new_ip}
                    </div>
                  )}

                  <div className="absolute top-3 left-3 right-3 flex items-start gap-2 pointer-events-none z-10">
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
                    {st.processingCount > 0 && (
                      <div className="px-3 py-1.5 rounded-full bg-amber-600/90 backdrop-blur-md border border-amber-400 text-xs font-bold text-white flex items-center gap-2 animate-pulse shadow-lg">
                        ⚙ {st.processingCount} đang xử lý
                      </div>
                    )}
                  </div>

                  {hasCam2 && (
                    <div className="absolute top-3 right-3 px-2 py-0.5 bg-blue-500/30 border border-blue-400/40 rounded text-[10px] text-blue-200 font-bold pointer-events-none z-10">
                      2 CAM
                    </div>
                  )}

                  {!mtxAvailable ? (
                    <MtxFallback />
                  ) : hasCam2 ? (
                    <div className="flex gap-1 w-full h-full">
                      <div className="flex-1 relative">
                        <iframe
                          key={`live-${station.id}`}
                          src={`http://${MTX_HOST}:8889/station_${station.id}?controls=false&muted=true&autoplay=true`}
                          scrolling="no"
                          className="w-full h-full object-cover"
                          style={{ border: 'none', background: '#000' }}
                          allow="autoplay"
                        />
                        <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-[10px] text-white/80 pointer-events-none">
                          Cam 1
                        </div>
                      </div>
                      <div className="flex-1 relative">
                        <iframe
                          key={`live-cam2-${station.id}`}
                          src={`http://${MTX_HOST}:8889/station_${station.id}_cam2?controls=false&muted=true&autoplay=true`}
                          scrolling="no"
                          className="w-full h-full object-cover"
                          style={{ border: 'none', background: '#000' }}
                          allow="autoplay"
                        />
                        <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-[10px] text-white/80 pointer-events-none">
                          Cam 2
                        </div>
                      </div>
                    </div>
                  ) : (
                    <iframe
                      key={`live-${station.id}`}
                      src={`http://${MTX_HOST}:8889/station_${station.id}?controls=false&muted=true&autoplay=true`}
                      scrolling="no"
                      className="w-full h-full object-cover"
                      style={{ border: 'none', background: '#000' }}
                      allow="autoplay"
                    />
                  )}
                  <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 transition-all duration-300 z-20 cursor-pointer" />
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
