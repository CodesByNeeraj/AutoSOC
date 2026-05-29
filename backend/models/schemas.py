from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

#incoming alert from the frontend
class AlertInput(BaseModel):
    raw_log: str
    source: Optional[str] = "manual"

#triage agent output shape
class TriageSchema(BaseModel):
    title: str
    priority: str
    category: str
    summary: str
    indicators: List[str]
    confidence: int
    needs_investigation: bool
    human_review: bool
    justification: str

#investigation agent output shape
class InvestigationSchema(BaseModel):
    incident_id: str
    attack_pattern: str
    mitre_tactics: List[str]
    timeline: List[str]
    affected_assets: List[str]
    blast_radius: str
    root_cause: str
    evidence_gaps: List[str]
    confidence: int
    human_review: bool
    escalate: bool
    summary: str

#response agent output shape
class ResponseSchema(BaseModel):
    incident_id: str
    immediate_actions: List[str]
    short_term_actions: List[str]
    long_term_actions: List[str]
    containment_strategy: str
    eradication_steps: List[str]
    recovery_steps: List[str]
    notify_teams: List[str]
    escalate_to_human: bool
    estimated_resolution_time: str
    confidence: int
    human_review: bool
    summary: str

#report agent output shape
class ReportSchema(BaseModel):
    incident_id: str
    executive_summary: str
    technical_summary: str
    timeline: List[str]
    affected_assets: List[str]
    attack_narrative: str
    response_actions_taken: List[str]
    lessons_learned: List[str]
    recommendations: List[str]
    open_items: List[str]
    severity_justification: str
    authored_by: str
    report_confidence: int

#full pipeline response sent back to frontend
class AnalysisResponse(BaseModel):
    incident_id: str
    triage: TriageSchema
    investigation: InvestigationSchema
    response: ResponseSchema
    report: ReportSchema

#incident as stored in db
class IncidentSchema(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    raw_log: str
    created_at: datetime

    class Config:
        from_attributes = True

#finding as stored in db
class FindingSchema(BaseModel):
    id: str
    incident_id: str
    agent: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

#report as stored in db
class StoredReportSchema(BaseModel):
    id: str
    incident_id: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

#dashboard stats response
class StatsSchema(BaseModel):
    total: int
    open: int
    resolved: int
    by_priority: dict

#manual status update
class StatusUpdate(BaseModel):
    status: str