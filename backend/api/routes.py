from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.database import get_db, Incident, Finding, Report
from models.schemas import AlertInput, AnalysisResponse, StatusUpdate
from orchestrator import run_pipeline

router = APIRouter()

#submit a new alert and run the full pipeline
@router.post("/analyse", response_model=AnalysisResponse)
async def analyse_alert(alert: AlertInput, db: Session = Depends(get_db)):
    try:
        result = await run_pipeline(
            raw_log=alert.raw_log,
            source=alert.source
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#get all incidents
@router.get("/incidents")
async def get_incidents(db: Session = Depends(get_db)):
    try:
        incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#get a single incident by id
@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str, db: Session = Depends(get_db)):
    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="incident not found")
        return incident
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#get all findings for an incident
@router.get("/incidents/{incident_id}/findings")
async def get_findings(incident_id: str, db: Session = Depends(get_db)):
    try:
        findings = db.query(Finding).filter(
            Finding.incident_id == incident_id
        ).order_by(Finding.created_at.asc()).all()
        return findings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#get the report for an incident
@router.get("/incidents/{incident_id}/report")
async def get_report(incident_id: str, db: Session = Depends(get_db)):
    try:
        report = db.query(Report).filter(
            Report.incident_id == incident_id
        ).first()
        if not report:
            raise HTTPException(status_code=404, detail="report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#manually resolve or reopen an incident
@router.patch("/incidents/{incident_id}/status")
async def update_status(incident_id: str, body: StatusUpdate, db: Session = Depends(get_db)):
    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="incident not found")
        if body.status not in ("open", "resolved"):
            raise HTTPException(status_code=400, detail="status must be 'open' or 'resolved'")
        incident.status = body.status
        db.commit()
        return incident
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#get all incidents by priority
@router.get("/incidents/priority/{priority}")
async def get_incidents_by_priority(priority: str, db: Session = Depends(get_db)):
    try:
        incidents = db.query(Incident).filter(
            func.lower(Incident.severity) == priority.lower()
        ).order_by(Incident.created_at.desc()).all()
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#get dashboard stats
@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    try:
        total = db.query(Incident).count()
        open_incidents = db.query(Incident).filter(Incident.status.in_(["open", "complete"])).count()
        resolved = db.query(Incident).filter(Incident.status == "resolved").count()
        p0 = db.query(Incident).filter(func.lower(Incident.severity) == "p0", Incident.status != "resolved").count()
        p1 = db.query(Incident).filter(func.lower(Incident.severity) == "p1").count()
        p2 = db.query(Incident).filter(func.lower(Incident.severity) == "p2").count()
        p3 = db.query(Incident).filter(func.lower(Incident.severity) == "p3").count()
        p4 = db.query(Incident).filter(func.lower(Incident.severity) == "p4").count()

        return {
            "total": total,
            "open": open_incidents,
            "resolved": resolved,
            "by_priority": {
                "p0": p0,
                "p1": p1,
                "p2": p2,
                "p3": p3,
                "p4": p4
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))