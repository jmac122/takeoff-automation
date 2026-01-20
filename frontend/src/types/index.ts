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
  condition_id: string;
  page_id: string;
  geometry_type: "line" | "polyline" | "polygon" | "rectangle" | "circle" | "point";
  geometry_data: Record<string, any>;
  quantity: number;
  unit: string;
  pixel_length?: number | null;
  pixel_area?: number | null;
  is_ai_generated: boolean;
  ai_confidence?: number | null;
  is_modified: boolean;
  is_verified: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

// Condition Types
export interface Condition {
  id: string;
  project_id: string;
  name: string;
  description?: string | null;
  scope: string;
  category?: string | null;
  measurement_type: "linear" | "area" | "volume" | "count";
  color: string;
  line_width: number;
  fill_opacity: number;
  unit: string;
  depth?: number | null;
  thickness?: number | null;
  total_quantity: number;
  measurement_count: number;
  sort_order: number;
  extra_metadata?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

// Project Types
export interface Project {
  id: string;
  name: string;
  description?: string | null;
  client_name?: string | null;
  project_address?: string | null;
  status?: string;
  document_count?: number;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  client_name?: string;
  project_address?: string;
}

// Document Types
export interface PageSummary {
  id: string;
  page_number: number;
  classification?: string | null;
  scale_calibrated: boolean;
  thumbnail_url?: string | null;
}

export interface Page {
  id: string;
  document_id: string;
  page_number: number;
  page_label?: string | null;
  classification?: string | null;
  classification_confidence?: number | null;
  detected_scale?: string | null;
  scale_value?: number | null;
  scale_unit?: string | null;
  scale_calibrated: boolean;
  scale_method?: string | null;
  image_url?: string | null;
  thumbnail_url?: string | null;
  width?: number | null;
  height?: number | null;
  ocr_text?: string | null;
  title_block_data?: Record<string, any> | null;
  extra_metadata?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  document?: {
    project_id: string;
  };
}

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  page_count: number | null;
  processing_error?: string | null;
  created_at: string;
  updated_at: string;
  pages?: PageSummary[];
}