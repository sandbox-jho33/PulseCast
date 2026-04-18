import { useState, useCallback, useEffect } from 'react';
import type { LLMProvider, StatusResponse, ScriptResponse, StoredJob } from '../types/podcast';
import {
  generatePodcast,
  getJobStatus,
  getScript,
  editScript as apiEditScript,
  retryAudioSynthesis,
} from '../api/podcast';

const STORAGE_KEY = 'pulsecast_jobs';

function loadStoredJobs(): StoredJob[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveStoredJobs(jobs: StoredJob[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs.slice(0, 10)));
}

function isAudioRetryable(status: StatusResponse | null): boolean {
  if (!status) return false;
  const hasPlayableAudioUrl = !!status.final_podcast_url && !status.final_podcast_url.startsWith('file://');

  const failedAtAudio = status.status === 'FAILED' && status.current_step === 'AUDIO';
  const completedWithoutAudio = status.status === 'COMPLETED' && !hasPlayableAudioUrl;

  return failedAtAudio || completedWithoutAudio;
}

export function useJob() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [script, setScript] = useState<ScriptResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRetryingAudio, setIsRetryingAudio] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentJobs, setRecentJobs] = useState<StoredJob[]>(loadStoredJobs);

  const isPolling = status?.status === 'RUNNING' || status?.status === 'PENDING';
  const canRetryAudio = isAudioRetryable(status);

  const addToRecentJobs = useCallback((job: StoredJob) => {
    setRecentJobs(prev => {
      const filtered = prev.filter(j => j.id !== job.id);
      const updated = [job, ...filtered].slice(0, 10);
      saveStoredJobs(updated);
      return updated;
    });
  }, []);

  const startGeneration = useCallback(async (
    sourceUrl: string,
    llmProvider?: LLMProvider,
  ) => {
    setIsLoading(true);
    setError(null);
    setScript(null);

    try {
      const response = await generatePodcast(sourceUrl, llmProvider);
      setJobId(response.job_id);
      setStatus({
        job_id: response.job_id,
        status: response.status,
        current_step: response.current_step,
        progress_pct: 0,
        script_version: 0,
      });
      
      const newJob: StoredJob = {
        id: response.job_id,
        status: response.status,
        created_at: new Date().toISOString(),
      };
      addToRecentJobs(newJob);
      
      window.history.replaceState(null, '', `?job=${response.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start generation');
    } finally {
      setIsLoading(false);
    }
  }, [addToRecentJobs]);

  const loadJob = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const statusResponse = await getJobStatus(id);
      
      setJobId(id);
      setStatus(statusResponse);
      
      if (statusResponse.current_step === 'COMPLETED') {
        const scriptResponse = await getScript(id).catch(() => null);
        if (scriptResponse) {
          setScript(scriptResponse);
        }
      }
      
      window.history.replaceState(null, '', `?job=${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load job');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const pollStatus = useCallback(async () => {
    if (!jobId) return;
    
    try {
      const statusResponse = await getJobStatus(jobId);
      setStatus(statusResponse);
      
      if (statusResponse.status === 'COMPLETED' || statusResponse.status === 'FAILED') {
        setRecentJobs(prev => {
          const updated = prev.map(j => 
            j.id === jobId 
              ? { 
                  ...j, 
                  status: statusResponse.status,
                  source_title: statusResponse.source_title,
                  final_podcast_url: statusResponse.final_podcast_url,
                }
              : j
          );
          saveStoredJobs(updated);
          return updated;
        });
      }
      
      if (statusResponse.current_step === 'COMPLETED') {
        const scriptResponse = await getScript(jobId).catch(() => null);
        if (scriptResponse) {
          setScript(scriptResponse);
        }
      }
    } catch (err) {
      console.error('Poll error:', err);
    }
  }, [jobId]);

  const editScript = useCallback(async (newScript: string, resume: boolean = false) => {
    if (!jobId) return;
    
    setIsLoading(true);
    try {
      const response = await apiEditScript(jobId, newScript, resume);
      setScript(prev => prev ? { ...prev, script: newScript, script_version: response.script_version } : null);
      setStatus(prev => prev ? { ...prev, status: response.status } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to edit script');
    } finally {
      setIsLoading(false);
    }
  }, [jobId]);

  const retryAudio = useCallback(async () => {
    if (!jobId || !canRetryAudio) return;

    setIsRetryingAudio(true);
    setError(null);

    try {
      const statusResponse = await retryAudioSynthesis(jobId);
      setStatus(statusResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry synthesis');
    } finally {
      setIsRetryingAudio(false);
    }
  }, [jobId, canRetryAudio]);

  const clearJob = useCallback(() => {
    setJobId(null);
    setStatus(null);
    setScript(null);
    setIsRetryingAudio(false);
    setError(null);
    window.history.replaceState(null, '', window.location.pathname);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const jobParam = params.get('job');
    if (jobParam && !jobId) {
      loadJob(jobParam);
    }
  }, [jobId, loadJob]);

  return {
    jobId,
    status,
    script,
    isLoading,
    isRetryingAudio,
    error,
    isPolling,
    canRetryAudio,
    recentJobs,
    startGeneration,
    loadJob,
    pollStatus,
    editScript,
    retryAudio,
    clearJob,
    setError,
  };
}
