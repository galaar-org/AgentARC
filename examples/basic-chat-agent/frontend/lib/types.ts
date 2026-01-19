export type ValidationStage =
  | 'started'
  | 'intent_analysis'
  | 'policy_validation'
  | 'simulation'
  | 'honeypot_detection'
  | 'llm_validation'
  | 'completed';

export type ValidationStatus =
  | 'started'
  | 'passed'
  | 'failed'
  | 'warning'
  | 'info';

export interface ValidationEvent {
  stage: ValidationStage;
  status: ValidationStatus;
  message: string;
  timestamp: number;
  details: Record<string, unknown>;
}

export interface SSEAgentEvent {
  type: 'agent';
  content: string;
}

export interface SSEToolEvent {
  type: 'tool';
  content: string;
}

export interface SSEEventsEvent {
  type: 'events';
  events: ValidationEvent[];
}

export interface SSEErrorEvent {
  type: 'error';
  content: string;
}

export interface SSEDoneEvent {
  type: 'done';
}

export type SSEEvent =
  | SSEAgentEvent
  | SSEToolEvent
  | SSEEventsEvent
  | SSEErrorEvent
  | SSEDoneEvent;
