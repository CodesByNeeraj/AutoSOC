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
class TriageOutput(BaseModel):
    title: str = "unknown"
    priority: str = "p2"
    category: str = "unknown"
    summary: str = ""
    indicators: List[str] = []
    needs_investigation: bool = True
    human_review: bool = False
    human_review_reason: str = ""
    justification: str = ""

#the triage agent definition
triage_analyst = Agent(
    role="Security Triage Specialist",
    goal="classify and prioritise every incoming security alert by severity and produce a structured triage with indicators and confidence gaps.",
    backstory="""you are a senior security analyst with 10 years of experience in a soc environment.
    you have seen every type of security alert imaginable and can quickly determine what is real and what is noise.
    you are fast, accurate, and never miss a critical threat.""",
    llm=llm,
    verbose=True
)

async def triage_agent(raw_log: str, environment_context: str = "", incident_context: str = "") -> dict:
    context_block = ""
    if environment_context:
        context_block += f"\nenvironment context (treat as ground truth):\n{environment_context}\n"
    if incident_context:
        context_block += f"\nincident context provided by analyst:\n{incident_context}\n"

    #task for the triage agent
    triage_task = Task(
        description=f"""
        you are performing first-pass triage on a new security alert. your output is the foundation for all subsequent investigation and response — accuracy here matters most.
        {context_block}
        raw log:
        {raw_log}

        work through this in order:

        step 1 — read the full log before making any judgement. do not skim. every line matters.

        step 2 — extract all indicators of compromise.
        pull out every ip address, domain, user account, process name, file path, hash, or port number that appears.
        include ones that seem benign — they matter for correlation later.
        if an indicator appears multiple times, note the frequency.

        step 3 — categorise the incident type:
        malware: code executing without authorisation (suspicious processes, unusual executables, persistence mechanisms)
        intrusion: unauthorised access (failed/successful logins from unexpected sources, privilege escalation)
        anomaly: unusual behaviour without clear malicious intent yet
        phishing: social engineering or credential harvesting
        data_exfiltration: data leaving the network without authorisation
        if none of the above fit, do not use "other" — write a short specific category name that accurately describes what this is (e.g. "insider_threat", "supply_chain_compromise", "misconfiguration")

        step 4 — assign a priority:
        p0: active breach in progress right now — data loss happening or imminent, every second counts
        p1: confirmed threat — damage has not started yet but will escalate quickly without action
        p2: suspicious activity — likely malicious based on evidence, investigate within 2 hours
        p3: anomaly detected — could be benign, investigate within 24 hours
        p4: informational — log and monitor only

        calibration guidance:
        only assign p0 if you see active exfiltration, active lateral movement, or confirmed ransomware execution
        only assign p1 if there is confirmed compromise but no active damage yet
        when in doubt between p2 and p3, choose p2 — over-triaging is safer than missing a real threat
        never assign p0 or p1 from a single indicator alone — require corroborating evidence

        step 5 — write a 2-3 sentence summary in plain english.
        what happened, what systems are involved, what is the risk. a non-technical manager must understand it.

        step 6 — justify your priority in one sentence by citing specific evidence.
        bad: "based on the indicators observed"
        good: "assigned p1 because svchost.exe initiated an outbound connection to known c2 ip 185.220.101.47 after 47 failed logins on the same host".

        step 7 — set needs_investigation to true if priority is p2 or above.
        set human_review to true only if your classification is unreliable — the log is too sparse, malformed, or truncated to classify confidently, there is a single ambiguous indicator with no corroboration, or signals conflict so strongly that two completely different categories are equally plausible.
        do not set human_review because the incident is severe or complex. a clear p0 with strong evidence does not warrant it. severity is not the same as uncertainty.
        if human_review is true, set human_review_reason to one sentence explaining exactly why the classification is uncertain. if human_review is false, leave human_review_reason empty.

        quality bar: a senior analyst reading your output should be able to brief management in 60 seconds and decide whether to escalate without reading the raw log.
        """,
        agent=triage_analyst,
        expected_output="a valid json object matching the triage output schema",
        output_json=TriageOutput
    )

    #run the crew with just the triage agent
    crew = Crew(
        agents=[triage_analyst],
        tasks=[triage_task],
        verbose=True
    )

    result = await crew.kickoff_async()

    #crewai returns pydantic object when output json is set
    #convert to dict for the rest of the pipeline
    try:
        output = result.json_dict
        # normalize priority to plain p0-p4 in case claude returns "P0" or "P0 - active breach"
        raw_priority = output.get("priority", "p2").lower()
        for level in ("p0", "p1", "p2", "p3", "p4"):
            if level in raw_priority:
                output["priority"] = level
                break
        else:
            output["priority"] = "p2"
        return output
    except Exception as e:
        print(f"[triage] output parse error: {e}")
        return {
            "title": "parse error",
            "priority": "p2",
            "category": "other",
            "summary": str(result),
            "indicators": [],
            "needs_investigation": True,
            "human_review": True,
            "justification": "parse error occurred — flagging for human review"
        }
