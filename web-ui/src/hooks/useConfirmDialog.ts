import { useState, useCallback } from 'react';

export function useConfirmDialog() {
  const [confirmDialog, setConfirmDialog] = useState<{ show: boolean; message: string; onConfirm: (() => void) | null }>({ show: false, message: '', onConfirm: null });

  const showConfirmDialog = useCallback((message: string, onConfirm: () => void) => {
    setConfirmDialog({ show: true, message, onConfirm });
  }, []);

  return { confirmDialog, setConfirmDialog, showConfirmDialog };
}
