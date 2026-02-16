import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface UrlInputProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
  disabled: boolean;
}

export function UrlInput({ onSubmit, isLoading, disabled }: UrlInputProps) {
  const [url, setUrl] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim() && !isLoading && !disabled) {
      onSubmit(url.trim());
    }
  }, [url, isLoading, disabled, onSubmit]);

  const isValidUrl = url.trim().length > 0 && (url.startsWith('http://') || url.startsWith('https://'));

  return (
    <motion.div 
      className="w-full"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <label 
            className="block text-xs font-medium tracking-widest text-muted uppercase mb-3"
            htmlFor="url-input"
          >
            Paste Article URL
          </label>
          
          <div className={`
            relative flex items-center border-b-2 transition-colors duration-300
            ${isFocused ? 'border-accent' : 'border-border'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}>
            <input
              id="url-input"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="https://..."
              disabled={disabled || isLoading}
              className="
                flex-1 bg-transparent py-4 pr-4 text-lg font-light
                placeholder:text-muted/40 focus:outline-none
                disabled:cursor-not-allowed
              "
              autoComplete="url"
              spellCheck={false}
            />
            
            <motion.button
              type="submit"
              disabled={!isValidUrl || isLoading || disabled}
              className={`
                flex items-center justify-center w-12 h-12
                transition-colors duration-200
                disabled:opacity-30 disabled:cursor-not-allowed
                ${isValidUrl && !isLoading ? 'text-accent hover:text-accent/80' : 'text-muted'}
              `}
              whileHover={{ scale: isValidUrl && !isLoading ? 1.05 : 1 }}
              whileTap={{ scale: isValidUrl && !isLoading ? 0.95 : 1 }}
            >
              <AnimatePresence mode="wait">
                {isLoading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-5 h-5 border-2 border-muted border-t-accent rounded-full animate-spin"
                  />
                ) : (
                  <motion.svg
                    key="arrow"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </motion.svg>
                )}
              </AnimatePresence>
            </motion.button>
          </div>
        </div>
      </form>
    </motion.div>
  );
}