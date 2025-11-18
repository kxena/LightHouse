// frontend/src/hooks/useAutoUpdate.ts
import { useState, useEffect, useCallback } from 'react';

interface TimestampResponse {
  last_update: string | null;
  next_update: string | null;
  has_data: boolean;
}

interface UseAutoUpdateOptions {
  pollInterval?: number;    // How often to check (ms)
  onUpdate?: () => void;    // Callback when new data is detected
  enabled?: boolean;        // Enable or disable polling
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function useAutoUpdate(options: UseAutoUpdateOptions = {}) {
  const {
    pollInterval = 60000, // 1 minute default
    onUpdate,
    enabled = true,
  } = options;

  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [nextUpdate, setNextUpdate] = useState<string | null>(null);
  const [hasNewData, setHasNewData] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  const checkForUpdates = useCallback(async () => {
    if (!enabled) return;

    setIsChecking(true);
    try {
      const res = await fetch(`${API_BASE}/timestamp`, { 
        cache: 'no-store' 
      });
      if (!res.ok) {
        console.warn('Timestamp fetch failed:', res.status);
        setIsChecking(false);
        return;
      }

      const data: TimestampResponse = await res.json();
      
      // Check if data has been updated
      if (data.last_update && data.last_update !== lastUpdate) {
        console.log('🔔 New data detected!', {
          old: lastUpdate,
          new: data.last_update
        });
        setHasNewData(true);
        setLastUpdate(data.last_update);
        
        if (onUpdate) {
          onUpdate();
        }
      } else if (!lastUpdate && data.last_update) {
        // Initial load
        setLastUpdate(data.last_update);
      }
      
      setNextUpdate(data.next_update);
    } catch (err) {
      console.error('Timestamp check failed:', err);
    } finally {
      setIsChecking(false);
    }
  }, [enabled, lastUpdate, onUpdate]);

  // Initial fetch
  useEffect(() => {
    checkForUpdates();
  }, [checkForUpdates]);

  // Polling loop
  useEffect(() => {
    if (!enabled) return;

    const id = setInterval(() => {
      checkForUpdates();
    }, pollInterval);

    return () => clearInterval(id);
  }, [enabled, pollInterval, checkForUpdates]);

  return {
    lastUpdate,
    nextUpdate,
    hasNewData,
    isChecking,
  };
}