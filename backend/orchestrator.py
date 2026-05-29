from agents.triage import triage_agent
from agents.investigation import investigation_agent
from agents.response import response_agent
from agents.report import report_agent
from db.database import SessionLocal, Incident, Finding, Report
from datetime import datetime
import uuid
import json

#runs all 4 agents in sequence and stores results in db
async def run_pipeline(raw_log: str, source: str = "manual") -> dict:
    db = SessionLocal()
    incident_id = str(uuid.uuid4())

    try:
        #step 1 triage
        print(f"[triage] starting for incident {incident_id}")
        triage_result = await triage_agent(raw_log)

        #save incident to db after triage
        incident = Incident(
            id=incident_id,
            title=triage_result.get("title", "unknown"),
            severity=triage_result.get("priority", "p2"),
            status="investigating",
            raw_log=raw_log,
            created_at=datetime.utcnow()
        )
        db.add(incident)
        db.commit()

        #save triage finding as proper json
        db.add(Finding(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            agent="triage",
            content=json.dumps(triage_result),
            created_at=datetime.utcnow()
        ))
        db.commit()

        #step 2 investigation
        print(f"[investigation] starting for incident {incident_id}")
        investigation_result = await investigation_agent(raw_log, triage_result)

        #save investigation finding as proper json
        db.add(Finding(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            agent="investigation",
            content=json.dumps(investigation_result),
            created_at=datetime.utcnow()
        ))
        db.commit()

        #step 3 response
        print(f"[response] starting for incident {incident_id}")
        response_result = await response_agent(triage_result, investigation_result)

        #save response finding as proper json
        db.add(Finding(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            agent="response",
            content=json.dumps(response_result),
            created_at=datetime.utcnow()
        ))
        db.commit()

        #step 4 report
        print(f"[report] starting for incident {incident_id}")
        report_result = await report_agent(triage_result, investigation_result, response_result)

        #save final report as proper json
        db.add(Report(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            content=json.dumps(report_result),
            created_at=datetime.utcnow()
        ))

        #mark incident as complete
        incident.status = "complete"
        db.commit()

        print(f"[pipeline] complete for incident {incident_id}")

        return {
            "incident_id": incident_id,
            "triage": triage_result,
            "investigation": investigation_result,
            "response": response_result,
            "report": report_result
        }

    except Exception as e:
        #rollback db on any failure
        print(f"[pipeline] error: {e}")
        db.rollback()
        raise e

    finally:
        db.close()