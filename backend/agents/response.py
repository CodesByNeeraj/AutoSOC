from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

#claude as the llm for this agent
llm = LLM(
    model="anthropic/claude-sonnet-5",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=16000
)

#exact output structure crewai will enforce
class ResponseOutput(BaseModel):
    incident_id: str = ""
    immediate_actions: List[str] = []
    short_term_actions: List[str] = []
    long_term_actions: List[str] = []
    containment_strategy: str = ""
    eradication_steps: List[str] = []
    recovery_steps: List[str] = []
    notify_teams: List[str] = []
    escalate_to_human: bool = False
    estimated_resolution_time: str = "unknown"
    human_review: bool = False
    summary: str = ""

#the response agent definition
response_analyst = Agent(
    role="Security Response Specialist",
    goal="recommend specific, prioritised response actions to contain, eradicate, and recover from security incidents.",
    backstory="""you are a senior incident responder with 15 years of experience handling security incidents at fortune 500 companies.
    you know exactly what to do in the first 15 minutes of an incident.
    you are calm under pressure, decisive, and always prioritise containment before eradication.""",
    llm=llm,
    verbose=True
)

async def response_agent(triage_result: dict, investigation_result: dict, environment_context: str = "", incident_context: str = "") -> dict:
    context_block = ""
    if environment_context:
        context_block += f"\nenvironment context (treat as ground truth):\n{environment_context}\n"
    if incident_context:
        context_block += f"\nincident context provided by analyst:\n{incident_context}\n"

    #task for the response agent
    response_task = Task(
        description=f"""
        you are recommending response actions for a confirmed or suspected security incident. every action must be specific, tied to a finding, and executable by an analyst without further clarification.
        {context_block}
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

        work through this in order:

        step 1 — read all findings before recommending anything.
        your actions must address this specific incident, not generic security advice.

        step 2 — immediate actions (within 15 minutes).
        these are critical — do them now, ask questions later.
        focus on: isolate affected hosts, block malicious ips/domains, revoke compromised credentials, preserve volatile evidence.
        name the specific asset or credential in every action.
        bad: "isolate affected systems"
        good: "isolate workstation WS-042 by disabling its switchport or applying quarantine VLAN — do not power it off, preserve RAM for forensics"

        step 3 — short-term actions (within 2 hours).
        post-containment: scan for lateral movement, patch exploited vulnerabilities, notify affected users.
        each action must reference a specific finding from the investigation.

        step 4 — long-term actions (within 24-72 hours).
        root cause remediation: policy updates, infrastructure hardening, forensic investigation.
        these address why the attack was possible, not just what happened.

        step 5 — containment strategy.
        one paragraph describing the overall containment approach for this specific incident.
        tie it to the blast radius: contained vs spreading vs critical each requires a different strategy.

        step 6 — eradication steps.
        ordered steps to fully remove the threat from the environment.
        include validation — how will you know it is gone?

        step 7 — recovery steps.
        how to restore normal operations after eradication.
        include verification steps before restoring — do not restore until eradication is confirmed.

        step 8 — notify teams based on category:
        malware → it security, security management
        data_exfiltration → legal, compliance, security management, affected data owners
        intrusion → it security, infrastructure, security management
        phishing → it security, affected users, hr if credentials were compromised
        anomaly → it security only until category is confirmed
        custom category (any name the triage agent assigned that is not one of the above) → use your judgement based on what the category name describes. for example, insider_threat → it security, hr, legal, security management. supply_chain_compromise → it security, security management, vendor management. misconfiguration → it security, infrastructure. when in doubt, default to it security and security management.

        step 9 — set escalate_to_human to true if priority is p0 or p1, blast radius is critical, or root cause suggests a systemic vulnerability.
        set human_review to true if the recommended actions are based on inferred rather than confirmed findings, or if critical asset details are unknown.

        step 10 — estimate resolution time realistically.
        base it on the blast radius and the number of affected assets.

        quality bar: a junior analyst receiving your output should be able to execute every action without asking a single clarifying question.
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
            "human_review": True,
            "summary": str(result)
        }
