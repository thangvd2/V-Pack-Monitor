import { useEffect } from 'react';
import axios from 'axios';
import API_BASE from '../config';
import { playRecordingWarning } from '../utils/notificationSounds';

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
}) {
  const sendScanAction = async (finalBarcode) => {
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
