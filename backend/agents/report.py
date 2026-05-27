from crewai import Agent, Task, Crew
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

#claude as the llm for this agent
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

#exact output structure crewai will enforce
class ReportOutput(BaseModel):
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

#the report agent definition
report_analyst = Agent(
    role="Incident Report Specialist",
    goal="""produce clear accurate and complete incident reports for two audiences:

    executive summary:
    - 3 to 4 sentences maximum
    - no technical jargon
    - what happened, what was affected, what was done about it
    - written for a ciso or board member who needs the big picture fast

    technical summary:
    - full technical detail
    - every indicator every affected asset every action taken
    - written for a security engineer who needs to understand exactly what happened
    - references mitre att&ck tactics where relevant

    good report looks like this:
    - executive summary is jargon free and under 4 sentences
    - technical summary covers every finding from triage and investigation
    - timeline is chronological and complete
    - every response action is documented
    - lessons learned are specific not generic
    - recommendations are actionable not vague
    - open items are explicitly listed so nothing gets missed
    - confidence above 80 means report is ready to send
    - confidence below 60 means flag sections that need more evidence
    """,
    backstory="""you are a senior incident report writer with 10 years of experience
    producing post incident reports for fortune 500 companies. you know how to
    translate complex technical findings into clear language for executives while
    keeping full technical detail for engineers. your reports have been used as
    evidence in legal proceedings and regulatory audits.""",
    llm=llm,
    verbose=True
)

async def report_agent(
    triage_result: dict,
    investigation_result: dict,
    response_result: dict
) -> dict:
    #task for the report agent
    report_task = Task(
        description=f"""
        produce a complete incident report from the findings below.
        
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
        
        your job:
        1. write an executive summary in plain english under 4 sentences
        2. write a full technical summary with all findings
        3. compile a complete chronological timeline
        4. list all affected assets
        5. write an attack narrative explaining what happened start to finish
        6. document every response action taken
        7. extract lessons learned that are specific to this incident
        8. write actionable recommendations not generic ones
        9. list any open items that still need resolution
        10. justify the severity level assigned
        
        executive summary must have zero technical jargon.
        technical summary must reference every finding.
        lessons learned must be specific to this incident not generic advice.
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

    result = crew.kickoff()

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
            "open_items": ["report generation failed review manually"],
            "severity_justification": "unknown",
            "authored_by": "autosoc report agent",
            "report_confidence": 0
        }