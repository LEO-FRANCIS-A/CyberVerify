import json
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Response
from fastapi.responses import StreamingResponse

from backend.app.models.schemas import (
    InvestigateRequest, Investigation, DashboardStats, InvestigationListItem,
    CyberEvent, EventTimelineEntry, EventAuditLog, SourceRegistryItem, ModelMetadata
)
from backend.app.services.investigation_coordinator import run_investigation_pipeline
from backend.app.services.report_generator import build_pdf_report
from backend.app.services.source_registry_service import (
    get_all_registered_sources, seed_source_registry
)
from backend.app.services.ingestion_service import run_full_ingestion_cycle
from backend.app.services.event_audit_service import run_hdbscan_audit
from backend.app.services.event_scoring_service import global_event_scorer
from backend.app.database.mongo import (
    get_investigations_collection, get_sources_collection, get_events_collection,
    get_articles_collection, get_event_audit_logs_collection, get_ingestion_logs_collection,
    get_article_event_pairs_collection, get_model_metadata_collection, db_instance
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ==========================================================
# HEALTH & DIAGNOSTICS
# ==========================================================

@router.get("/health")
async def health_check():
    """Health status and database connectivity check."""
    mongo_status = "connected"
    try:
        if db_instance.client:
            await db_instance.client.admin.command('ping')
        else:
            mongo_status = "disconnected"
    except Exception as e:
        mongo_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "CyberVerify Dual-Engine Platform",
        "version": "2.0.0",
        "database": mongo_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==========================================================
# CLAIM VERIFICATION ENGINE ROUTES
# ==========================================================

@router.post("/investigate", response_model=Investigation)
async def create_investigation(req: InvestigateRequest):
    """
    Submits a cybersecurity news claim or rumor to be investigated.
    Runs the full 7-step verification engine and persists the result.
    """
    try:
        investigation = await run_investigation_pipeline(claim=req.claim.strip())
        return investigation
    except Exception as e:
        logger.error(f"Investigation execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")

@router.get("/investigate/stream")
async def stream_investigation(claim: str = Query(..., min_length=5, max_length=1500)):
    """
    Real-time Server-Sent Events (SSE) investigation stream.
    Streams live progress across each of the 7 investigation stages.
    """
    async def event_generator():
        queue = asyncio.Queue()

        async def progress_listener(step: int, message: str, meta: Dict[str, Any]):
            await queue.put({
                "type": "progress",
                "step": step,
                "message": message,
                "meta": meta or {}
            })

        async def worker():
            try:
                res = await run_investigation_pipeline(
                    claim=claim.strip(),
                    progress_callback=progress_listener
                )
                await queue.put({
                    "type": "complete",
                    "step": 7,
                    "message": "Investigation successfully concluded.",
                    "data": res.model_dump()
                })
            except Exception as ex:
                logger.error(f"Streaming pipeline error: {ex}", exc_info=True)
                await queue.put({
                    "type": "error",
                    "message": str(ex)
                })

        task = asyncio.create_task(worker())

        while True:
            item = await queue.get()
            yield f"data: {json.dumps(item, default=str)}\n\n"
            if item.get("type") in ("complete", "error"):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/investigations", response_model=List[InvestigationListItem])
async def list_investigations(
    search: Optional[str] = Query(None, description="Search term in claim text or organization"),
    verdict: Optional[str] = Query(None, description="Filter by verdict"),
    limit: int = Query(50, ge=1, le=100)
):
    """Retrieves all past investigations with optional filtering and search."""
    try:
        col = get_investigations_collection()
        query = {}
        if verdict and verdict.strip() and verdict.upper() != "ALL":
            query["verdict"] = verdict.strip().upper()
        if search and search.strip():
            query["$or"] = [
                {"original_claim": {"$regex": search.strip(), "$options": "i"}},
                {"extracted_entities.organisation": {"$regex": search.strip(), "$options": "i"}},
                {"incident_category": {"$regex": search.strip(), "$options": "i"}}
            ]

        cursor = col.find(query).sort("created_at", -1).limit(limit)
        results = []
        async for doc in cursor:
            results.append(InvestigationListItem(
                investigation_id=doc["investigation_id"],
                original_claim=doc["original_claim"],
                organisation=doc.get("extracted_entities", {}).get("organisation", "Unknown"),
                incident_category=doc.get("incident_category", "General Incident"),
                investigation_date=doc.get("investigation_date", ""),
                verdict=doc.get("verdict", "UNVERIFIED"),
                confidence_score=doc.get("confidence_score", 0.0),
                total_sources=len(doc.get("sources", [])),
                official_sources_count=doc.get("mathematical_results", {}).get("official_sources_count", 0),
                created_at=doc.get("created_at", datetime.now(timezone.utc))
            ))
        return results
    except Exception as e:
        logger.error(f"Error fetching investigations: {e}")
        return []

@router.get("/investigations/{investigation_id}", response_model=Investigation)
async def get_investigation(investigation_id: str):
    """Retrieves complete details of an existing investigation report."""
    try:
        col = get_investigations_collection()
        doc = await col.find_one({"investigation_id": investigation_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Investigation not found")
        doc.pop("_id", None)
        return Investigation(**doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting investigation {investigation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/investigations/{investigation_id}")
async def delete_investigation(investigation_id: str):
    """Deletes an investigation and its associated sources."""
    try:
        col = get_investigations_collection()
        src_col = get_sources_collection()
        
        result = await col.delete_one({"investigation_id": investigation_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Investigation not found")
            
        await src_col.delete_many({"investigation_id": investigation_id})
        return {"status": "success", "message": f"Investigation {investigation_id} deleted."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/investigations/{investigation_id}/reinvestigate", response_model=Investigation)
async def reinvestigate_claim(investigation_id: str):
    """
    Reinvestigates an existing claim to discover newly published advisories or reports.
    """
    col = get_investigations_collection()
    prev = await col.find_one({"investigation_id": investigation_id})
    if not prev:
        raise HTTPException(status_code=404, detail="Original investigation not found")

    claim_text = prev.get("original_claim")
    try:
        new_inv = await run_investigation_pipeline(
            claim=claim_text,
            previous_investigation_id=investigation_id
        )
        return new_inv
    except Exception as e:
        logger.error(f"Reinvestigation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reinvestigation failed: {str(e)}")

@router.get("/investigations/{investigation_id}/export")
async def export_investigation(investigation_id: str, format: str = Query("pdf")):
    """Exports an investigation as an Executive PDF or structured JSON."""
    col = get_investigations_collection()
    doc = await col.find_one({"investigation_id": investigation_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Investigation not found")
    doc.pop("_id", None)

    if format.lower() == "json":
        return Response(
            content=json.dumps(doc, default=str, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=CyberVerify_{investigation_id}.json"}
        )

    # PDF generation
    try:
        pdf_bytes = build_pdf_report(doc)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=CyberVerify_Report_{investigation_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@router.get("/compare")
async def compare_investigations(id1: str = Query(...), id2: str = Query(...)):
    """Compares two investigations side-by-side."""
    col = get_investigations_collection()
    doc1 = await col.find_one({"investigation_id": id1})
    doc2 = await col.find_one({"investigation_id": id2})
    
    if not doc1 or not doc2:
        raise HTTPException(status_code=404, detail="One or both investigations not found")
        
    doc1.pop("_id", None)
    doc2.pop("_id", None)
    
    return {
        "investigation_1": doc1,
        "investigation_2": doc2,
        "comparison_summary": {
            "verdict_changed": doc1.get("verdict") != doc2.get("verdict"),
            "confidence_delta": round(doc2.get("confidence_score", 0.0) - doc1.get("confidence_score", 0.0), 3),
            "score_delta": round(
                doc2.get("mathematical_results", {}).get("weighted_evidence_score", 0.0) - 
                doc1.get("mathematical_results", {}).get("weighted_evidence_score", 0.0), 3
            ),
            "sources_delta": len(doc2.get("sources", [])) - len(doc1.get("sources", []))
        }
    }

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Aggregates metrics and statistics for the main dashboard cards and charts."""
    try:
        col = get_investigations_collection()
        docs = await col.find().to_list(length=1000)
        
        total = len(docs)
        verified = sum(1 for d in docs if d.get("verdict") == "VERIFIED")
        likely_true = sum(1 for d in docs if d.get("verdict") == "LIKELY TRUE")
        false_count = sum(1 for d in docs if d.get("verdict") == "FALSE")
        misleading = sum(1 for d in docs if d.get("verdict") == "MISLEADING")
        unverified = sum(1 for d in docs if d.get("verdict") == "UNVERIFIED")
        
        confidences = [d.get("confidence_score", 0.0) for d in docs if d.get("confidence_score") is not None]
        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

        verdict_distribution = [
            {"name": "VERIFIED", "count": verified, "color": "#16A34A"},
            {"name": "LIKELY TRUE", "count": likely_true, "color": "#2563EB"},
            {"name": "FALSE", "count": false_count, "color": "#DC2626"},
            {"name": "MISLEADING", "count": misleading, "color": "#D97706"},
            {"name": "UNVERIFIED", "count": unverified, "color": "#64748B"}
        ]

        # Activity timeline
        activity_dict = {}
        for d in docs:
            date_str = d.get("investigation_date", "").split(" ")[0] if d.get("investigation_date") else "Recent"
            activity_dict[date_str] = activity_dict.get(date_str, 0) + 1

        recent_activity = [{"date": k, "investigations": v} for k, v in list(activity_dict.items())[-7:]]
        if not recent_activity:
            recent_activity = [{"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "investigations": total}]

        # Evidence stances
        total_sup = sum(d.get("mathematical_results", {}).get("evidence_distribution", {}).get("supporting_count", 0) for d in docs)
        total_con = sum(d.get("mathematical_results", {}).get("evidence_distribution", {}).get("contradicting_count", 0) for d in docs)
        total_neu = sum(d.get("mathematical_results", {}).get("evidence_distribution", {}).get("neutral_count", 0) for d in docs)
        total_inc = sum(d.get("mathematical_results", {}).get("evidence_distribution", {}).get("inconclusive_count", 0) for d in docs)

        return DashboardStats(
            total_investigations=total,
            verified_claims=verified,
            likely_true_claims=likely_true,
            false_claims=false_count,
            misleading_claims=misleading,
            unverified_claims=unverified,
            verdict_distribution=verdict_distribution,
            recent_activity=recent_activity,
            evidence_distribution={
                "Supporting": total_sup,
                "Contradicting": total_con,
                "Neutral": total_neu,
                "Inconclusive": total_inc
            },
            average_confidence=avg_conf
        )
    except Exception as e:
        logger.error(f"Error computing dashboard stats: {e}")
        return DashboardStats(
            total_investigations=0,
            verified_claims=0,
            likely_true_claims=0,
            false_claims=0,
            misleading_claims=0,
            unverified_claims=0,
            verdict_distribution=[],
            recent_activity=[],
            evidence_distribution={},
            average_confidence=0.0
        )

# ==========================================================
# EVENT INTELLIGENCE ENGINE ROUTES
# ==========================================================

@router.get("/events", response_model=List[CyberEvent])
async def list_events(
    search: Optional[str] = Query(None, description="Search term in title or description"),
    status: Optional[str] = Query(None, description="ACTIVE, RESOLVED, MONITORING"),
    cve: Optional[str] = Query(None, description="Filter by CVE identifier"),
    limit: int = Query(50, ge=1, le=100)
):
    """Retrieves cybersecurity events clustered by the event intelligence engine."""
    try:
        col = get_events_collection()
        query = {}
        if status and status.upper() != "ALL":
            query["event_status"] = status.upper()
        if cve and cve.strip():
            query["cves"] = cve.strip().upper()
        if search and search.strip():
            query["$or"] = [
                {"title": {"$regex": search.strip(), "$options": "i"}},
                {"description": {"$regex": search.strip(), "$options": "i"}},
                {"organizations": {"$regex": search.strip(), "$options": "i"}},
                {"threat_actors": {"$regex": search.strip(), "$options": "i"}}
            ]

        cursor = col.find(query).sort("latest_update", -1).limit(limit)
        events = []
        async for doc in cursor:
            doc.pop("_id", None)
            events.append(CyberEvent(**doc))
        return events
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        return []

@router.get("/events/{event_id}", response_model=CyberEvent)
async def get_event(event_id: str):
    """Retrieves full details of a single cybersecurity event including timeline and articles."""
    col = get_events_collection()
    doc = await col.find_one({"event_id": event_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Event not found")
    doc.pop("_id", None)
    return CyberEvent(**doc)

@router.get("/events/{event_id}/timeline", response_model=List[EventTimelineEntry])
async def get_event_timeline(event_id: str):
    """Retrieves the chronological intelligence timeline of an event."""
    col = get_events_collection()
    doc = await col.find_one({"event_id": event_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Event not found")
    timeline_data = doc.get("timeline", [])
    return [EventTimelineEntry(**t) for t in timeline_data]

@router.post("/events/audit", response_model=EventAuditLog)
async def trigger_event_audit():
    """Triggers an unsupervised HDBSCAN diagnostic audit across events and articles."""
    try:
        audit_log = await run_hdbscan_audit()
        return audit_log
    except Exception as e:
        logger.error(f"HDBSCAN audit execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/audits", response_model=List[EventAuditLog])
async def list_event_audits(limit: int = 10):
    """Retrieves historical HDBSCAN audit logs."""
    try:
        col = get_event_audit_logs_collection()
        cursor = col.find().sort("timestamp", -1).limit(limit)
        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(EventAuditLog(**doc))
        return results
    except Exception as e:
        logger.error(f"Error fetching event audits: {e}")
        return []

# ==========================================================
# INGESTION & SOURCE REGISTRY ROUTES
# ==========================================================

@router.get("/sources/registry", response_model=List[SourceRegistryItem])
async def list_registered_sources():
    """Retrieves all configured collection sources from the registry."""
    return await get_all_registered_sources(enabled_only=False)

@router.post("/ingest/trigger")
async def trigger_ingestion_cycle(background_tasks: BackgroundTasks):
    """Triggers an asynchronous continuous ingestion cycle across all active sources."""
    try:
        # Run in foreground for immediate metrics or background if preferred
        result = await run_full_ingestion_cycle()
        return {"status": "SUCCESS", "ingestion_summary": result}
    except Exception as e:
        logger.error(f"Ingestion trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ingest/logs")
async def get_ingestion_logs(limit: int = 20):
    """Retrieves execution logs of continuous ingestion cycles."""
    try:
        col = get_ingestion_logs_collection()
        cursor = col.find().sort("timestamp", -1).limit(limit)
        logs = []
        async for doc in cursor:
            doc.pop("_id", None)
            logs.append(doc)
        return logs
    except Exception as e:
        logger.error(f"Error getting ingestion logs: {e}")
        return []

# ==========================================================
# ML MODEL STATUS & RETRAINING ROUTES
# ==========================================================

@router.get("/model/status")
async def get_model_status():
    """Retrieves the weights, metrics, and training status of the event scoring model."""
    col = get_model_metadata_collection()
    doc = await col.find_one({"is_active": True})
    if doc:
        doc.pop("_id", None)
        return doc
    return {
        "model_id": "model_logistic_regression_default",
        "model_version": "1.0.0",
        "is_trained": global_event_scorer.is_trained,
        "weights": global_event_scorer.weights,
        "metrics": global_event_scorer.metrics,
        "confusion_matrix": global_event_scorer.confusion_matrix,
        "is_active": True
    }
