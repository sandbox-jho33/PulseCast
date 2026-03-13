import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface ScriptViewerProps {
  script: string | null | undefined;
  sourceTitle?: string;
  onEdit?: () => void;
  canEdit?: boolean;
  shouldTruncate?: boolean;
}

interface ParsedLine {
  speaker: 'LEO' | 'SARAH' | 'NARRATOR' | 'DIRECTION';
  text: string;
}

const PREVIEW_LINE_COUNT = 10;

function parseScript(script: string): ParsedLine[] {
  if (!script) return [];
  const lines: ParsedLine[] = [];
  const rawLines = script.split('\n');
  
  for (const line of rawLines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    
    const leoMatch = trimmed.match(/^LEO:\s*(.+)/);
    const sarahMatch = trimmed.match(/^SARAH:\s*(.+)/);
    const directionMatch = trimmed.match(/^\[(.+)\]$/);
    
    if (leoMatch) {
      lines.push({ speaker: 'LEO', text: leoMatch[1] });
    } else if (sarahMatch) {
      lines.push({ speaker: 'SARAH', text: sarahMatch[1] });
    } else if (directionMatch) {
      lines.push({ speaker: 'DIRECTION', text: directionMatch[1] });
    } else if (trimmed.startsWith('(') && trimmed.endsWith(')')) {
      lines.push({ speaker: 'NARRATOR', text: trimmed.slice(1, -1) });
    } else {
      lines.push({ speaker: 'NARRATOR', text: trimmed });
    }
  }
  
  return lines;
}

export function ScriptViewer({ script, sourceTitle, onEdit, canEdit, shouldTruncate = false }: ScriptViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const allLines = useMemo(() => parseScript(script ?? ''), [script]);

  const hasMoreLines = allLines.length > PREVIEW_LINE_COUNT;
  const showTruncation = shouldTruncate && hasMoreLines && !isExpanded;
  const visibleLines = showTruncation ? allLines.slice(0, PREVIEW_LINE_COUNT) : allLines;

  if (!script || allLines.length === 0) {
    return (
      <motion.div
        className="h-full flex flex-col items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <span className="text-xs font-medium tracking-widest text-muted uppercase">Script</span>
        <p className="text-sm text-muted mt-2">No script available yet.</p>
      </motion.div>
    );
  }
  
  const speakerStyles = {
    LEO: {
      badge: 'bg-leo/10 text-leo border-leo/20',
      indicator: 'bg-leo',
      text: 'text-ink',
    },
    SARAH: {
      badge: 'bg-sarah/10 text-sarah border-sarah/20',
      indicator: 'bg-sarah',
      text: 'text-ink',
    },
    NARRATOR: {
      badge: 'bg-muted/10 text-muted border-muted/20',
      indicator: 'bg-muted',
      text: 'text-muted',
    },
    DIRECTION: {
      badge: 'bg-accent/10 text-accent border-accent/20',
      indicator: 'bg-accent',
      text: 'text-muted italic',
    },
  };

  return (
    <motion.div
      className="h-full flex flex-col"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-xs font-medium tracking-widest text-muted uppercase">Script</span>
          {sourceTitle && (
            <p className="text-sm text-ink mt-1 font-medium truncate max-w-md">{sourceTitle}</p>
          )}
        </div>
        {canEdit && onEdit && (
          <motion.button
            onClick={onEdit}
            className="text-xs text-muted hover:text-accent transition-colors underline underline-offset-4"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Edit
          </motion.button>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto pr-2 -mr-2 scrollbar-thin">
        <div className="space-y-3">
          <AnimatePresence mode="popLayout">
            {visibleLines.map((line, index) => {
              const styles = speakerStyles[line.speaker];
              
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ 
                    duration: 0.3, 
                    delay: Math.min(index * 0.02, 0.5),
                    ease: [0.16, 1, 0.3, 1]
                  }}
                  className="flex gap-3"
                >
                  <div className="flex-shrink-0 pt-1">
                    <div className={`w-1.5 h-1.5 rounded-full ${styles.indicator} mt-1.5`} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    {line.speaker !== 'NARRATOR' && line.speaker !== 'DIRECTION' && (
                      <span className={`
                        inline-block text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded border mb-1
                        ${styles.badge}
                      `}>
                        {line.speaker}
                      </span>
                    )}
                    <p className={`text-sm leading-relaxed ${styles.text}`}>
                      {line.text}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
        
        {shouldTruncate && hasMoreLines && (
          <motion.div
            className="pt-4 flex justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1.5 text-xs text-muted hover:text-ink transition-colors"
            >
              {isExpanded ? (
                <>
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 15l-6-6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  Show less
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  Show more ({allLines.length - PREVIEW_LINE_COUNT} lines)
                </>
              )}
            </button>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
