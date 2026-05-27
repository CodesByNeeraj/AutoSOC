from crewai import Agent, Task, Crew, LLM
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

#claude as the llm for this agent
llm = LLM(
    model="anthropic/claude-sonnet-4-20250514",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

#exact output structure crewai will enforce
class ResponseOutput(BaseModel):
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

#the response agent definition
response_analyst = Agent(
    role="Security Response Specialist",
    goal="""recommend precise response actions for security incidents using this framework:

    immediate actions = must happen within 15 minutes
        isolate affected hosts
        block malicious ips or domains
        revoke compromised credentials
        preserve evidence before it disappears

    short term actions = must happen within 2 hours
        patch exploited vulnerabilities
        scan for lateral movement
        notify affected users
        review access logs

    long term actions = happen within 24 to 72 hours
        full forensic investigation
        policy updates
        security awareness training
        infrastructure hardening

    good response looks like this:
    - actions are specific not vague
    - every affected asset from investigation has a response action
    - containment comes before eradication
    - eradication comes before recovery
    - notify the right teams based on incident category:
        malware = notify it security and management
        data exfiltration = notify legal compliance and management
        intrusion = notify it security and infrastructure
        phishing = notify it security and affected users
    - escalate to human if priority is p0 or p1
    - escalate to human if blast radius is critical
    - confidence above 80 means clear path to resolution
    - confidence below 60 means flag for human review
    """,
    backstory="""you are a senior incident responder with 15 years of experience
    handling security incidents at fortune 500 companies. you know exactly what
    to do in the first 15 minutes of an incident. you are calm under pressure,
    decisive and always prioritise containment before eradication.""",
    llm=llm,
    verbose=True
)

async def response_agent(triage_result: dict, investigation_result: dict) -> dict:
    #task for the response agent
    response_task = Task(
        description=f"""
        recommend response actions for this security incident.
        
        triage findings:
        priority: {triage_result.get('priority')}
        category: {triage_result.get('category')}
        indicators: {triage_result.get('indicators')}
        
        investigation findings:
        attack pattern: {investigation_result.get('attack_pattern')}
        blast radius: {investigation_result.get('blast_radius')}
        affected assets: {investigation_result.get('affected_assets')}
        mitre tactics: {investigation_result.get('mitre_tactics')}
        root cause: {investigation_result.get('root_cause')}
        escalate: {investigation_result.get('escalate')}
        
        your job:
        1. define immediate actions to take within 15 minutes
        2. define short term actions to take within 2 hours
        3. define long term actions to take within 24 to 72 hours
        4. define containment strategy
        5. define eradication steps
        6. define recovery steps
        7. identify which teams to notify based on incident category
        8. set escalate to human if priority is p0 or p1
        9. set escalate to human if blast radius is critical
        10. set human review to true if confidence is below 60
        11. estimate how long resolution will take
        
        actions must be specific not vague.
        containment before eradication.
        eradication before recovery.
        """,
        agent=response_analyst,
        expected_output="a valid json object matching the response output schema",
        output_json=ResponseOutput
    )

    #run the crew with just the response agent
    crew = Crew(
        agents=[response_analyst],
        tasks=[response_task],
        verbose=True
    )

    result = await crew.kickoff_async()

    #return as dict for the rest of the pipeline
    try:
        return result.json_dict
    except Exception as e:
        print(f"[response] output parse error: {e}")
        return {
            "incident_id": triage_result.get("title", "unknown"),
            "immediate_actions": ["escalate to human immediately"],
            "short_term_actions": [],
            "long_term_actions": [],
            "containment_strategy": "unknown",
            "eradication_steps": [],
            "recovery_steps": [],
            "notify_teams": ["it security"],
            "escalate_to_human": True,
            "estimated_resolution_time": "unknown",
            "confidence": 0,
            "human_review": True,
            "summary": str(result)
        }