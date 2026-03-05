import { useState, useCallback, useEffect } from 'react';
import type { JobListItem } from '../types/podcast';
import { listJobs as apiListJobs, deleteJob as apiDeleteJob } from '../api/podcast';

const ITEMS_PER_PAGE = 10;

export function useLibrary() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);

  const loadJobs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiListJobs(ITEMS_PER_PAGE, page * ITEMS_PER_PAGE, search);
      setJobs(response.jobs);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load podcasts');
    } finally {
      setIsLoading(false);
    }
  }, [page, search]);

  const deleteJobById = useCallback(async (jobId: string) => {
    setDeletingId(jobId);
    try {
      await apiDeleteJob(jobId);
      setJobs(prev => prev.filter(j => j.job_id !== jobId));
      setTotal(prev => Math.max(0, prev - 1));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete podcast');
    } finally {
      setDeletingId(null);
    }
  }, []);

  const handleSearch = useCallback((query: string) => {
    setSearch(query);
    setPage(0);
  }, []);

  const nextPage = useCallback(() => {
    if (page < totalPages - 1) {
      setPage(p => p + 1);
    }
  }, [page, totalPages]);

  const prevPage = useCallback(() => {
    if (page > 0) {
      setPage(p => p - 1);
    }
  }, [page]);

  const goToPage = useCallback((pageNum: number) => {
    if (pageNum >= 0 && pageNum < totalPages) {
      setPage(pageNum);
    }
  }, [totalPages]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  return {
    jobs,
    total,
    isLoading,
    error,
    search,
    page,
    totalPages,
    deletingId,
    loadJobs,
    deleteJobById,
    handleSearch,
    nextPage,
    prevPage,
    goToPage,
    setError,
  };
}
