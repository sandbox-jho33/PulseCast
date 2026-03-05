import { motion } from 'motion/react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPrev: () => void;
  onNext: () => void;
  onGoto: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPrev, onNext, onGoto }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages = getPageNumbers(currentPage, totalPages);

  return (
    <motion.div
      className="flex items-center justify-center gap-1"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <button
        onClick={onPrev}
        disabled={currentPage === 0}
        className="p-2 text-muted hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {pages.map((page, idx) =>
        page === '...' ? (
          <span key={`ellipsis-${idx}`} className="px-2 text-muted">...</span>
        ) : (
          <button
            key={page}
            onClick={() => onGoto(page as number)}
            className={`w-8 h-8 text-sm rounded transition-colors ${
              page === currentPage
                ? 'bg-ink text-paper'
                : 'text-muted hover:text-ink hover:bg-card'
            }`}
          >
            {(page as number) + 1}
          </button>
        )
      )}

      <button
        onClick={onNext}
        disabled={currentPage === totalPages - 1}
        className="p-2 text-muted hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </motion.div>
  );
}

function getPageNumbers(current: number, total: number): (number | string)[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i);
  }

  const pages: (number | string)[] = [];

  if (current < 3) {
    pages.push(0, 1, 2, 3, '...', total - 1);
  } else if (current > total - 4) {
    pages.push(0, '...', total - 4, total - 3, total - 2, total - 1);
  } else {
    pages.push(0, '...', current - 1, current, current + 1, '...', total - 1);
  }

  return pages;
}
