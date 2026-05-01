import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import API_BASE from '../config';

import { PackingRecord, User } from '../types/api';

const SEARCH_DEBOUNCE = 300;

export function useRecords({ 
  activeStationId, 
  currentUser, 
  setLoading, 
  fetchAnalytics 
}: { 
  activeStationId: number | null | 'orphaned';
  currentUser: User | null;
  setLoading?: (v: boolean) => void;
  fetchAnalytics?: (id: number | null | 'orphaned') => void;
}) {
  const [records, setRecords] = useState<PackingRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [recordsPage, setRecordsPage] = useState(1);
  const [recordsTotal, setRecordsTotal] = useState(0);
  const [recordsTotalPages, setRecordsTotalPages] = useState(0);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const searchTermRef = useRef(searchTerm);
  useEffect(() => {
    searchTermRef.current = searchTerm;
  }, [searchTerm]);

  const recordsPageRef = useRef(recordsPage);
  useEffect(() => {
    recordsPageRef.current = recordsPage;
  }, [recordsPage]);

  const dateFromRef = useRef(dateFrom);
  useEffect(() => {
    dateFromRef.current = dateFrom;
  }, [dateFrom]);

  const dateToRef = useRef(dateTo);
  useEffect(() => {
    dateToRef.current = dateTo;
  }, [dateTo]);

  const statusFilterRef = useRef(statusFilter);
  useEffect(() => {
    statusFilterRef.current = statusFilter;
  }, [statusFilter]);

  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchRecords = async (query = '', sid = activeStationId, page = 1, signal?: AbortSignal) => {
    try {
      if (setLoading) setLoading(true);
      const params = new URLSearchParams();
      if (query) params.set('search', query);
      if (sid === 'orphaned') {
        params.set('orphaned', 'true');
      } else if (sid !== null) {
        params.set('station_id', String(sid));
      }
      if (page > 1) params.set('page', String(page));
      if (dateFromRef.current) params.set('date_from', dateFromRef.current);
      if (dateToRef.current) params.set('date_to', dateToRef.current);
      if (statusFilterRef.current) params.set('status', statusFilterRef.current);
      params.set('limit', '20');

      const res = await axios.get(`${API_BASE}/api/records?${params.toString()}`, { signal });
      setRecords(res.data.records);
      setRecordsTotal(res.data.total);
      setRecordsTotalPages(res.data.total_pages);
      setRecordsPage(res.data.page);
      if (setLoading) setLoading(false);
      if (fetchAnalytics) fetchAnalytics(sid);
    } catch (err: unknown) {
      if (axios.isCancel(err) || (err as Error).name === 'CanceledError') return;
      if (setLoading) setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser) {
      setRecordsPage(1);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();
      const debounce = setTimeout(() => {
        if (abortControllerRef.current) {
          fetchRecords(searchTerm, activeStationId, 1, abortControllerRef.current.signal);
        }
      }, SEARCH_DEBOUNCE);
      return () => {
        clearTimeout(debounce);
        if (abortControllerRef.current) abortControllerRef.current.abort();
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, activeStationId, currentUser, dateFrom, dateTo, statusFilter]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  return {
    records,
    setRecords,
    searchTerm,
    setSearchTerm,
    recordsPage,
    setRecordsPage,
    recordsTotal,
    recordsTotalPages,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    statusFilter,
    setStatusFilter,
    fetchRecords,
    handleSearch,
    searchTermRef,
    recordsPageRef,
  };
}
