import logging
from typing import Tuple
from backend.app.models.schemas import MathematicalResults, SourceItem

logger = logging.getLogger(__name__)

def determine_verdict(
    math_results: MathematicalResults,
    sources: list[SourceItem],
    has_official_denial: bool = False,
    has_official_confirmation: bool = False
) -> Tuple[str, str]:
    """
    Deterministically computes the investigation verdict based strictly on mathematical
    evidence weights, source credibility, and independent confirmation.
    
    Verdicts:
    - VERIFIED: Authoritative corroboration (official advisory or multiple primary sources)
    - LIKELY TRUE: Strong credible reporting, pending formal post-mortem or advisory
    - FALSE: Explicit contradiction / denial by primary authoritative sources or proof of hoax
    - MISLEADING: Core claim is exaggerated, out of context, or misattributes blame
    - UNVERIFIED: Insufficient independent evidence or unresolved conflicting reports
    """
    E = math_results.weighted_evidence_score
    groups = math_results.independent_source_count
    conf = math_results.confidence_score
    dist = math_results.evidence_distribution
    officials = math_results.official_sources_count

    # 1. Rule out insufficient evidence first -> UNVERIFIED
    if groups < 2 or (dist.supporting_count == 0 and dist.contradicting_count == 0):
        return (
            "UNVERIFIED",
            f"Insufficient independent evidence discovered ({groups} independent cluster(s)). "
            f"No conclusive confirmation or formal denial could be verified from authoritative channels."
        )

    # 2. Check for explicit authoritative denial or debunking -> FALSE
    if has_official_denial or (E <= -0.40 and dist.contradicting_count >= 2):
        return (
            "FALSE",
            f"Claim is refuted with high confidence (weighted score: {E}). "
            f"{dist.contradicting_count} source(s) directly contradict the allegation, including authoritative statements or verification logs."
        )

    # 3. Check for official confirmation or overwhelming consensus -> VERIFIED
    if (has_official_confirmation and E >= 0.35) or (E >= 0.50 and conf >= 0.50 and dist.supporting_count >= 2):
        return (
            "VERIFIED",
            f"Claim is verified with authoritative evidence (weighted score: {E}, confidence: {int(conf * 100)}%). "
            f"Supported by {dist.supporting_count} independent sources including verified security disclosures."
        )

    # 4. Check for Misleading / Exaggerated claims
    # Strong presence of both contradiction and support, or neutral clarifications noting third-party/credential stuffing
    if (dist.supporting_count > 0 and dist.contradicting_count > 0 and abs(E) < 0.40) or (-0.40 < E < -0.10 and dist.neutral_count > 0):
        return (
            "MISLEADING",
            f"Claim contains material inaccuracies or exaggerations (weighted score: {E}). "
            f"Evidence indicates the incident was either misattributed (e.g., third-party supplier vs core systems) or sensationalized beyond official disclosures."
        )

    # 5. Check for Likely True
    if E >= 0.30 and groups >= 2 and dist.supporting_count >= 2:
        return (
            "LIKELY TRUE",
            f"Claim is supported by credible reporting across {groups} independent sources (weighted score: {E}), "
            f"though a formal comprehensive incident post-mortem advisory from the primary organisation is pending."
        )

    # 6. Fallback if inconclusive or weak signals
    return (
        "UNVERIFIED",
        f"Available evidence remains inconclusive (weighted score: {E}, confidence: {int(conf * 100)}%). "
        f"Independent verification threshold not met across collected intelligence."
    )
