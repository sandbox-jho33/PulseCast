import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface SourcePanelProps {
  markdown: string;
  title?: string;
}

export function SourcePanel({ markdown, title }: SourcePanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-6">
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-xs text-muted hover:text-ink transition-colors"
        whileHover={{ x: 2 }}
      >
        <motion.svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <path d="M9 18l6-6-6-6" />
        </motion.svg>
        <span className="font-medium tracking-wide uppercase">Source</span>
      </motion.button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <div className="mt-3 p-4 bg-card border border-border text-sm leading-relaxed max-h-80 overflow-y-auto">
              {title && (
                <p className="font-medium text-ink mb-3">{title}</p>
              )}
              <div className="prose prose-sm prose-neutral max-w-none prose-headings:font-medium prose-headings:text-ink prose-p:text-muted prose-a:text-accent prose-strong:text-ink">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {markdown}
                </ReactMarkdown>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}