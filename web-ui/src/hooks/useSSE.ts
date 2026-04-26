import { useEffect, useState, useRef, useCallback } from 'react';
import API_BASE from '../config';
import { playScanStart, playRecordingStop, playVideoReady, playRecordingWarning } from '../utils/notificationSounds';

import { StationStatus } from '../types/props';
import { User, Station } from '../types/api';

const RESTART_DELAY = 5000;

export function useSSE({
  activeStationId,
  viewMode,
  stationsIdStr,
  currentUser,
  stationsRef,
  setStations,
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
  onReconnect,
}: {
  activeStationId: number | null | 'orphaned';
  viewMode: string;
  stationsIdStr: string;
  currentUser: User | null;
  stationsRef: React.MutableRefObject<Station[]>;
  setStations: React.Dispatch<React.SetStateAction<Station[]>>;
  setStationStatuses: React.Dispatch<React.SetStateAction<Record<string, StationStatus>>>;
  setPackingStatus: (status: 'idle' | 'packing') => void;
  setCurrentWaybill: (waybill: string) => void;
  activeRecordIdRef: React.MutableRefObject<number | null>;
  fetchStorageInfo: () => void;
  fetchRecords: (query: string, sid: number | null | 'orphaned', page: number) => void;
  searchTermRef: React.MutableRefObject<string>;
  recordsPageRef: React.MutableRefObject<number>;
  setUpdateProgress: (progress: { percentage: number; status: string } | null) => void;
  showToast: (msg: string, type?: 'info' | 'error' | 'warning') => void;
  onReconnect?: () => void;
}) {
  const [sseStatus, setSseStatus] = useState<'connected' | 'reconnecting' | 'disconnected'>('disconnected');
  const forceReconnectRef = useRef(0);

  const forceReconnect = useCallback(() => {
    forceReconnectRef.current += 1;
    setSseStatus('reconnecting');
  }, []);

  useEffect(() => {
    let es: EventSource | null = null;
    let timeoutId: ReturnType<typeof setTimeout>;
    let isMounted = true;
    let retryCount = 0;

    const connect = (isReconnect: boolean) => {
      if (es) {
        es.close();
      }
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      const isGlobalSSE = viewMode === 'grid' || currentUser?.role === 'ADMIN';
      const stationIds = isGlobalSSE ? stationsIdStr : String(activeStationId || '');
      const sseToken = localStorage.getItem('vpack_token');
      es = new EventSource(
        `${API_BASE}/api/events?stations=${stationIds}${sseToken ? '&token=' + encodeURIComponent(sseToken) : ''}`,
      );

      es.onopen = () => {
        if (!isMounted) return;
        setSseStatus('connected');
        retryCount = 0;
        if (isReconnect && onReconnect) {
          onReconnect();
        }
      };

      es.onerror = () => {
        if (!isMounted) return;
        es?.close();
        es = null;
        retryCount += 1;

        if (retryCount > 10) {
          setSseStatus('disconnected');
          showToast('Không thể kết nối máy chủ. Vui lòng tải lại trang.', 'error');
        } else {
          setSseStatus('reconnecting');
          if (retryCount === 1) {
            showToast('Mất kết nối. Đang tự động thử lại...', 'warning');
          }
          const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 30000);
          timeoutId = setTimeout(() => {
            if (isMounted) connect(true);
          }, delay);
        }
      };

      es.addEventListener('video_status', (evt) => {
        try {
          const data = JSON.parse(evt.data);

          if (isGlobalSSE) {
            const isRecording = data.status === 'RECORDING';
            const waybill = data.waybill || '';
            setStationStatuses((prev) => {
              const current = prev[data.station_id] || { status: 'idle', waybill: '', processingCount: 0 };
              const nextStatus = isRecording
                ? 'packing'
                : data.status === 'PROCESSING' ||
                    data.status === 'READY' ||
                    data.status === 'FAILED' ||
                    data.status === 'DELETED'
                  ? 'idle'
                  : current.status;
              return {
                ...prev,
                [data.station_id]: {
                  status: nextStatus,
                  waybill: isRecording ? waybill : current.waybill,
                  processingCount: data.processing_count !== undefined ? data.processing_count : current.processingCount,
                },
              };
            });
            // Station-specific UI (sounds, packing status) only when viewing that station
            if (data.station_id === activeStationId) {
              if (isRecording) {
                playScanStart();
                setPackingStatus('packing');
                setCurrentWaybill(waybill);
                activeRecordIdRef.current = data.record_id;
              }
              if (data.status === 'PROCESSING') {
                playRecordingStop();
              }
              if (data.status === 'READY') {
                playVideoReady();
              }
              if (
                data.status === 'PROCESSING' ||
                data.status === 'READY' ||
                data.status === 'FAILED' ||
                data.status === 'DELETED'
              ) {
                if (data.record_id === activeRecordIdRef.current) {
                  setPackingStatus('idle');
                  setCurrentWaybill('');
                  activeRecordIdRef.current = null;
                }
              }
            }
            // Always refresh records + storage for admin on any station status change
            if (
              data.status === 'PROCESSING' ||
              data.status === 'READY' ||
              data.status === 'FAILED' ||
              data.status === 'DELETED'
            ) {
              fetchStorageInfo();
            }
            fetchRecords(searchTermRef.current, activeStationId, recordsPageRef.current);
          } else {
            if (data.station_id !== activeStationId) return;

            if (data.status === 'RECORDING') {
              playScanStart();
              setPackingStatus('packing');
              setCurrentWaybill(data.waybill || '');
              activeRecordIdRef.current = data.record_id;
              fetchRecords(searchTermRef.current, activeStationId, recordsPageRef.current);
            } else if (data.status === 'PROCESSING') {
              playRecordingStop();
              if (data.record_id === activeRecordIdRef.current) {
                setPackingStatus('idle');
                setCurrentWaybill('');
                activeRecordIdRef.current = null;
              }
              fetchRecords(searchTermRef.current, activeStationId, recordsPageRef.current);
              fetchStorageInfo();
            } else if (data.status === 'READY') {
              playVideoReady();
              if (data.record_id === activeRecordIdRef.current) {
                setPackingStatus('idle');
                setCurrentWaybill('');
                activeRecordIdRef.current = null;
              }
              fetchRecords(searchTermRef.current, activeStationId, recordsPageRef.current);
              fetchStorageInfo();
            } else if (data.status === 'FAILED' || data.status === 'DELETED') {
              if (data.record_id === activeRecordIdRef.current) {
                setPackingStatus('idle');
                setCurrentWaybill('');
                activeRecordIdRef.current = null;
              }
              fetchRecords(searchTermRef.current, activeStationId, recordsPageRef.current);
              fetchStorageInfo();
            }
          }
        } catch {
          // SSE parse failure - ignore
        }
      });

      es.addEventListener('camera_status', (evt) => {
        try {
          const data = JSON.parse(evt.data);
          setStations((prev) =>
            prev.map((s) =>
              s.id === Number(data.station_id)
                ? { ...s, camera_health: { ...s.camera_health, online: data.online } }
                : s
            )
          );
        } catch {
          // ignore
        }
      });

      es.addEventListener('update_progress', (evt) => {
        try {
          const data = JSON.parse(evt.data);
          setUpdateProgress(data);
          if (data.stage === 'restarting') {
            setTimeout(() => {
              window.location.reload();
            }, RESTART_DELAY);
          }
        } catch {
          // SSE parse failure - ignore
        }
      });

      es.addEventListener('recording_warning', (evt) => {
        try {
          const data = JSON.parse(evt.data);
          const sec = data.remaining_seconds || 60;
          const station = stationsRef.current.find((s) => s.id === data.station_id);
          const name = station ? station.name : '';
          showToast(`⚠️ ${name ? name + ': ' : ''}Tự động dừng sau ${sec}s`, 'warning');
          playRecordingWarning();
        } catch {
          // SSE parse failure - ignore
        }
      });
    };

    connect(false);

    return () => {
      isMounted = false;
      if (es) es.close();
      if (timeoutId) clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeStationId, viewMode, stationsIdStr, forceReconnectRef.current]);

  return { sseStatus, forceReconnect };
}
