from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

#claude as the llm for this agent
llm = LLM(
    model="anthropic/claude-sonnet-4-6",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=16000
)

#exact output structure crewai will enforce
class ReportOutput(BaseModel):
    incident_id: str = ""
    executive_summary: str = ""
    technical_summary: str = ""
    timeline: List[str] = []
    affected_assets: List[str] = []
    attack_narrative: str = ""
    response_actions_taken: List[str] = []
    lessons_learned: List[str] = []
    recommendations: List[str] = []
    open_items: List[str] = []

#the report agent definition
report_analyst = Agent(
    role="Incident Report Specialist",
    goal="produce accurate incident reports for both executive and technical audiences from all investigation findings.",
    backstory="""you are a senior incident report writer with 10 years of experience producing post-incident reports for fortune 500 companies.
    you translate complex technical findings into clear language for executives while keeping full technical detail for engineers.
    your reports have been used as evidence in regulatory audits.""",
    llm=llm,
    verbose=True
)

async def report_agent(
    triage_result: dict,
    investigation_result: dict,
    response_result: dict,
    environment_context: str = "",
    incident_context: str = ""
) -> dict:
    context_block = ""
    if environment_context:
        context_block += f"\nenvironment context (treat as ground truth):\n{environment_context}\n"
    if incident_context:
        context_block += f"\nincident context provided by analyst:\n{incident_context}\n"

    #task for the report agent
    report_task = Task(
        description=f"""
        you are producing the final incident report. this document will be read by two different audiences: executives who need to make decisions, and engineers who need to understand exactly what happened. it must serve both without compromise.
        {context_block}
        triage findings:
        priority: {triage_result.get('priority')}
        category: {triage_result.get('category')}
        indicators: {triage_result.get('indicators')}
        summary: {triage_result.get('summary')}
        justification: {triage_result.get('justification')}

        investigation findings:
        attack pattern: {investigation_result.get('attack_pattern')}
        mitre tactics: {investigation_result.get('mitre_tactics')}
        timeline: {investigation_result.get('timeline')}
        affected assets: {investigation_result.get('affected_assets')}
        blast radius: {investigation_result.get('blast_radius')}
        root cause: {investigation_result.get('root_cause')}
        evidence gaps: {investigation_result.get('evidence_gaps')}

        response findings:
        immediate actions: {response_result.get('immediate_actions')}
        short term actions: {response_result.get('short_term_actions')}
        long term actions: {response_result.get('long_term_actions')}
        containment strategy: {response_result.get('containment_strategy')}
        notify teams: {response_result.get('notify_teams')}
        estimated resolution time: {response_result.get('estimated_resolution_time')}

        work through this in order:

        step 1 — executive summary.
        3-4 sentences maximum. zero technical jargon.
        answer: what happened, what was the impact, what was done, what is the current status.
        test: a board member with no security background must understand this completely.
        bad: "a threat actor leveraged credential stuffing to initiate c2 beaconing"
        good: "an unauthorised person gained access to an employee account and attempted to communicate with an external server. the account has been locked, the connection blocked, and no data was confirmed to have left the organisation."

        step 2 — technical summary.
        3-5 sentences maximum. written for a security engineer.
        cover: attack technique, key indicators (IPs, accounts, tools), affected assets, and mitre tactics.
        do not repeat the full timeline or repeat content from other fields — those have their own sections.

        step 3 — compile the complete chronological timeline.
        use the investigation timeline as a base. add context from triage or response if it adds to the sequence.

        step 4 — attack narrative.
        3-5 sentences maximum. tell the story of the attack from start to finish.
        be explicit about what is confirmed vs inferred. do not repeat the timeline.

        step 5 — response actions taken.
        document every recommended action from the response agent.

        step 6 — lessons learned.
        specific to this incident — not generic security advice.
        bad: "implement mfa across all systems"
        good: "account svc_backup had no mfa and was reachable from external ips — this specific gap enabled the initial access"
        list 2-4 specific lessons.

        step 7 — recommendations.
        actionable items that address the root cause and prevent recurrence.
        each recommendation must reference a specific finding that motivated it.

        step 8 — open items.
        what is still unresolved? include evidence gaps from the investigation that still need answers.

        quality bar: the executive summary must be shareable with leadership immediately. the technical summary must be detailed enough for a forensic handoff.
        """,
        agent=report_analyst,
        expected_output="a valid json object matching the report output schema",
        output_json=ReportOutput
    )

    #run the crew with just the report agent
    crew = Crew(
        agents=[report_analyst],
        tasks=[report_task],
        verbose=True
    )

    result = await crew.kickoff_async()

    #return as dict for the rest of the pipeline
    try:
        return result.json_dict
    except Exception as e:
        print(f"[report] output parse error: {e}")
        return {
            "incident_id": triage_result.get("title", "unknown"),
            "executive_summary": "report generation failed",
            "technical_summary": str(result),
            "timeline": [],
            "affected_assets": [],
            "attack_narrative": "unknown",
            "response_actions_taken": [],
            "lessons_learned": [],
            "recommendations": [],
            "open_items": ["report generation failed review manually"]
        }
