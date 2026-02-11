// API Response Types
export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export type JsonObject = Record<string, JsonValue>;
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
  geometry_data: JsonObject;
  quantity: number;
  unit: string;
  pixel_length?: number | null;
  pixel_area?: number | null;
  is_ai_generated: boolean;
  ai_confidence?: number | null;
  ai_model?: string | null;
  is_modified: boolean;
  is_verified: boolean;
  is_rejected: boolean;
  rejection_reason?: string | null;
  review_notes?: string | null;
  reviewed_at?: string | null;
  original_geometry?: JsonObject | null;
  original_quantity?: number | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

// Review Types
export interface ReviewActionResponse {
  status: string;
  measurement_id: string;
  new_quantity?: number | null;
}

export interface AutoAcceptResponse {
  auto_accepted_count: number;
  threshold: number;
}

export interface ConfidenceDistribution {
  high: number;
  medium: number;
  low: number;
}

export interface ReviewStatistics {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  modified: number;
  ai_generated_count: number;
  ai_accuracy_percent: number;
  confidence_distribution: ConfidenceDistribution;
}

export interface NextUnreviewedResponse {
  measurement: Measurement | null;
  remaining_count: number;
}

export interface MeasurementHistoryEntry {
  id: string;
  measurement_id: string;
  action: string;
  actor: string;
  actor_type: string;
  previous_status?: string | null;
  new_status?: string | null;
  previous_quantity?: number | null;
  new_quantity?: number | null;
  change_description?: string | null;
  notes?: string | null;
  created_at: string;
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
  is_ai_generated: boolean;
  is_visible: boolean;
  extra_metadata?: JsonObject | null;
  created_at: string;
  updated_at: string;
}

export interface MeasurementSummary {
  id: string;
  page_id: string;
  geometry_type: string;
  quantity: number;
  unit: string;
  is_ai_generated: boolean;
  is_verified: boolean;
}

export interface ConditionWithMeasurements extends Condition {
  measurements: MeasurementSummary[];
}

export interface ConditionTemplate {
  name: string;
  scope: string;
  category?: string | null;
  measurement_type: "linear" | "area" | "volume" | "count";
  unit: string;
  depth?: number | null;
  thickness?: number | null;
  color: string;
  line_width: number;
  fill_opacity: number;
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
  classification_confidence?: number | null;
  concrete_relevance?: string | null;
  scale_calibrated: boolean;
  thumbnail_url?: string | null;
}

export interface ScaleDetectionResult {
  best_scale?: {
    text: string;
    confidence: number;
    method: string;
    bbox?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  };
  parsed_scales?: JsonValue[];
  scale_bars?: JsonValue[];
}

export interface Page {
  id: string;
  document_id: string;
  page_number: number;
  page_label?: string | null;
  sheet_number?: string | null;
  title?: string | null;
  classification?: string | null;
  classification_confidence?: number | null;
  discipline?: string | null;
  discipline_confidence?: number | null;
  page_type?: string | null;
  page_type_confidence?: number | null;
  concrete_relevance?: string | null;
  concrete_elements?: string[] | null;
  description?: string | null;
  llm_provider?: string | null;
  llm_latency_ms?: number | null;
  detected_scale?: string | null;
  scale_text?: string | null;
  scale_value?: number | null;
  scale_unit?: string | null;
  scale_calibrated: boolean;
  scale_method?: string | null;
  scale_detection_method?: string | null;
  scale_calibration_data?: {
    best_scale?: {
      text: string;
      confidence: number;
      method: string;
      bbox?: {
        x: number;
        y: number;
        width: number;
        height: number;
      };
    };
    parsed_scales?: JsonValue[];
    scale_bars?: JsonValue[];
    manual_calibration?: JsonValue;
    calibration?: JsonValue;
  } | null;
  image_url?: string | null;
  thumbnail_url?: string | null;
  width?: number | null;
  height?: number | null;
  status?: string | null; // pending, processing, completed, error
  ocr_text?: string | null;
  ocr_blocks?: {
    blocks: Array<{
      text: string;
      bbox: {
        x0: number;
        y0: number;
        x1: number;
        y1: number;
      };
      confidence: number;
    }>;
    detected_scales?: string[];
    detected_sheet_numbers?: string[];
    detected_titles?: string[];
  } | null;
  title_block_data?: JsonObject | null;
  extra_metadata?: JsonObject | null;
  created_at: string;
  updated_at: string;
  document?: {
    project_id: string;
    title_block_region?: TitleBlockRegion | null;
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
  title_block_region?: TitleBlockRegion | null;

  // Revision tracking
  revision_number?: string | null;
  revision_date?: string | null;
  revision_label?: string | null;
  supersedes_document_id?: string | null;
  is_latest_revision?: boolean;
}

export interface TitleBlockRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  source_page_id?: string | null;
}

