import { motion, AnimatePresence } from 'motion/react';
import { Link } from 'react-router-dom';
import { useLibrary } from '../../hooks/useLibrary';
import { PodcastCard } from './PodcastCard';
import { SearchBar } from './SearchBar';
import { Pagination } from './Pagination';

function EmptyState({ hasSearch }: { hasSearch: boolean }) {
  return (
    <motion.div
      className="flex-1 flex items-center justify-center py-12"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="text-center max-w-sm">
        <div className="w-16 h-16 mx-auto mb-6 rounded-full border border-border flex items-center justify-center">
          <svg
            className="w-6 h-6 text-muted"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-ink mb-2">
          {hasSearch ? 'No podcasts found' : 'No podcasts yet'}
        </h3>
        <p className="text-sm text-muted">
          {hasSearch
            ? 'Try a different search term'
            : 'Generate your first podcast to see it here'}
        </p>
        {!hasSearch && (
          <Link
            to="/"
            className="inline-block mt-4 px-4 py-2 bg-ink text-paper text-sm rounded hover:bg-ink/90 transition-colors"
          >
            Create Podcast
          </Link>
        )}
      </div>
    </motion.div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="border border-border bg-card p-4 animate-pulse">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="h-4 bg-border rounded w-2/3 mb-2" />
              <div className="h-3 bg-border rounded w-1/2 mb-2" />
              <div className="h-3 bg-border rounded w-1/4" />
            </div>
            <div className="h-8 w-16 bg-border rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function LibraryPage() {
  const {
    jobs,
    total,
    isLoading,
    error,
    search,
    page,
    totalPages,
    deletingId,
    deleteJobById,
    handleSearch,
    nextPage,
    prevPage,
    goToPage,
  } = useLibrary();

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 w-full max-w-4xl mx-auto px-6 py-8 flex flex-col">
        <motion.header
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Link to="/" className="text-muted hover:text-ink transition-colors">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 12H5M12 19l-7-7 7-7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </Link>
              <h1 className="text-xl font-semibold tracking-tight font-display">Library</h1>
            </div>
            <Link
              to="/"
              className="px-4 py-2 bg-ink text-paper text-sm rounded hover:bg-ink/90 transition-colors"
            >
              New Podcast
            </Link>
          </div>

          <div className="max-w-md">
            <SearchBar value={search} onChange={handleSearch} />
          </div>

          {total > 0 && (
            <p className="mt-4 text-sm text-muted">
              {total} podcast{total !== 1 ? 's' : ''}
            </p>
          )}
        </motion.header>

        {error && (
          <motion.div
            className="mb-4 p-4 bg-red-500/10 border border-red-500/20 text-red-500 text-sm rounded"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {error}
          </motion.div>
        )}

        <div className="flex-1">
          {isLoading ? (
            <LoadingState />
          ) : jobs.length === 0 ? (
            <EmptyState hasSearch={!!search} />
          ) : (
            <>
              <AnimatePresence mode="popLayout">
                <div className="space-y-3">
                  {jobs.map((job) => (
                    <PodcastCard
                      key={job.job_id}
                      job={job}
                      onDelete={deleteJobById}
                      isDeleting={deletingId === job.job_id}
                    />
                  ))}
                </div>
              </AnimatePresence>

              <div className="mt-8">
                <Pagination
                  currentPage={page}
                  totalPages={totalPages}
                  onPrev={prevPage}
                  onNext={nextPage}
                  onGoto={goToPage}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
