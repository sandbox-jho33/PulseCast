import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import type { JobListItem, JobStatus } from '../../types/podcast';

interface PodcastCardProps {
  job: JobListItem;
  onDelete: (jobId: string) => void;
  isDeleting: boolean;
}

function StatusBadge({ status }: { status: JobStatus }) {
  const config = {
    PENDING: { bg: 'bg-muted/20', text: 'text-muted', label: 'Pending' },
    RUNNING: { bg: 'bg-accent/20', text: 'text-accent', label: 'Running' },
    COMPLETED: { bg: 'bg-sarah/20', text: 'text-sarah', label: 'Complete' },
    FAILED: { bg: 'bg-red-500/20', text: 'text-red-500', label: 'Failed' },
  };
  const { bg, text, label } = config[status];

  return (
    <span className={`px-2 py-0.5 text-xs ${bg} ${text} rounded`}>
      {label}
    </span>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function truncateUrl(url: string, maxLength: number = 50): string {
  try {
    const parsed = new URL(url);
    const display = parsed.hostname + parsed.pathname;
    return display.length > maxLength ? display.slice(0, maxLength) + '...' : display;
  } catch {
    return url.length > maxLength ? url.slice(0, maxLength) + '...' : url;
  }
}

export function PodcastCard({ job, onDelete, isDeleting }: PodcastCardProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const navigate = useNavigate();

  const handleView = () => {
    navigate(`/?job=${job.job_id}`);
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = () => {
    onDelete(job.job_id);
    setShowDeleteConfirm(false);
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  return (
    <motion.div
      className="border border-border bg-card p-4 hover:border-muted transition-colors"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      layout
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-medium text-ink truncate">
              {job.source_title || 'Untitled Podcast'}
            </h3>
            <StatusBadge status={job.status} />
          </div>
          <p className="text-xs text-muted truncate mb-2">
            {truncateUrl(job.source_url)}
          </p>
          <p className="text-xs text-muted/60">
            {formatDate(job.created_at)}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <AnimatePresence mode="wait">
            {showDeleteConfirm ? (
              <motion.div
                key="confirm"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex items-center gap-2"
              >
                <button
                  onClick={handleConfirmDelete}
                  disabled={isDeleting}
                  className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                >
                  {isDeleting ? 'Deleting...' : 'Confirm'}
                </button>
                <button
                  onClick={handleCancelDelete}
                  disabled={isDeleting}
                  className="px-2 py-1 text-xs border border-border text-muted rounded hover:border-muted"
                >
                  Cancel
                </button>
              </motion.div>
            ) : (
              <motion.div
                key="actions"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-2"
              >
                <button
                  onClick={handleView}
                  className="px-3 py-1.5 text-xs bg-ink text-paper rounded hover:bg-ink/90 transition-colors"
                >
                  View
                </button>
                <button
                  onClick={handleDeleteClick}
                  className="p-1.5 text-muted hover:text-red-500 transition-colors"
                  title="Delete podcast"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
