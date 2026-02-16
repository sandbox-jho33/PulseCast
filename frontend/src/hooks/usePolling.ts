import { useEffect, useRef } from 'react';

export function usePolling(
  callback: () => void,
  delay: number | null,
  enabled: boolean = true
) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled || delay === null) return;

    const tick = () => savedCallback.current();

    const id = setInterval(tick, delay);
    return () => clearInterval(id);
  }, [delay, enabled]);
}