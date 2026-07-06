from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

llm = LLM(
    model="anthropic/claude-sonnet-5",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=16000
)
#exact output structure
class InvestigationOutput(BaseModel):
    incident_id: str = ""
    attack_pattern: str = "unknown"
    mitre_tactics: List[str] = []
    timeline: List[str] = []
    affected_assets: List[str] = []
    blast_radius: str = "unknown"
    root_cause: str = "unknown"
    evidence_gaps: List[str] = []
    human_review: bool = False
    escalate: bool = False
    summary: str = ""

#the investigation agent definition
investigation_analyst = Agent(
    role="Security Investigation Analyst",
    goal="investigate triaged security incidents to determine what happened, how far it spread, and what caused it.",
    backstory="""you are a senior threat hunter with 12 years of experience investigating security incidents.
    you think like an attacker, know every common attack pattern, and never jump to conclusions without evidence.
    you are methodical, thorough, and always follow the evidence even when it leads somewhere unexpected.""",
    llm=llm,
    verbose=True
)

async def investigation_agent(raw_log: str, triage_result: dict, environment_context: str = "", incident_context: str = "") -> dict:
    context_block = ""
    if environment_context:
        context_block += f"\nenvironment context (treat as ground truth):\n{environment_context}\n"
    if incident_context:
        context_block += f"\nincident context provided by analyst:\n{incident_context}\n"

    # task for the investigation agent
    investigation_task = Task(
        description=f"""
        you are conducting a deep investigation on a triaged security incident. your job is to tell the full story of what happened — from first indicator to current state — with evidence supporting every claim.
        {context_block}
        original log:
        {raw_log}

        triage findings:
        priority: {triage_result.get('priority')}
        category: {triage_result.get('category')}
        indicators: {triage_result.get('indicators')}
        summary: {triage_result.get('summary')}

        work through this in order:

        step 1 — build a chronological timeline.
        sequence every event you can find in the log with timestamps where available.
        label each event: [confirmed] (direct evidence in the log) or [inferred] (logical conclusion from evidence).
        never present an inference as a confirmed fact.

        step 2 — identify the attack pattern.
        what technique was used? map to a known pattern if possible (credential stuffing, lateral movement, c2 beaconing, privilege escalation, data staging, etc.).
        explain how the evidence supports this pattern specifically.

        step 3 — map to mitre att&ck tactics.
        only list tactics that have direct evidence in the log. do not list tactics that could theoretically apply.

        step 4 — determine every affected asset.
        list every host, user account, service, or data store with evidence of involvement.
        distinguish: directly compromised / potentially compromised / at risk but not yet touched.

        step 5 — assess blast radius:
        contained: single asset affected, no evidence of spread
        spreading: multiple assets affected or active lateral movement detected
        critical: domain-wide access, confirmed data exfiltration, or ransomware deployment
        base this strictly on evidence — do not guess.

        step 6 — establish root cause.
        what enabled this attack? go beyond what happened to why it was possible.
        bad: "attacker used credential stuffing"
        good: "account svc_backup had no mfa and its password appeared in the rockyou2024 breach list, enabling successful authentication from an external ip"
        if you cannot determine root cause from available evidence, say so explicitly.

        step 7 — list evidence gaps.
        what specific information is missing that would change your assessment?
        bad: "more logs needed"
        good: "cannot determine if lateral movement from WS-042 to DC-01 succeeded — dc-01 authentication logs are not present in this log set"
        list 3-6 gaps maximum.

        step 8 — set escalate to true if blast radius is spreading or critical.
        set human_review to true if you are not confident in your blast radius or root cause — for example if key logs are missing, evidence contradicts itself, or you had to guess at more than one major conclusion.

        quality bar: a threat hunter who has not seen this log should be able to reproduce your timeline from your output alone and reach the same conclusions. every claim must have an evidence citation.
        """,
        agent=investigation_analyst,
        expected_output="a valid json object matching the investigation output schema",
        output_json=InvestigationOutput
    )

    # run the crew with just the investigation agent
    crew = Crew(
        agents=[investigation_analyst],
        tasks=[investigation_task],
        verbose=True
    )

    result = await crew.kickoff_async()

    # return as dict for the rest of the pipeline
    try:
        return result.json_dict
    except Exception as e:
        print(f"[investigation] output parse error: {e}")
        return {
            "incident_id": triage_result.get("title", "unknown"),
            "attack_pattern": "unknown",
            "mitre_tactics": [],
            "timeline": [],
            "affected_assets": [],
            "blast_radius": "unknown",
            "root_cause": "could not determine",
            "evidence_gaps": ["parse error occurred"],
            "human_review": True,
            "escalate": True,
            "summary": str(result)
        }
