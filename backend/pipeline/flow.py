from crewai.flow.flow import Flow, listen, router, start
from pipeline.state import PipelineState
from agents.triage import triage_agent
from agents.investigation import investigation_agent
from agents.response import response_agent
from agents.report import report_agent
from db.database import SessionLocal, Incident, Finding, Report
from datetime import datetime
import json
import uuid


def _save(fn):
    db = SessionLocal()
    try:
        fn(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class AutoSOCFlow(Flow[PipelineState]):

    @start()
    async def run_triage(self):
        print(f"[triage] starting for incident {self.state.incident_id}")
        result = await triage_agent(
            self.state.raw_log,
            self.state.environment_context,
            self.state.incident_context
        )
        result['incident_id'] = self.state.incident_id
        self.state.triage_result = result

        incident_id = self.state.incident_id
        raw_log = self.state.raw_log
        incident_context = self.state.incident_context

        _save(lambda db: (
            db.add(Incident(
                id=incident_id,
                title=result.get("title", "unknown"),
                severity=result.get("priority", "p2").lower(),
                status="open",
                raw_log=raw_log,
                incident_context=incident_context,
                created_at=datetime.utcnow()
            )) or
            db.add(Finding(
                id=str(uuid.uuid4()),
                incident_id=incident_id,
                agent="triage",
                content=json.dumps(result),
                created_at=datetime.utcnow()
            ))
        ))

    @router(run_triage)
    async def route_after_triage(self):
        if self.state.triage_result.get('human_review'):
            print(f"[pipeline] stopping at triage — human review required: {self.state.triage_result.get('human_review_reason')}")
            self.state.stopped_at_triage = True
            return 'stop'
        return 'proceed'

    @listen('proceed')
    async def run_investigation(self):
        print(f"[investigation] starting for incident {self.state.incident_id}")
        result = await investigation_agent(
            self.state.raw_log,
            self.state.triage_result,
            self.state.environment_context,
            self.state.incident_context
        )
        result['incident_id'] = self.state.incident_id
        self.state.investigation_result = result

        incident_id = self.state.incident_id
        _save(lambda db: db.add(Finding(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            agent="investigation",
            content=json.dumps(result),
            created_at=datetime.utcnow()
        )))

    @listen(run_investigation)
    async def run_response(self):
        print(f"[response] starting for incident {self.state.incident_id}")
        result = await response_agent(
            self.state.triage_result,
            self.state.investigation_result,
            self.state.environment_context,
            self.state.incident_context
        )
        result['incident_id'] = self.state.incident_id
        self.state.response_result = result

        incident_id = self.state.incident_id
        _save(lambda db: db.add(Finding(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            agent="response",
            content=json.dumps(result),
            created_at=datetime.utcnow()
        )))

    @listen(run_response)
    async def run_report(self):
        print(f"[report] starting for incident {self.state.incident_id}")
        result = await report_agent(
            self.state.triage_result,
            self.state.investigation_result,
            self.state.response_result,
            self.state.environment_context,
            self.state.incident_context
        )
        result['incident_id'] = self.state.incident_id
        self.state.report_result = result

        incident_id = self.state.incident_id
        _save(lambda db: db.add(Report(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            content=json.dumps(result),
            created_at=datetime.utcnow()
        )))
