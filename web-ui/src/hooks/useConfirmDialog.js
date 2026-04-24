import { useState, useCallback } from 'react';

export function useConfirmDialog() {
  const [confirmDialog, setConfirmDialog] = useState({ show: false, message: '', onConfirm: null });

  const showConfirmDialog = useCallback((message, onConfirm) => {
    setConfirmDialog({ show: true, message, onConfirm });
  }, []);

  return { confirmDialog, setConfirmDialog, showConfirmDialog };
}
