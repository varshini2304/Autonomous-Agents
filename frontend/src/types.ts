export interface AgentRequest {
  request: string
}

export interface PlanStep {
  id: string
  description: string
  tool: string
  expected_output: string
}

export interface AgentPlan {
  document_type: string
  title: string
  objective: string
  assumptions: string[]
  tasks: PlanStep[]
}

export interface StepResult {
  step_id: string
  description: string
  tool: string
  status: 'succeeded' | 'failed' | 'skipped'
  output: unknown
  error: string | null
}

export interface AgentResponse {
  summary: string
  plan: AgentPlan
  assumptions: string[]
  steps: StepResult[]
  document_id: string | null
  download_url: string | null
  status: 'succeeded' | 'partial' | 'failed'
  provider_mode: 'xai' | 'groq' | 'fallback'
  planner_status: 'succeeded' | 'fallback'
  fallback_reason: string | null
}

export interface ApiErrorBody {
  detail?: string | { [key: string]: unknown } | Array<{ msg?: string; loc?: Array<string | number> }>
}
