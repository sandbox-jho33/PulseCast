export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export type CurrentStep = 
  | 'INGESTING' 
  | 'RESEARCHING' 
  | 'SCRIPTING' 
  | 'DIRECTOR' 
  | 'AUDIO' 
  | 'COMPLETED';

export type DirectorDecision = 'APPROVE' | 'REWRITE' | 'CONTINUE';

export interface AudioSegment {
  speaker: string;
  text: string;
  audio_url?: string;
}

export interface PodcastState {
  id: string;
  source_url: string;
  source_title?: string;
  created_at: string;
  updated_at: string;
  source_markdown?: string;
  knowledge_points?: string;
  script?: string;
  script_version: number;
  status: JobStatus;
  current_step: CurrentStep;
  progress_pct: number;
  critique_count: number;
  critique_limit: number;
  director_decision?: DirectorDecision;
  audio_segments?: AudioSegment[];
  final_podcast_url?: string;
  duration_seconds?: number;
  error_message?: string;
}

export interface GenerateRequest {
  source_url: string;
}

export interface GenerateResponse {
  job_id: string;
  status: JobStatus;
  current_step: CurrentStep;
}

export interface StatusResponse {
  job_id: string;
  status: JobStatus;
  current_step: CurrentStep;
  progress_pct: number;
  script_version: number;
  source_title?: string;
  final_podcast_url?: string;
  duration_seconds?: number;
  error_message?: string;
}

export interface ScriptResponse {
  job_id: string;
  script: string;
  script_version: number;
  source_title?: string;
}

export interface EditRequest {
  job_id: string;
  script: string;
  resume_from_director?: boolean;
}

export interface EditResponse {
  job_id: string;
  script_version: number;
  status: JobStatus;
}

export interface DownloadResponse {
  final_podcast_url: string;
  duration_seconds: number;
}

export interface StoredJob {
  id: string;
  source_title?: string;
  status: JobStatus;
  created_at: string;
  final_podcast_url?: string;
}

export interface JobListItem {
  job_id: string;
  source_url: string;
  source_title?: string;
  status: JobStatus;
  progress_pct: number;
  created_at: string;
}

export interface JobListResponse {
  jobs: JobListItem[];
  total: number;
}

export const STEP_ORDER: CurrentStep[] = [
  'INGESTING',
  'RESEARCHING', 
  'SCRIPTING',
  'DIRECTOR',
  'AUDIO',
  'COMPLETED',
];

export const STEP_LABELS: Record<CurrentStep, string> = {
  INGESTING: 'Ingesting',
  RESEARCHING: 'Researching',
  SCRIPTING: 'Writing',
  DIRECTOR: 'Reviewing',
  AUDIO: 'Synthesizing',
  COMPLETED: 'Complete',
};

export const STEP_DESCRIPTIONS: Record<CurrentStep, string> = {
  INGESTING: 'Extracting content from source',
  RESEARCHING: 'Analyzing key insights',
  SCRIPTING: 'Crafting conversation',
  DIRECTOR: 'Polishing the script',
  AUDIO: 'Generating audio',
  COMPLETED: 'Ready to listen',
};