import re
import json
import uuid
import logging
from typing import List, Dict, Any, Optional

from backend.app.models.schemas import Subclaim, ExtractedEntities
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

SUBCLAIM_SYSTEM_PROMPT = """You are a senior cybersecurity intelligence analyst.
Deconstruct the user's cybersecurity claim or rumor into 1 to 3 distinct atomic subclaims.
For each subclaim, extract:
- subclaim_text: Clear, isolated assertion
- target_org: Target company or institution
- threat_actor: Accused threat actor or group (or null)
- incident_type: Data Breach, Ransomware, Zero-Day, Credential Stuffing, Supply Chain, DDoS, Account Takeover, or General Incident
- affected_product: Affected software, hardware, or service (or null)
- cve: Specific CVE ID if mentioned (or null)
- allegation: The precise technical accusation

Respond strictly in valid JSON format:
{
  "subclaims": [
    {
      "subclaim_text": "...",
      "target_org": "...",
      "threat_actor": null,
      "incident_type": "...",
      "affected_product": null,
      "cve": null,
      "allegation": "..."
    }
  ]
}"""

async def decompose_claim_with_llm(claim: str) -> Optional[List[Subclaim]]:
    """Attempts subclaim decomposition using configured LLM APIs (Gemini or OpenAI)."""
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{SUBCLAIM_SYSTEM_PROMPT}\n\nClaim to decompose:\n\"{claim}\"",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            if response.text:
                data = json.loads(response.text)
                subclaims = []
                for item in data.get("subclaims", []):
                    subclaims.append(Subclaim(
                        subclaim_id=f"sub_{uuid.uuid4().hex[:8]}",
                        subclaim_text=item.get("subclaim_text", claim),
                        target_org=item.get("target_org"),
                        threat_actor=item.get("threat_actor"),
                        incident_type=item.get("incident_type", "Cybersecurity Incident"),
                        affected_product=item.get("affected_product"),
                        cve=item.get("cve"),
                        allegation=item.get("allegation", item.get("subclaim_text", claim))
                    ))
                if subclaims:
                    return subclaims
        except Exception as e:
            logger.debug(f"LLM subclaim decomposition failed: {e}")

    return None

def decompose_claim_heuristics(claim: str, entities: ExtractedEntities) -> List[Subclaim]:
    """
    Deterministic rule-based subclaim decomposition.
    Separates complex claims into primary core allegation and impact/attribution components.
    """
    from backend.app.services.claim_extraction import KNOWN_THREAT_ACTORS
    
    claim_lower = claim.lower()
    detected_actor = None
    for actor in KNOWN_THREAT_ACTORS:
        if re.search(r"\b" + re.escape(actor) + r"\b", claim_lower):
            detected_actor = actor.upper() if len(actor) <= 4 else actor.title()
            break

    cve_match = re.search(r"CVE-\d{4}-\d{4,7}", claim, re.IGNORECASE)
    cve_id = cve_match.group(0).upper() if cve_match else None
    primary_prod = entities.affected_products[0] if entities.affected_products else None

    subclaims = []
    
    # Check for conjunctions or compound statements
    clauses = re.split(r"\b(?:and|leading to|resulting in|caused by|after|alleging that)\b", claim, flags=re.IGNORECASE)
    cleaned_clauses = [c.strip() for c in clauses if len(c.strip()) > 15]

    if len(cleaned_clauses) > 1:
        for idx, clause in enumerate(cleaned_clauses[:3]):
            subclaims.append(Subclaim(
                subclaim_id=f"sub_{uuid.uuid4().hex[:8]}",
                subclaim_text=clause,
                target_org=entities.organisation if idx == 0 else None,
                threat_actor=detected_actor,
                incident_type=entities.incident_type,
                affected_product=primary_prod,
                cve=cve_id,
                allegation=clause
            ))
    else:
        # Single primary atomic subclaim
        subclaims.append(Subclaim(
            subclaim_id=f"sub_{uuid.uuid4().hex[:8]}",
            subclaim_text=claim.strip(),
            target_org=entities.organisation,
            threat_actor=detected_actor,
            incident_type=entities.incident_type,
            affected_product=primary_prod,
            cve=cve_id,
            allegation=entities.allegation
        ))

    return subclaims

async def decompose_claim_into_subclaims(claim: str, entities: ExtractedEntities) -> List[Subclaim]:
    """Unified entry point for claim decomposition."""
    subclaims = await decompose_claim_with_llm(claim)
    if not subclaims:
        subclaims = decompose_claim_heuristics(claim, entities)
    return subclaims

def answer_eight_investigative_questions(
    subclaim: Subclaim,
    supporting_passages: List[str],
    contradicting_passages: List[str],
    official_status: str,
    verdict: str
) -> Dict[str, str]:
    """
    Formulates evidence-grounded answers for the 8 mandatory investigative questions per subclaim:
    1. What happened?
    2. Who was affected?
    3. Which component was affected?
    4. When did it happen?
    5. Who disclosed it?
    6. What technical evidence exists?
    7. Was exploitation confirmed?
    8. Was organizational compromise confirmed?
    """
    answers = {}
    
    # 1. What happened?
    answers["what_happened"] = f"Alleged {subclaim.incident_type.lower()}: '{subclaim.allegation}'."
    
    # 2. Who was affected?
    answers["who_affected"] = subclaim.target_org or "Reported target organization or its user accounts."
    
    # 3. Which component was affected?
    answers["component_affected"] = subclaim.affected_product or (f"Vulnerability {subclaim.cve}" if subclaim.cve else "Perimeter or customer accounts.")
    
    # 4. When did it happen?
    answers["when_happened"] = "Referenced in recent technical disclosures and security advisories."
    
    # 5. Who disclosed it?
    answers["who_disclosed"] = official_status
    
    # 6. What technical evidence exists?
    if supporting_passages:
        answers["technical_evidence"] = f"Disclosed evidence excerpts: '{supporting_passages[0][:150]}...'"
    elif contradicting_passages:
        answers["technical_evidence"] = f"Refutation excerpts: '{contradicting_passages[0][:150]}...'"
    else:
        answers["technical_evidence"] = "No direct public forensic evidence or packet capture disclosed."
        
    # 7. Was exploitation confirmed?
    if verdict in ("VERIFIED", "LIKELY TRUE") and any("exploit" in p.lower() for p in supporting_passages):
        answers["exploitation_confirmed"] = "Yes, active exploitation was corroborated in public threat intelligence."
    elif verdict == "FALSE":
        answers["exploitation_confirmed"] = "No, claim has been authoritatively refuted."
    else:
        answers["exploitation_confirmed"] = "Unconfirmed or pending formal technical post-mortem."

    # 8. Was organizational compromise confirmed?
    if verdict == "MISLEADING":
        answers["compromise_confirmed"] = "Misattributed: Central systems were not compromised; customer accounts or third-party suppliers were impacted."
    elif verdict == "VERIFIED":
        answers["compromise_confirmed"] = "Confirmed organizational security incident verified by authoritative sources."
    elif verdict == "FALSE":
        answers["compromise_confirmed"] = "No organizational compromise occurred."
    else:
        answers["compromise_confirmed"] = "Unverified based on collected public intelligence."

    return answers
