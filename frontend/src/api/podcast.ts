import type {
  GenerateRequest,
  GenerateResponse,
  StatusResponse,
  ScriptResponse,
  EditRequest,
  EditResponse,
  DownloadResponse,
  JobListResponse,
} from '../types/podcast';

const API_BASE = '/api/v1/podcast';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function generatePodcast(source_url: string): Promise<GenerateResponse> {
  const response = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_url } as GenerateRequest),
  });
  return handleResponse<GenerateResponse>(response);
}

export async function getJobStatus(job_id: string): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE}/status/${job_id}`);
  return handleResponse<StatusResponse>(response);
}

export async function getScript(job_id: string): Promise<ScriptResponse> {
  const response = await fetch(`${API_BASE}/${job_id}/script`);
  return handleResponse<ScriptResponse>(response);
}

export async function editScript(
  job_id: string,
  script: string,
  resume_from_director?: boolean
): Promise<EditResponse> {
  const body: EditRequest = { job_id, script };
  if (resume_from_director !== undefined) {
    body.resume_from_director = resume_from_director;
  }
  const response = await fetch(`${API_BASE}/edit`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse<EditResponse>(response);
}

export async function getDownload(job_id: string): Promise<DownloadResponse> {
  const response = await fetch(`${API_BASE}/download/${job_id}`);
  return handleResponse<DownloadResponse>(response);
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse<{ status: string; service: string }>(response);
}

export async function listJobs(
  limit: number = 50,
  offset: number = 0,
  search: string = ""
): Promise<JobListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    search,
  });
  const response = await fetch(`${API_BASE}/jobs?${params}`);
  return handleResponse<JobListResponse>(response);
}

export async function deleteJob(job_id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${job_id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
}