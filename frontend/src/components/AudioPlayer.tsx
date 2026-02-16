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
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !audioUrl) return;

    setIsLoading(true);
    
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
      backend: 'WebAudio',
    });

    ws.load(audioUrl);

    ws.on('ready', () => {
      setIsLoading(false);
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

    wavesurferRef.current = ws;

    return () => {
      ws.destroy();
      wavesurferRef.current = null;
    };
  }, [audioUrl]);

  const togglePlay = useCallback(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause();
    }
  }, []);

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
      <div className="flex items-center gap-4">
        <motion.button
          onClick={togglePlay}
          disabled={isLoading}
          className={`
            w-10 h-10 rounded-full bg-ink text-paper flex items-center justify-center
            hover:bg-ink/90 transition-colors disabled:opacity-50
          `}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-paper/30 border-t-paper rounded-full animate-spin" />
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

        <div className="flex-1">
          <div ref={containerRef} className="waveform-container" />
        </div>

        <div className="flex items-center gap-1 text-xs font-mono text-muted w-24 justify-end">
          <span>{formatTime(currentTime)}</span>
          <span className="text-muted/50">/</span>
          <span>{formatTime(estimatedDuration)}</span>
        </div>
      </div>
    </motion.div>
  );
}