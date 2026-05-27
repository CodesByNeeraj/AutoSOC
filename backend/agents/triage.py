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
class TriageOutput(BaseModel):
    #short description of what happened
    title: str    
    #p0 p1 p2 p3 p4        
    priority: str 
    #malware intrusion anomaly phishing data exfiltration other        
    category: str  
    #2 to 3 sentences explaining what happened       
    summary: str  
    #every suspicious thing found in the log        
    indicators: List[str] 
    #0 to 100
    confidence: int       
    needs_investigation: bool
    #true if confidence below 60
    human_review: bool    
    #one sentence explaining priority choice
    justification: str    

#the triage agent definition
triage_analyst = Agent(
    role="Security Triage Specialist",
    goal="""classify and prioritise every incoming security alert using this scale:
    
    p0 = active breach in progress, data loss happening right now, immediate action needed
    p1 = confirmed threat, no active damage yet but will escalate fast without action
    p2 = suspicious activity, likely malicious, needs investigation within 2 hours
    p3 = anomaly detected, could be benign, investigate within 24 hours
    p4 = informational, low risk, log and monitor only
    
    good triage looks like this:
    - correct priority level with clear justification
    - no false positives on p0 and p1
    - every indicator in the log is accounted for
    - confidence score above 80 means you found enough evidence
    - confidence below 60 means flag for human review
    - never ignore an indicator even if it seems minor
    - if something does not add up say so explicitly
    """,
    backstory="""you are a senior security analyst with 10 years of experience
    in a soc environment. you have seen every type of security alert imaginable
    and can quickly determine what is real and what is noise. you are fast,
    accurate and never miss a critical threat.""",
    llm=llm,
    verbose=True
)

async def triage_agent(raw_log: str) -> dict:
    #task for the triage agent
    triage_task = Task(
        description=f"""
        analyse the following security alert or log and provide a structured triage.
        
        raw log:
        {raw_log}
        
        priority scale:
        p0 = active breach right now
        p1 = confirmed threat not yet causing damage
        p2 = suspicious activity needs investigation within 2 hours
        p3 = anomaly investigate within 24 hours
        p4 = informational log and monitor only
        
        set human review to true if confidence is below 60.
        justify your priority choice in one sentence.
        account for every indicator you find even minor ones.
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
        return result.json_dict
    except Exception as e:
        print(f"[triage] output parse error: {e}")
        return {
            "title": "parse error",
            "priority": "p2",
            "category": "other",
            "summary": str(result),
            "indicators": [],
            "confidence": 0,
            "needs_investigation": True,
            "human_review": True,
            "justification": "parse error occurred flagging for human review"
        }