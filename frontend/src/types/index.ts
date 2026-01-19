// API Response Types
export interface HealthResponse {
  status: string;
}

// LLM Provider Types
export interface LLMProvider {
  name: string;
  display_name: string;
  model: string;
  available: boolean;
  is_default: boolean;
}

export interface LLMSettings {
  available_providers: LLMProvider[];
  default_provider: string;
  fallback_providers: string[];
  task_overrides: Record<string, string>;
}

// Measurement Types
export interface Measurement {
  id: string;
  conditionId: string;
  geometryType: "polygon" | "polyline" | "line" | "point";
  quantity: number;
}

// Document Types
export interface PageSummary {
  id: string;
  page_number: number;
  classification?: string | null;
  scale_calibrated: boolean;
  thumbnail_url?: string | null;
}

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: string;
  page_count?: number | null;
  processing_error?: string | null;
  created_at: string;
  updated_at: string;
  pages: PageSummary[];
}