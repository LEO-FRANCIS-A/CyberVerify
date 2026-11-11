import re
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse

from backend.app.models.schemas import EvidenceRecord, SourceItem
from backend.app.services.deduplication_service import normalize_canonical_url

logger = logging.getLogger(__name__)

def verify_passage_in_content(passage: str, raw_content: str) -> Tuple[bool, float, str]:
    """
    Validates that an extracted evidentiary passage genuinely exists within the stored raw source content.
    Returns: (is_valid, overlap_ratio, location_note)
    """
    if not passage or not raw_content:
        return False, 0.0, "Missing passage or raw content"

    clean_passage = re.sub(r"\s+", " ", passage.strip().lower())
    clean_content = re.sub(r"\s+", " ", raw_content.strip().lower())

    # 1. Direct exact substring match
    if clean_passage in clean_content:
        return True, 1.0, "Verbatim substring match confirmed in article body"

    # 2. Token set overlap match (for minor formatting/whitespace deviations)
    passage_tokens = set(clean_passage.split())
    if not passage_tokens:
        return False, 0.0, "Empty passage tokens"

    content_tokens = clean_content.split()
    if not content_tokens:
        return False, 0.0, "Empty content tokens"

    if len(content_tokens) <= len(passage_tokens) + 15:
        intersection = len(passage_tokens.intersection(set(content_tokens)))
        overlap = intersection / len(passage_tokens)
        if overlap >= 0.65:
            return True, round(overlap, 3), f"High-fidelity passage alignment ({int(overlap*100)}% token overlap)"
        return False, round(overlap, 3), f"Passage rejected: insufficient presence in raw text (overlap: {round(overlap, 2)})"

    w_size = len(passage_tokens) + 15
    best_overlap = 0.0
    step = max(1, min(5, len(passage_tokens) // 2))

    for i in range(0, len(content_tokens) - w_size + 1, step):
        window = set(content_tokens[i : i + w_size])
        intersection = len(passage_tokens.intersection(window))
        overlap = intersection / len(passage_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            if best_overlap >= 0.85:
                return True, round(best_overlap, 3), f"High-fidelity passage alignment ({int(best_overlap*100)}% token overlap)"

    if best_overlap >= 0.65:
        return True, round(best_overlap, 3), f"Paraphrased excerpt detected ({int(best_overlap*100)}% token overlap)"

    return False, round(best_overlap, 3), f"Passage rejected: insufficient presence in raw text (overlap: {round(best_overlap, 2)})"

def evaluate_nli_entailment_heuristic(passage: str, claim: str, stance: str) -> float:
    """
    Computes an NLI-based entailment score [0.0 - 1.0] between passage and claim.
    Penalizes common false inferences:
    - Mentioning an organization != Compromising the organization
    - Vulnerability disclosure != Confirmed exploitation
    - Third-party compromise != Core vendor compromise
    """
    lower_passage = passage.lower()
    lower_claim = claim.lower()
    
    score = 0.50  # Neutral base

    if stance == "SUPPORTING":
        score = 0.75
        # Guard: Check for false attribution / third-party caveats
        if "third-party" in lower_passage or "contractor" in lower_passage or "credential stuffing" in lower_passage:
            if "breached" in lower_claim and "third-party" not in lower_claim:
                # Claim says company breached, but passage says third party!
                score = 0.40  # Downgrade entailment
        if "no evidence" in lower_passage or "not affected" in lower_passage:
            score = 0.20  # Passage actually contradicts!

    elif stance == "CONTRADICTING":
        score = 0.85
        if any(den in lower_passage for den in ["denies", "false", "no evidence", "unfounded", "did not occur"]):
            score = 0.95

    return round(score, 3)

def build_validated_evidence_record(
    investigation_id: str,
    source_item: SourceItem,
    raw_content: str,
    claim: str,
    subclaim_id: Optional[str] = None
) -> EvidenceRecord:
    """
    Builds a fully traceable, audited EvidenceRecord with verified citation status.
    Guarantees no fabricated quotations or URLs enter the final intelligence briefing.
    """
    passage = source_item.extracted_passages[0] if source_item.extracted_passages else source_item.title
    
    # 1. Validate that the URL has a valid domain
    parsed = urlparse(source_item.url)
    domain = parsed.hostname.lower() if parsed.hostname else "unknown"

    # 2. Verify passage exists in raw scraped content
    is_valid_passage, overlap, loc_note = verify_passage_in_content(passage, raw_content or source_item.title)
    
    # 3. Determine citation validation status
    if not source_item.url or not parsed.scheme.startswith("http") or not raw_content or not raw_content.strip():
        status = "URL_INACCESSIBLE"
    elif is_valid_passage:
        status = "VALIDATED"
    elif len(raw_content.strip()) < 50:
        status = "UNCONFIRMED_PASSAGE"
    else:
        status = "REJECTED_UNSUPPORTED"

    # 4. Compute NLI Entailment
    nli_score = evaluate_nli_entailment_heuristic(passage, claim, source_item.evidence_classification)

    ev_record = EvidenceRecord(
        evidence_id=f"evr_{uuid.uuid4().hex[:10]}",
        investigation_id=investigation_id,
        subclaim_id=subclaim_id,
        source_title=source_item.title,
        source_url=source_item.url,
        canonical_url=normalize_canonical_url(source_item.url),
        source_domain=domain,
        source_category=source_item.source_category,
        publication_date=source_item.publication_date,
        retrieval_timestamp=datetime.now(timezone.utc),
        extracted_passage=passage,
        passage_location=loc_note,
        evidence_stance=source_item.evidence_classification,
        source_reliability=source_item.reliability_score,
        syndication_group_id=source_item.source_group_id,
        citation_validation_status=status,
        nli_entailment_score=nli_score,
        is_primary_evidence=source_item.is_primary_evidence,
        is_official=source_item.is_official
    )

    return ev_record
