import type {
  GenerateRequest,
  GenerateResponse,
  LLMProvider,
  StatusResponse,
  ScriptResponse,
  EditRequest,
  EditResponse,
  DownloadResponse,
  JobListResponse,
  CredentialProvider,
  CredentialStatusResponse,
} from '../types/podcast';

const API_BASE = '/api/v1/podcast';
const CREDENTIALS_BASE = '/api/v1/credentials';
type TokenGetter = () => Promise<string | null>;

let tokenGetter: TokenGetter | null = null;

export function setAuthTokenGetter(getter: TokenGetter): void {
  tokenGetter = getter;
}

async function authFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const token = tokenGetter ? await tokenGetter() : null;
  const headers = new Headers(init.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(input, { ...init, headers });
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function generatePodcast(
  source_url: string,
  llm_provider?: LLMProvider,
): Promise<GenerateResponse> {
  const body: GenerateRequest = { source_url };
  if (llm_provider) body.llm_provider = llm_provider;
  const response = await authFetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse<GenerateResponse>(response);
}

export async function getJobStatus(job_id: string): Promise<StatusResponse> {
  const response = await authFetch(`${API_BASE}/status/${job_id}`);
  return handleResponse<StatusResponse>(response);
}

export async function retryAudioSynthesis(job_id: string): Promise<StatusResponse> {
  const response = await authFetch(`${API_BASE}/${job_id}/retry-audio`, {
    method: 'POST',
  });
  return handleResponse<StatusResponse>(response);
}

export async function getScript(job_id: string): Promise<ScriptResponse> {
  const response = await authFetch(`${API_BASE}/${job_id}/script`);
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
  const response = await authFetch(`${API_BASE}/edit`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse<EditResponse>(response);
}

export async function getDownload(job_id: string): Promise<DownloadResponse> {
  const response = await authFetch(`${API_BASE}/download/${job_id}`);
  return handleResponse<DownloadResponse>(response);
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const response = await fetch('/health');
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
  const response = await authFetch(`${API_BASE}/jobs?${params}`);
  return handleResponse<JobListResponse>(response);
}

export async function deleteJob(job_id: string): Promise<void> {
  const response = await authFetch(`${API_BASE}/${job_id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
}

export async function listCredentials(): Promise<CredentialStatusResponse> {
  const response = await authFetch(CREDENTIALS_BASE);
  return handleResponse<CredentialStatusResponse>(response);
}

export async function saveCredential(
  provider: CredentialProvider,
  api_key: string,
): Promise<CredentialStatusResponse> {
  const response = await authFetch(CREDENTIALS_BASE, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key }),
  });
  return handleResponse<CredentialStatusResponse>(response);
}

export async function deleteCredential(provider: CredentialProvider): Promise<void> {
  const response = await authFetch(`${CREDENTIALS_BASE}/${provider}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
}
