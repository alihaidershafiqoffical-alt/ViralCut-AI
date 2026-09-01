"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import apiClient from "@/lib/axios";

interface UsePollingOptions {
  enabled?: boolean;
  onError?: (error: Error) => void;
}

interface UsePollingResult<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

/**
 * Custom hook that polls a backend endpoint at a given interval.
 *
 * @param url - API endpoint to poll (relative to baseURL)
 * @param intervalMs - Polling interval in milliseconds
 * @param options - Optional configuration (enabled flag, error callback)
 */
export function usePolling<T>(
  url: string,
  intervalMs: number = 3000,
  options: UsePollingOptions = {}
): UsePollingResult<T> {
  const { enabled = true, onError } = options;
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(enabled);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const response = await apiClient.get<T>(url);
      setData(response.data);
      setError(null);
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Unknown error");
      setError(error);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  }, [url, onError]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Initial fetch deferred to next tick
    const initTimer = setTimeout(() => {
      fetchData();
    }, 0);

    // Set up polling interval
    intervalRef.current = setInterval(fetchData, intervalMs);

    return () => {
      clearTimeout(initTimer);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, intervalMs, enabled]);

  return { data, isLoading, error, refresh: fetchData };
}
