import { motion } from 'motion/react';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  retryLabel?: string;
  retryHint?: string;
  isRetrying?: boolean;
}

export function ErrorState({
  message,
  onRetry,
  onDismiss,
  retryLabel = 'Retry synthesis',
  retryHint,
  isRetrying = false,
}: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      className="p-4 bg-accent/5 border-l-2 border-accent"
    >
      <div className="flex items-start gap-3">
        <svg 
          className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        
        <div className="flex-1 min-w-0">
          <p className="text-sm text-ink font-medium">Generation failed</p>
          <p className="text-xs text-muted mt-1">{message}</p>
          {retryHint && (
            <p className="text-xs text-muted mt-2">{retryHint}</p>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {onRetry && (
            <motion.button
              onClick={onRetry}
              disabled={isRetrying}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-accent text-paper text-xs font-semibold shadow-sm hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              whileHover={{ scale: isRetrying ? 1 : 1.03 }}
              whileTap={{ scale: isRetrying ? 1 : 0.97 }}
            >
              {isRetrying ? (
                <>
                  <span className="inline-block w-3 h-3 border-2 border-paper/60 border-t-transparent rounded-full animate-spin" />
                  Retrying…
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4.5 4.5v6h6" />
                    <path d="M19.5 19.5v-6h-6" />
                    <path d="M5 19a9 9 0 0 0 9 0 9 9 0 0 0 5-8" />
                    <path d="M19 5a9 9 0 0 0-9 0 9 9 0 0 0-5 8" />
                  </svg>
                  {retryLabel}
                </>
              )}
            </motion.button>
          )}
          {onDismiss && (
            <motion.button
              onClick={onDismiss}
              className="text-xs text-muted hover:text-ink transition-colors"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Dismiss
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