// Assembly Types
export interface Assembly {
  id: string;
  condition_id: string;
  template_id?: string | null;
  name: string;
  description?: string | null;
  csi_code?: string | null;
  csi_description?: string | null;
  default_waste_percent: number;
  productivity_rate?: number | null;
  productivity_unit?: string | null;
  crew_size?: number | null;
  material_cost: number;
  labor_cost: number;
  equipment_cost: number;
  subcontract_cost: number;
  other_cost: number;
  total_cost: number;
  unit_cost: number;
  total_labor_hours: number;
  overhead_percent: number;
  profit_percent: number;
  total_with_markup: number;
  is_locked: boolean;
  locked_at?: string | null;
  locked_by?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssemblyComponent {
  id: string;
  assembly_id: string;
  cost_item_id?: string | null;
  name: string;
  description?: string | null;
  component_type: 'material' | 'labor' | 'equipment' | 'subcontract' | 'other';
  sort_order: number;
  quantity_formula: string;
  calculated_quantity: number;
  unit: string;
  unit_cost: number;
  waste_percent: number;
  quantity_with_waste: number;
  extended_cost: number;
  labor_hours?: number | null;
  labor_rate?: number | null;
  crew_size?: number | null;
  duration_hours?: number | null;
  hourly_rate?: number | null;
  daily_rate?: number | null;
  is_included: boolean;
  is_optional: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssemblyDetail extends Assembly {
  components: AssemblyComponent[];
}

export interface AssemblyTemplate {
  id: string;
  name: string;
  description?: string | null;
  scope: string;
  category?: string | null;
  subcategory?: string | null;
  csi_code?: string | null;
  csi_description?: string | null;
  measurement_type: string;
  expected_unit: string;
  default_waste_percent: number;
  productivity_rate?: number | null;
  productivity_unit?: string | null;
  crew_size?: number | null;
  is_system: boolean;
  is_active: boolean;
  version: number;
  component_definitions: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
}

export interface ProjectCostSummary {
  project_id: string;
  total_conditions: number;
  conditions_with_assemblies: number;
  material_cost: number;
  labor_cost: number;
  equipment_cost: number;
  subcontract_cost: number;
  other_cost: number;
  total_cost: number;
  total_with_markup: number;
}

export interface FormulaValidateResponse {
  is_valid: boolean;
  error?: string | null;
  test_result?: number | null;
}

// Auto Count Types
export interface BBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface AutoCountDetection {
  id: string;
  session_id: string;
  measurement_id?: string | null;
  bbox: BBox;
  center_x: number;
  center_y: number;
  confidence: number;
  detection_source: 'template' | 'llm' | 'both';
  status: 'pending' | 'confirmed' | 'rejected';
  is_auto_confirmed: boolean;
  created_at: string;
  updated_at: string;
}

export interface AutoCountSession {
  id: string;
  page_id: string;
  condition_id: string;
  template_bbox: BBox;
  confidence_threshold: number;
  scale_tolerance: number;
  rotation_tolerance: number;
  detection_method: 'template' | 'llm' | 'hybrid';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_detections: number;
  confirmed_count: number;
  rejected_count: number;
  error_message?: string | null;
  processing_time_ms?: number | null;
  template_match_count: number;
  llm_match_count: number;
  created_at: string;
  updated_at: string;
}

export interface AutoCountSessionDetail extends AutoCountSession {
  detections: AutoCountDetection[];
}

export interface AutoCountStartResponse {
  session_id: string;
  task_id: string;
  status: string;
}

// Quick Adjust Types
export type GeometryAdjustAction =
  | 'nudge'
  | 'snap_to_grid'
  | 'extend'
  | 'trim'
  | 'offset'
  | 'split'
  | 'join';

export interface GeometryAdjustRequest {
  action: GeometryAdjustAction;
  params: Record<string, unknown>;
}

export interface GeometryAdjustResponse {
  status: string;
  action: string;
  measurement_id: string;
  new_geometry_type: string;
  new_geometry_data: Record<string, unknown>;
  new_quantity: number;
  new_unit: string;
  created_measurement_id?: string | null;
}