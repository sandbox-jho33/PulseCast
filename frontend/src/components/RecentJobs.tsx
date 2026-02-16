import { motion } from 'motion/react';
import type { StoredJob, JobStatus } from '../types/podcast';

interface RecentJobsProps {
  jobs: StoredJob[];
  onSelect: (jobId: string) => void;
  currentJobId?: string | null;
}

function StatusIndicator({ status }: { status: JobStatus }) {
  const colors = {
    PENDING: 'bg-muted',
    RUNNING: 'bg-accent animate-pulse-subtle',
    COMPLETED: 'bg-sarah',
    FAILED: 'bg-accent',
  };

  return (
    <span className={`w-1.5 h-1.5 rounded-full ${colors[status]}`} />
  );
}

function truncateId(id: string): string {
  return `${id.slice(0, 8)}...`;
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export function RecentJobs({ jobs, onSelect, currentJobId }: RecentJobsProps) {
  if (jobs.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.4 }}
      className="pt-6 border-t border-border"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium tracking-widest text-muted uppercase">Recent</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {jobs.slice(0, 5).map((job) => {
          const isActive = job.id === currentJobId;
          
          return (
            <motion.button
              key={job.id}
              onClick={() => onSelect(job.id)}
              className={`
                flex items-center gap-2 px-3 py-1.5 text-xs transition-colors
                ${isActive 
                  ? 'bg-ink text-paper' 
                  : 'bg-card border border-border text-muted hover:text-ink hover:border-muted'
                }
              `}
              whileHover={{ scale: isActive ? 1 : 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <StatusIndicator status={job.status} />
              <span className="font-mono">{truncateId(job.id)}</span>
              <span className={isActive ? 'text-paper/60' : 'text-muted/60'}>
                {formatTimeAgo(job.created_at)}
              </span>
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}