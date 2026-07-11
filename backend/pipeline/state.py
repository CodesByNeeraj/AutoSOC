from pydantic import BaseModel

class PipelineState(BaseModel):
    incident_id: str = ""
    raw_log: str = ""
    environment_context: str = ""
    incident_context: str = ""
    triage_result: dict = {}
    investigation_result: dict = {}
    response_result: dict = {}
    report_result: dict = {}
    stopped_at_triage: bool = False
