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
