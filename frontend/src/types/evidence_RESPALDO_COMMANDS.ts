export type EvidenceStatus =
  | "DETECTED"
  | "RESPONDING"
  | "CONTAINED"
  | "FAILED";

export interface EvidenceDetection {
  rule_id: string | null;
  wazuh_level: number | null;
  attempts: number | null;
  user: string | null;
  sensor_confirmed: boolean;
  timestamp: string | null;
}

export interface EvidenceMitre {
  technique_id: string;
  technique_name: string;
  tactic: string;
  reference_url: string | null;
}

export interface EvidenceResponse {
  id: number;
  action_type: string;
  target: string | null;
  status: string;
  reversible: boolean;
  duration_seconds: number | null;
  reason: string | null;
  result: string | null;
  created_at: string | null;
  executed_at: string | null;
  rolled_back_at: string | null;
  failure_reason: string | null;
}

export interface EvidenceTimelineItem {
  stage:
    | "DETECTED"
    | "RESPONDING"
    | "CONTAINED"
    | "FAILED";

  timestamp: string | null;
  completed: boolean;
}

export interface IncidentEvidence {
  incident_id: number;
  event_id: number;

  status: EvidenceStatus;
  incident_status: string;

  severity: string;

  event_type: string;
  source: string;
  source_ip: string | null;
  server_id: number | null;

  description: string;

  detection: EvidenceDetection;
  mitre: EvidenceMitre | null;
  response: EvidenceResponse | null;

  timeline: EvidenceTimelineItem[];
}