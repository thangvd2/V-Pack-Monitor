import { useEffect } from 'react';
import axios from 'axios';
import API_BASE from '../config';
import { playRecordingWarning } from '../utils/notificationSounds';

import { User } from '../types/api';

const BARCODE_TIMEOUT = 100;

export function useBarcodeScanner({
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
}: {
  currentUser: User | null;
  activeStationId: number | null | 'orphaned';
  searchTerm: string;
  packingStatusRef: React.MutableRefObject<string>;
  showToast: (msg: string, type?: 'info' | 'error' | 'warning') => void;
  fetchRecords: (query: string, sid: number | null | 'orphaned', page: number) => void;
  recordsPageRef: React.MutableRefObject<number>;
  setPackingStatus: (status: 'idle' | 'packing') => void;
  setCurrentWaybill: (waybill: string) => void;
  activeRecordIdRef: React.MutableRefObject<number | null>;
}) {
  const sendScanAction = async (finalBarcode: string) => {
    if (!activeStationId) return;
    try {
      const res = await axios.post(`${API_BASE}/api/scan`, {
        barcode: finalBarcode,
        station_id: activeStationId,
      });
      if (res.data.status === 'recording') {
        if (res.data.record_id) {
          activeRecordIdRef.current = res.data.record_id;
          setPackingStatus('packing');
          setCurrentWaybill(finalBarcode);
        } else {
          showToast(res.data.message || 'Đang ghi đơn. Quét STOP trước khi quét mã mới.', 'warning');
          playRecordingWarning();
        }
      } else if (res.data.status === 'error') {
        if (res.data.message) {
          showToast(res.data.message, 'error');
        }
        setPackingStatus('idle');
        setCurrentWaybill('');
        fetchRecords(searchTerm, activeStationId, recordsPageRef.current);
      } else if (res.data.status === 'processing') {
        setPackingStatus('idle');
        setCurrentWaybill('');
        fetchRecords(searchTerm, activeStationId, recordsPageRef.current);
      }
    } catch {
      showToast('Lỗi quét mã vạch.', 'error');
    }
  };

  useEffect(() => {
    if (currentUser?.role === 'ADMIN') return;

    let barcodeBuffer = '';
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const handleKeyDown = async (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        const finalBarcode = barcodeBuffer.trim();
        barcodeBuffer = '';

        if (finalBarcode.length > 0) {
          if (packingStatusRef.current === 'packing' && finalBarcode !== 'STOP' && finalBarcode !== 'EXIT') {
            showToast('Đang ghi đơn. Quét STOP trước khi quét mã mới.', 'warning');
            playRecordingWarning();
          } else {
            await sendScanAction(finalBarcode);
          }
        }
      } else {
        if (e.key.length === 1) {
          barcodeBuffer += e.key;
        }

        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          barcodeBuffer = '';
        }, BARCODE_TIMEOUT);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      if (timeoutId) clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, activeStationId, currentUser]);

  return { sendScanAction };
}
