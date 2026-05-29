from agents.triage import triage_agent
from agents.investigation import investigation_agent
from agents.response import response_agent
from agents.report import report_agent
from db.database import SessionLocal, Incident, Finding, Report
from datetime import datetime
import uuid
import json

def _save(fn):
    """open a fresh session, run fn(db), commit, close — survives Neon idle drops"""
    db = SessionLocal()
    try:
        fn(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

#runs all 4 agents in sequence and stores results in db
async def run_pipeline(raw_log: str, source: str = "manual") -> dict:
    incident_id = str(uuid.uuid4())

    try:
        #step 1 triage
        print(f"[triage] starting for incident {incident_id}")
        triage_result = await triage_agent(raw_log)

        _save(lambda db: (
            db.add(Incident(
                id=incident_id,
                title=triage_result.get("title", "unknown"),
                severity=triage_result.get("priority", "p2").lower(),
                status="open",
                raw_log=raw_log,
                created_at=datetime.utcnow()
            )) or
            db.add(Finding(
                id=str(uuid.uuid4()),
                incident_id=incident_id,
                agent="triage",
                content=json.dumps(triage_result),
                created_at=datetime.utcnow()
            ))
        ))

        #step 2 investigation
        print(f"[investigation] starting for incident {incident_id}")
        investigation_result = await investigation_agent(raw_log, triage_result)

        _save(lambda db: db.add(Finding(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            agent="investigation",
            content=json.dumps(investigation_result),
            created_at=datetime.utcnow()
        )))

        #step 3 response
        print(f"[response] starting for incident {incident_id}")
        response_result = await response_agent(triage_result, investigation_result)

        _save(lambda db: db.add(Finding(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            agent="response",
            content=json.dumps(response_result),
            created_at=datetime.utcnow()
        )))

        #step 4 report
        print(f"[report] starting for incident {incident_id}")
        report_result = await report_agent(triage_result, investigation_result, response_result)

        _save(lambda db: db.add(Report(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            content=json.dumps(report_result),
            created_at=datetime.utcnow()
        )))

        print(f"[pipeline] complete for incident {incident_id}")

        return {
            "incident_id": incident_id,
            "triage": triage_result,
            "investigation": investigation_result,
            "response": response_result,
            "report": report_result
        }

    except Exception as e:
        print(f"[pipeline] error: {e}")
        raise e