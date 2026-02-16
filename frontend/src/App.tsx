import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useJob } from './hooks/useJob';
import { usePolling } from './hooks/usePolling';
import { UrlInput } from './components/UrlInput';
import { ProgressTimeline } from './components/ProgressTimeline';
import { ScriptViewer } from './components/ScriptViewer';
import { ScriptEditor } from './components/ScriptEditor';
import { AudioPlayer } from './components/AudioPlayer';
import { SourcePanel } from './components/SourcePanel';
import { ErrorState } from './components/ErrorState';
import { RecentJobs } from './components/RecentJobs';

function Header() {
  return (
    <motion.header 
      className="flex items-center justify-between mb-12"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="w-8 h-8 rounded-full border-2 border-accent flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-accent" />
          </div>
          <motion.div
            className="absolute inset-0 rounded-full border border-accent/30"
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>
        <h1 className="text-xl font-semibold tracking-tight font-display">PulseCast</h1>
      </div>
      
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-muted/30" />
        <div className="w-2 h-2 rounded-full bg-muted/30" />
        <div className="w-2 h-2 rounded-full bg-muted/30" />
      </div>
    </motion.header>
  );
}

function EmptyState() {
  return (
    <motion.div
      className="flex-1 flex items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
    >
      <div className="text-center max-w-sm">
        <div className="w-16 h-16 mx-auto mb-6 rounded-full border border-border flex items-center justify-center">
          <svg 
            className="w-6 h-6 text-muted" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
        </div>
        <h2 className="text-lg font-medium text-ink mb-2">Transform articles into podcasts</h2>
        <p className="text-sm text-muted leading-relaxed">
          Paste any article URL above to generate a conversational podcast between two AI hosts.
        </p>
      </div>
    </motion.div>
  );
}

function App() {
  const {
    jobId,
    status,
    script,
    isLoading,
    error,
    isPolling,
    recentJobs,
    startGeneration,
    loadJob,
    pollStatus,
    editScript,
    setError,
  } = useJob();

  const [isEditing, setIsEditing] = useState(false);

  usePolling(pollStatus, 2000, isPolling);

  const handleSubmit = useCallback((url: string) => {
    setIsEditing(false);
    startGeneration(url);
  }, [startGeneration]);

  const handleEdit = useCallback(() => {
    setIsEditing(true);
  }, []);

  const handleSaveEdit = useCallback((newScript: string, resume: boolean) => {
    editScript(newScript, resume);
    setIsEditing(false);
  }, [editScript]);

  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
  }, []);

  const handleSelectJob = useCallback((id: string) => {
    setIsEditing(false);
    loadJob(id);
  }, [loadJob]);

  const handleClearError = useCallback(() => {
    setError(null);
  }, [setError]);

  const hasJob = !!status;
  const isComplete = status?.status === 'COMPLETED';
  const isFailed = status?.status === 'FAILED';
  const canEdit = hasJob && !isPolling && (status?.current_step === 'SCRIPTING' || status?.current_step === 'DIRECTOR' || isComplete || isFailed);

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 w-full max-w-6xl mx-auto px-6 py-8 flex flex-col">
        <Header />
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <UrlInput 
            onSubmit={handleSubmit} 
            isLoading={isLoading} 
            disabled={isPolling}
          />
        </motion.div>

        <AnimatePresence mode="wait">
          {error && (
            <motion.div className="mt-6">
              <ErrorState 
                message={error} 
                onDismiss={handleClearError}
              />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex-1 mt-8 flex flex-col">
          <AnimatePresence mode="wait">
            {!hasJob ? (
              <EmptyState key="empty" />
            ) : (
              <motion.div
                key="content"
                className="flex-1 grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
              >
                <div className="lg:border-r lg:border-border lg:pr-8">
                  <ProgressTimeline
                    currentStep={status.current_step}
                    progressPct={status.progress_pct}
                    isRunning={isPolling}
                  />
                </div>

                <div className="flex flex-col min-h-0">
                  <div className="flex-1 min-h-0 mb-6">
                    <AnimatePresence mode="wait">
                      {isEditing && script ? (
                        <ScriptEditor
                          key="editor"
                          script={script.script}
                          onSave={handleSaveEdit}
                          onCancel={handleCancelEdit}
                          isLoading={isLoading}
                        />
                      ) : script ? (
                        <ScriptViewer
                          key="viewer"
                          script={script.script}
                          sourceTitle={status.source_title}
                          onEdit={canEdit ? handleEdit : undefined}
                          canEdit={canEdit}
                        />
                      ) : (
                        <motion.div
                          key="placeholder"
                          className="h-full flex items-center justify-center text-muted text-sm"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                        >
                          {isPolling ? 'Generating script...' : 'Waiting for script...'}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  <AudioPlayer
                    audioUrl={status.final_podcast_url}
                    durationSeconds={status.duration_seconds}
                  />

                  {script?.source_title && (
                    <SourcePanel 
                      markdown={script.script} 
                      title={script.source_title}
                    />
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <RecentJobs
          jobs={recentJobs}
          onSelect={handleSelectJob}
          currentJobId={jobId}
        />
      </div>

      <footer className="py-4 text-center">
        <p className="text-xs text-muted/50">
          Powered by AI
        </p>
      </footer>
    </div>
  );
}

export default App;