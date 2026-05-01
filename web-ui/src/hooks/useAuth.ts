import { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE from '../config';

import { User } from '../types/api';

export function useAuth({ 
  onLoginAdmin, 
  onRequirePasswordChange, 
  onLogoutAction 
}: { 
  onLoginAdmin?: () => void;
  onRequirePasswordChange?: () => void;
  onLogoutAction?: () => Promise<void> | void;
}) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [loginError, setLoginError] = useState('');
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });

  useEffect(() => {
    const token = localStorage.getItem('vpack_token');
    const savedUser = localStorage.getItem('vpack_user');
    if (token && savedUser) {
      try {
        const user = JSON.parse(savedUser);
        setCurrentUser(user);
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        if (user.role === 'ADMIN' && onLoginAdmin) {
          onLoginAdmin();
        }
        if (user.must_change_password && onRequirePasswordChange) {
          onRequirePasswordChange();
        }
      } catch {
        localStorage.removeItem('vpack_token');
        localStorage.removeItem('vpack_user');
      }
    }
    setAuthLoading(false);
    axios.defaults.timeout = 15000;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('vpack_token');
          localStorage.removeItem('vpack_user');
          setCurrentUser(null);
          delete axios.defaults.headers.common['Authorization'];
        }
        return Promise.reject(error);
      },
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    try {
      const res = await axios.post(`${API_BASE}/api/auth/login`, loginForm);
      if (res.data.status === 'success') {
        const { access_token, user } = res.data;
        localStorage.setItem('vpack_token', access_token);
        localStorage.setItem('vpack_user', JSON.stringify(user));
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        setCurrentUser(user);
        if (user.role === 'ADMIN' && onLoginAdmin) {
          onLoginAdmin();
        }
        if (user.must_change_password && onRequirePasswordChange) {
          onRequirePasswordChange();
        }
        setLoginForm({ username: '', password: '' });
      } else {
        setLoginError(res.data.message || 'Đăng nhập thất bại.');
      }
    } catch {
      setLoginError('Lỗi kết nối server.');
    }
  };

  const handleLogout = async () => {
    if (onLogoutAction) {
      await onLogoutAction();
    }
    localStorage.removeItem('vpack_token');
    localStorage.removeItem('vpack_user');
    delete axios.defaults.headers.common['Authorization'];
    setCurrentUser(null);
  };

  return {
    currentUser,
    setCurrentUser,
    authLoading,
    loginError,
    loginForm,
    setLoginForm,
    handleLogin,
    handleLogout,
  };
}
