import { useState, useRef, useCallback, useEffect } from 'react';

const TOAST_DURATIONS = { info: 2000, error: 3000, warning: 5000 };

export function useToast() {
  const [toast, setToast] = useState<string | null>(null);
  const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((msg: string, type: 'info' | 'error' | 'warning' = 'info') => {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToast(msg);
    toastTimeoutRef.current = setTimeout(() => setToast(null), TOAST_DURATIONS[type] ?? TOAST_DURATIONS.info);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    };
  }, []);

  return { toast, showToast };
}
