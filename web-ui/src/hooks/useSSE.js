import { useEffect } from 'react';
import API_BASE from '../config';
import { playScanStart, playRecordingStop, playVideoReady, playRecordingWarning } from '../utils/notificationSounds';

const RESTART_DELAY = 5000;

export function useSSE({
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
}) {
  useEffect(() => {
    const isGlobalSSE = viewMode === 'grid' || currentUser?.role === 'ADMIN';
    const stationIds = isGlobalSSE ? stationsIdStr : String(activeStationId || '');
    const sseToken = localStorage.getItem('vpack_token');
    const es = new EventSource(
      `${API_BASE}/api/events?stations=${stationIds}${sseToken ? '&token=' + encodeURIComponent(sseToken) : ''}`,
    );

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

    es.onerror = () => {};

    return () => es.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: SSE reconnect controlled by activeStationId/viewMode
  }, [activeStationId, viewMode, stationsIdStr]);
}
