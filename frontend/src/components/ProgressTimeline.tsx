import { motion } from 'motion/react';
import type { CurrentStep } from '../types/podcast';
import { STEP_ORDER, STEP_LABELS, STEP_DESCRIPTIONS } from '../types/podcast';

interface ProgressTimelineProps {
  currentStep: CurrentStep;
  progressPct: number;
  isRunning: boolean;
}

export function ProgressTimeline({ currentStep, progressPct, isRunning }: ProgressTimelineProps) {
  const currentIndex = STEP_ORDER.indexOf(currentStep);

  return (
    <motion.div 
      className="w-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, delay: 0.2 }}
    >
      <div className="mb-4">
        <span className="text-xs font-medium tracking-widest text-muted uppercase">Progress</span>
      </div>
      
      <div className="space-y-1">
        {STEP_ORDER.map((step, index) => {
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex;
          
          return (
            <motion.div
              key={step}
              className="relative"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ 
                duration: 0.4, 
                delay: 0.1 + index * 0.05,
                ease: [0.16, 1, 0.3, 1]
              }}
            >
              <div className="flex items-center py-2.5">
                <div className="w-8 flex-shrink-0 flex items-center justify-center">
                  <motion.div
                    className={`
                      w-2 h-2 rounded-full transition-colors duration-300
                      ${isCompleted ? 'bg-accent' : isActive ? 'bg-accent' : 'bg-border'}
                    `}
                    animate={isActive && isRunning ? { scale: [1, 1.3, 1] } : { scale: 1 }}
                    transition={{ 
                      duration: 1.5, 
                      repeat: isActive && isRunning ? Infinity : 0,
                      ease: "easeInOut"
                    }}
                  />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between">
                    <span className={`
                      text-sm font-medium transition-colors duration-300
                      ${isActive ? 'text-ink' : isCompleted ? 'text-muted' : 'text-muted/50'}
                    `}>
                      {STEP_LABELS[step]}
                    </span>
                    
                    {isActive && isRunning && (
                      <motion.span
                        className="text-xs text-accent font-mono"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3 }}
                      >
                        {Math.round(progressPct)}%
                      </motion.span>
                    )}
                    
                    {isCompleted && (
                      <motion.svg
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 400, damping: 15 }}
                        className="w-3.5 h-3.5 text-accent"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M20 6L9 17l-5-5" />
                      </motion.svg>
                    )}
                  </div>
                  
                  {isActive && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="text-xs text-muted/70 mt-0.5 overflow-hidden"
                    >
                      {STEP_DESCRIPTIONS[step]}
                    </motion.p>
                  )}
                </div>
              </div>
              
              {index < STEP_ORDER.length - 1 && (
                <div className="absolute left-[15px] top-[44px] w-px h-3 bg-border" />
              )}
            </motion.div>
          );
        })}
      </div>
      
      <motion.div 
        className="mt-6 pt-4 border-t border-border"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted">Overall</span>
          <span className="text-xs font-mono text-muted">{Math.round(progressPct)}%</span>
        </div>
        <div className="h-1 bg-border rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-accent rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progressPct}%` }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}