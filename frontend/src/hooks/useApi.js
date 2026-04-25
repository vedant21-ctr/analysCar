import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL, timeout: 30000 });

export function useApi(endpoint, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(endpoint, { params: options.params });
      setData(res.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch data');
      console.error(`API Error [${endpoint}]:`, err);
    } finally {
      setLoading(false);
    }
  }, [endpoint, JSON.stringify(options.params)]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export async function postApi(endpoint, body) {
  const res = await api.post(endpoint, body);
  return res.data;
}

export async function getApi(endpoint, params = {}) {
  const res = await api.get(endpoint, { params });
  return res.data;
}
