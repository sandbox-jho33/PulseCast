import { useRef, useState, useEffect, useCallback } from 'react';
import { motion } from 'motion/react';
import WaveSurfer from 'wavesurfer.js';

interface AudioPlayerProps {
  audioUrl?: string;
  durationSeconds?: number;
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function AudioPlayer({ audioUrl, durationSeconds }: AudioPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const nativeAudioRef = useRef<HTMLAudioElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const destroyedRef = useRef(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useNativeFallback, setUseNativeFallback] = useState(false);

  function formatErrorMessage(err: unknown): string {
    if (typeof err === 'string') return err;
    if (err instanceof Error) return err.message;
    if (err && typeof err === 'object' && 'message' in err) {
      const msg = (err as { message?: unknown }).message;
      if (typeof msg === 'string') return msg;
    }
    return 'Audio failed to load';
  }

  useEffect(() => {
    if (!containerRef.current || !audioUrl) return;

    setIsLoading(true);
    setIsReady(false);
    setError(null);
    setUseNativeFallback(false);
    setCurrentTime(0);

    destroyedRef.current = false;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#737373',
      progressColor: '#dc2626',
      cursorColor: '#dc2626',
      cursorWidth: 1,
      barWidth: 2,
      barGap: 3,
      barRadius: 2,
      height: 48,
      normalize: true,
      backend: 'MediaElement',
      fetchParams: { mode: 'cors' },
    });

    ws.load(audioUrl);

    ws.on('ready', () => {
      setIsLoading(false);
      setIsReady(true);
      setDuration(ws.getDuration());
    });

    ws.on('audioprocess', () => {
      setCurrentTime(ws.getCurrentTime());
    });

    ws.on('seeking', () => {
      setCurrentTime(ws.getCurrentTime());
    });

    ws.on('play', () => setIsPlaying(true));
    ws.on('pause', () => setIsPlaying(false));
    ws.on('finish', () => setIsPlaying(false));
    ws.on('error', (err) => {
      const message = formatErrorMessage(err);
      const isAbortSignalError =
        /signal is aborted without reason/i.test(message) ||
        /aborterror/i.test(message);

      if (isAbortSignalError) {
        return;
      }

      setError(message);
      setUseNativeFallback(true);
      setIsLoading(false);
      setIsReady(false);
    });

    wavesurferRef.current = ws;

    return () => {
      if (destroyedRef.current) return;
      destroyedRef.current = true;
      try {
        ws.destroy();
      } catch {
        // In React strict/dev double-invoke, destroy can receive an aborted signal; safe to ignore.
      }
      wavesurferRef.current = null;
    };
  }, [audioUrl]);

  const togglePlay = useCallback(() => {
    if (useNativeFallback) {
      const audio = nativeAudioRef.current;
      if (!audio) return;

      if (audio.paused) {
        void audio.play();
      } else {
        audio.pause();
      }
      return;
    }

    if (wavesurferRef.current) {
      wavesurferRef.current.playPause();
    }
  }, [useNativeFallback]);

  const seekBy = useCallback((deltaSeconds: number) => {
    if (useNativeFallback) {
      const audio = nativeAudioRef.current;
      if (!audio) return;
      const dur = Number.isFinite(audio.duration) && audio.duration > 0
        ? audio.duration
        : durationSeconds;
      if (!dur || Number.isNaN(dur)) return;
      const next = Math.min(Math.max(0, audio.currentTime + deltaSeconds), dur);
      audio.currentTime = next;
      setCurrentTime(next);
      return;
    }

    const ws = wavesurferRef.current;
    if (!ws) return;
    const dur = ws.getDuration();
    if (!dur || Number.isNaN(dur)) return;
    const next = Math.min(Math.max(0, ws.getCurrentTime() + deltaSeconds), dur);
    ws.seekTo(next / dur);
    setCurrentTime(next);
  }, [durationSeconds, useNativeFallback]);

  const estimatedDuration = durationSeconds ?? duration;

  if (!audioUrl) {
    return (
      <motion.div
        className="py-6 px-4 border border-border bg-card/50"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-border flex items-center justify-center">
            <svg className="w-4 h-4 text-muted" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          <div className="flex-1">
            <div className="h-12 bg-border/50 rounded flex items-center justify-center">
              <span className="text-xs text-muted">Audio will appear here when ready</span>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="py-6 px-4 border border-border bg-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-center">
          <div className="flex-1" />
          <div className="flex items-center gap-3 justify-center">
            <motion.button
              onClick={() => seekBy(-10)}
              disabled={isLoading || !isReady}
              className="w-9 h-9 rounded-full bg-border text-ink flex items-center justify-center hover:bg-border/70 disabled:opacity-50 disabled:cursor-not-allowed transition"
              whileHover={{ scale: isLoading || !isReady ? 1 : 1.05 }}
              whileTap={{ scale: isLoading || !isReady ? 1 : 0.95 }}
              aria-label="Rewind 10 seconds"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 19 2 12l9-7v14Z" />
                <path d="M22 19l-9-7 9-7v14Z" />
              </svg>
            </motion.button>

            <motion.button
              onClick={togglePlay}
              disabled={isLoading || !audioUrl || (!useNativeFallback && !!error)}
              className={`
                w-12 h-12 rounded-full bg-ink text-paper flex items-center justify-center
                hover:bg-ink/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
              `}
              whileHover={{ scale: isLoading || !audioUrl || (!useNativeFallback && !!error) ? 1 : 1.07 }}
              whileTap={{ scale: isLoading || !audioUrl || (!useNativeFallback && !!error) ? 1 : 0.93 }}
              aria-label={isPlaying ? 'Pause audio' : 'Play audio'}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-paper/30 border-t-paper rounded-full animate-spin" />
              ) : isPlaying ? (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="4" width="4" height="16" rx="1" />
                  <rect x="14" y="4" width="4" height="16" rx="1" />
                </svg>
              ) : (
                <svg className="w-4 h-4 ml-0.5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </motion.button>

            <motion.button
              onClick={() => seekBy(10)}
              disabled={isLoading || !isReady}
              className="w-9 h-9 rounded-full bg-border text-ink flex items-center justify-center hover:bg-border/70 disabled:opacity-50 disabled:cursor-not-allowed transition"
              whileHover={{ scale: isLoading || !isReady ? 1 : 1.05 }}
              whileTap={{ scale: isLoading || !isReady ? 1 : 0.95 }}
              aria-label="Forward 10 seconds"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="m13 5 9 7-9 7V5Z" />
                <path d="m2 5 9 7-9 7V5Z" />
              </svg>
            </motion.button>
          </div>
          <div className="flex-1 flex justify-end items-center gap-1 text-xs font-mono text-muted">
            <span className="text-ink">{formatTime(currentTime)}</span>
            <span className="text-muted/50">/</span>
            <span>{formatTime(estimatedDuration)}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex-1">
            {useNativeFallback ? (
              <audio
                ref={nativeAudioRef}
                controls
                preload="metadata"
                src={audioUrl}
                className="w-full h-10"
                onLoadedMetadata={(event) => {
                  const loadedDuration = event.currentTarget.duration;
                  if (Number.isFinite(loadedDuration) && loadedDuration > 0) {
                    setDuration(loadedDuration);
                  }
                  setIsLoading(false);
                  setIsReady(true);
                }}
                onTimeUpdate={(event) => {
                  setCurrentTime(event.currentTarget.currentTime || 0);
                }}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onEnded={() => setIsPlaying(false)}
                onError={() => {
                  setError('Native audio failed to load');
                  setIsLoading(false);
                  setIsReady(false);
                }}
              >
                Your browser does not support audio playback.
              </audio>
            ) : (
              <div
                ref={containerRef}
                className={`waveform-container rounded bg-border/60 ${!isReady ? 'animate-pulse-subtle' : ''}`}
              />
            )}
          </div>
        </div>

        {error && (
          <p className="text-xs text-accent">
            Audio error: {error}
            {useNativeFallback ? ' Switched to native audio controls.' : ''}
          </p>
        )}
      </div>
    </motion.div>
  );
}
