import { motion } from 'motion/react';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorState({ message, onRetry, onDismiss }: ErrorStateProps) {
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
        </div>
        
        <div className="flex items-center gap-2">
          {onRetry && (
            <motion.button
              onClick={onRetry}
              className="text-xs text-accent hover:text-accent/80 transition-colors font-medium"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Retry
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