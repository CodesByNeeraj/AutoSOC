from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os

load_dotenv()

llm = LLM(
    model="anthropic/claude-sonnet-4-20250514",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
#exact output structure
class InvestigationOutput(BaseModel):
    #links back to triage
    incident_id: str
    #what technique was used
    attack_pattern: str    
    #mitre att&ck tactics identified        
    mitre_tactics: List[str]
    #chronological sequence of events       
    timeline: List[str]  
    #hosts users systems impacted          
    affected_assets: List[str] 
    #how far did this spread    
    blast_radius: str   
    #what started this           
    root_cause: str     
    #what we dont know yet           
    evidence_gaps: List[str]    
    #0 to 100   
    confidence: int    
    #true if confidence below 60            
    human_review: bool      
    #true if blast radius is growing       
    escalate: bool 
    #2 to 3 sentence investigation summary                
    summary: str                  

#the investigation agent definition
investigation_analyst = Agent(
    role="Security Investigation Analyst",
    goal="""conduct deep investigation on triaged security incidents using this approach:

    good investigation looks like this:
    - build a complete chronological timeline from the evidence
    - identify the attack pattern and map it to mitre att&ck tactics
    - determine every affected asset host user and system
    - establish root cause not just symptoms
    - identify what we dont know and flag it as evidence gaps
    - blast radius assessment:
        contained = single host or user affected
        spreading = multiple hosts or lateral movement detected  
        critical = domain wide or data exfiltration confirmed
    - confidence above 80 means enough evidence to act
    - confidence below 60 means flag for human review
    - if blast radius is spreading or critical set escalate to true
    - never assume, only report what the evidence shows
    - if evidence contradicts itself say so explicitly
    """,
    backstory="""you are a senior threat hunter with 12 years of experience
    investigating security incidents. you think like an attacker, you know
    every common attack pattern and you never jump to conclusions without
    evidence. you are methodical, thorough and always follow the evidence
    even when it leads somewhere unexpected.""",
    llm=llm,
    verbose=True
)

async def investigation_agent(raw_log: str, triage_result: dict) -> dict:
    # task for the investigation agent
    investigation_task = Task(
        description=f"""
        conduct a deep investigation on this security incident.
        
        original log:
        {raw_log}
        
        triage findings:
        priority: {triage_result.get('priority')}
        category: {triage_result.get('category')}
        indicators: {triage_result.get('indicators')}
        summary: {triage_result.get('summary')}
        
        your job:
        1. build a chronological timeline of events from the evidence
        2. map the attack to mitre att&ck tactics where possible
        3. identify every affected asset
        4. determine blast radius: contained, spreading or critical
        5. find the root cause
        6. flag any gaps in evidence
        7. set escalate to true if blast radius is spreading or critical
        8. set human review to true if confidence is below 60
        
        only report what the evidence shows.
        if evidence is contradictory flag it explicitly.
        do not assume intent without evidence.
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
            "confidence": 0,
            "human_review": True,
            "escalate": True,
            "summary": str(result)
        }