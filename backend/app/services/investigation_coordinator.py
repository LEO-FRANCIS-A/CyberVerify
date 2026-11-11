import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any, List
from backend.app.models.schemas import (
    Investigation, ExtractedEntities, SourceItem, OfficialSourcesReport,
    MathematicalResults, AISummary, Subclaim, EvidenceRecord, InvestigationCoverage
)
from backend.app.services.claim_extraction import extract_claim
from backend.app.services.claim_decomposition_service import (
    decompose_claim_into_subclaims, answer_eight_investigative_questions
)
from backend.app.services.web_search import conduct_targeted_search
from backend.app.services.article_extraction import extract_article_content
from backend.app.services.evidence_analysis import classify_evidence_stance
from backend.app.services.citation_validation_service import build_validated_evidence_record
from backend.app.services.coverage_service import compute_investigation_coverage
from backend.app.services.mathematical_engine import compute_mathematical_results
from backend.app.services.verdict_engine import determine_verdict
from backend.app.services.report_generator import generate_ai_summary
from backend.app.database.mongo import (
    get_investigations_collection, get_sources_collection, get_evidence_records_collection
)

logger = logging.getLogger(__name__)

async def run_investigation_pipeline(
    claim: str,
    progress_callback: Optional[Callable[[int, str, Dict[str, Any]], Any]] = None,
    previous_investigation_id: Optional[str] = None
) -> Investigation:
    """
    Coordinates the end-to-end 7-step investigation process with subclaim decomposition,
    citation validation, and coverage tracking.
    """
    inv_id = f"cv_{uuid.uuid4().hex[:12]}"
    
    async def report_progress(step: int, message: str, meta: Dict[str, Any] = None):
        if progress_callback:
            try:
                res = progress_callback(step, message, meta or {})
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.debug(f"Progress callback exception: {e}")

    # STEP 1: Claim Extraction & Subclaim Decomposition
    await report_progress(1, "Extracting structured claim components, entities, and search parameters...")
    entities: ExtractedEntities = await extract_claim(claim)
    subclaims: List[Subclaim] = await decompose_claim_into_subclaims(claim, entities)
    
    await report_progress(
        1,
        f"Identified entity: {entities.organisation} | Incident: {entities.incident_type} | Decomposed into {len(subclaims)} subclaim(s)",
        {"entities": entities.model_dump(), "subclaims": [sc.model_dump() for sc in subclaims]}
    )

    # STEP 2: Internet Search & Multi-Vector OSINT
    await report_progress(2, f"Conducting prioritized web search across official advisories and cybersecurity press...")
    search_results, official_queries = await conduct_targeted_search(
        organisation=entities.organisation,
        incident_type=entities.incident_type,
        keywords=entities.search_keywords
    )
    providers_queried = ["DuckDuckGo"]
    from backend.app.core.config import settings
    if settings.TAVILY_API_KEY:
        providers_queried.append("Tavily")

    await report_progress(2, f"Retrieved {len(search_results)} relevant search candidate URLs.", {"candidates_count": len(search_results)})

    # STEP 3: Sandboxed Scraping & Extraction
    await report_progress(3, "Collecting and safely extracting readable body text from candidate URLs...")
    extracted_sources: List[SourceItem] = []
    raw_contents: Dict[str, str] = {}
    failed_retrievals: List[Dict[str, str]] = []
    
    semaphore = asyncio.Semaphore(5)
    
    async def process_candidate(item: Dict[str, Any]):
        async with semaphore:
            url = item["url"]
            try:
                art_data = await extract_article_content(url)
                content = art_data["content"] if (art_data and art_data.get("content")) else item.get("snippet", "")
                if not content or len(content.strip()) < 30:
                    content = f"{item['title']}. {content}".strip()
                if not content or len(content.strip()) < 10:
                    failed_retrievals.append({"url": url, "reason": "Insufficient text content extracted"})
                    return None
                    
                pub_date = art_data.get("publication_date") if art_data else None
                raw_contents[url] = content
                
                # STEP 4/5: Stance & Source Classification
                stance, passages = await classify_evidence_stance(
                    claim=claim,
                    allegation=entities.allegation,
                    title=item["title"],
                    content=content
                )
                
                src_item = SourceItem(
                    source_id=f"src_{uuid.uuid4().hex[:8]}",
                    investigation_id=inv_id,
                    title=item["title"],
                    publisher=item["publisher"],
                    url=url,
                    publication_date=pub_date,
                    source_category=item["source_category"],
                    reliability_score=item["reliability_score"],
                    evidence_classification=stance,
                    extracted_passages=passages,
                    source_group_id=item["source_group_id"],
                    is_primary_evidence=item.get("is_primary_evidence", False),
                    is_official=item.get("is_official", False)
                )
                return src_item
            except Exception as e:
                failed_retrievals.append({"url": url, "reason": str(e)})
                return None

    tasks = [process_candidate(item) for item in search_results]
    completed_items = await asyncio.gather(*tasks, return_exceptions=True)
    
    for res in completed_items:
        if isinstance(res, SourceItem):
            extracted_sources.append(res)

    await report_progress(3, f"Successfully extracted and sanitized {len(extracted_sources)} sources.", {"sources_count": len(extracted_sources)})

    # STEP 4: Official Source Identification
    await report_progress(4, "Evaluating official vendor announcements and security advisories...")
    official_found = [s for s in extracted_sources if s.is_official or s.source_category in ("Official Company Announcement", "Government Security Advisory")]
    
    has_primary_confirmation = any(s.is_official and s.evidence_classification == "SUPPORTING" for s in extracted_sources)
    has_primary_denial = any(s.is_official and s.evidence_classification == "CONTRADICTING" for s in extracted_sources)

    if official_found:
        status_summary = f"Identified {len(official_found)} official announcement/advisory source(s) from {entities.organisation} or government CSIRT."
    else:
        status_summary = f"No direct official company announcement or government security advisory was discovered for {entities.organisation} regarding this allegation."

    official_report = OfficialSourcesReport(
        official_sources_found=[{"title": s.title, "url": s.url, "publisher": s.publisher, "stance": s.evidence_classification} for s in official_found],
        official_sources_checked=official_queries,
        status_summary=status_summary,
        has_primary_confirmation=has_primary_confirmation,
        has_primary_denial=has_primary_denial
    )
    await report_progress(4, status_summary, {"official_sources_count": len(official_found)})

    # STEP 5 & 6: Mathematical Consensus & Bayesian Probability Updates
    await report_progress(5, "Executing mathematical weighting, syndication clustering, and Bayesian probability updates...")
    math_results: MathematicalResults = compute_mathematical_results(extracted_sources)
    await report_progress(5, f"Computed Weighted Score E = {math_results.weighted_evidence_score} | Confidence: {int(math_results.confidence_score * 100)}%", {"math": math_results.model_dump()})

    # STEP 6/7: Generating Final Deterministic Verdict
    await report_progress(6, "Evaluating verdict rules and evidence consensus...")
    verdict, verdict_explanation = determine_verdict(
        math_results=math_results,
        sources=extracted_sources,
        has_official_denial=has_primary_denial,
        has_official_confirmation=has_primary_confirmation
    )
    await report_progress(6, f"Generated Final Verdict: {verdict}", {"verdict": verdict})

    # STEP 7: Evidence Traceability, Citation Validation & Subclaim Evaluation
    await report_progress(7, "Validating citations, answering investigative questions, and synthesizing intelligence briefing...")
    
    evidence_records: List[EvidenceRecord] = []
    supporting_passages = []
    contradicting_passages = []

    for src in extracted_sources:
        raw_text = raw_contents.get(src.url, "")
        ev_rec = build_validated_evidence_record(
            investigation_id=inv_id,
            source_item=src,
            raw_content=raw_text,
            claim=claim,
            subclaim_id=subclaims[0].subclaim_id if subclaims else None
        )
        evidence_records.append(ev_rec)
        if src.evidence_classification == "SUPPORTING" and src.extracted_passages:
            supporting_passages.extend(src.extracted_passages)
        elif src.evidence_classification == "CONTRADICTING" and src.extracted_passages:
            contradicting_passages.extend(src.extracted_passages)

    # Evaluate 8 questions per subclaim
    for sc in subclaims:
        sc.status = verdict
        sc.confidence = math_results.confidence_score
        sc.evidence_ids = [er.evidence_id for er in evidence_records]
        sc.answers = answer_eight_investigative_questions(
            subclaim=sc,
            supporting_passages=supporting_passages,
            contradicting_passages=contradicting_passages,
            official_status=official_report.status_summary,
            verdict=verdict
        )

    # Compute Investigation Coverage Indicator
    coverage: InvestigationCoverage = compute_investigation_coverage(
        queries_executed=entities.search_keywords,
        providers_queried=providers_queried,
        official_queries=official_queries,
        sources=extracted_sources,
        failed_retrievals=failed_retrievals,
        target_org=entities.organisation
    )

    # AI Investigative Summary
    ai_summary: AISummary = await generate_ai_summary(
        claim=claim,
        entities=entities,
        verdict=verdict,
        math_results=math_results,
        official_sources=official_report,
        sources=extracted_sources
    )

    now_utc = datetime.now(timezone.utc)
    investigation = Investigation(
        investigation_id=inv_id,
        original_claim=claim,
        extracted_entities=entities,
        incident_category=entities.incident_type,
        investigation_date=now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        verdict=verdict,
        confidence_score=math_results.confidence_score,
        verdict_explanation=verdict_explanation,
        official_sources=official_report,
        sources=extracted_sources,
        mathematical_results=math_results,
        ai_summary=ai_summary,
        subclaims=subclaims,
        evidence_records=evidence_records,
        coverage=coverage,
        status="COMPLETED",
        created_at=now_utc,
        previous_investigation_id=previous_investigation_id
    )

    # Save to MongoDB
    try:
        inv_col = get_investigations_collection()
        src_col = get_sources_collection()
        ev_col = get_evidence_records_collection()
        
        # Save investigation document
        await inv_col.insert_one(investigation.model_dump())
        
        # Save individual sources
        if extracted_sources:
            await src_col.insert_many([s.model_dump() for s in extracted_sources])
            
        # Save validated evidence records
        if evidence_records:
            await ev_col.insert_many([er.model_dump() for er in evidence_records])
            
        logger.info(f"Persisted investigation {inv_id} with {len(evidence_records)} evidence records to MongoDB.")
    except Exception as e:
        logger.error(f"Failed to persist investigation to MongoDB: {e}")

    await report_progress(7, "Investigation complete. Report ready.", {"investigation_id": inv_id})
    return investigation
