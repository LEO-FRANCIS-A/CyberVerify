import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
import feedparser

from backend.app.core.security import is_safe_url, sanitize_untrusted_text
from backend.app.core.config import settings
from backend.app.models.schemas import Article, SourceRegistryItem
from backend.app.database.mongo import (
    get_articles_collection, get_ingestion_logs_collection
)
from backend.app.services.source_registry_service import (
    get_all_registered_sources, update_source_status
)
from backend.app.services.article_extraction import extract_article_content
from backend.app.services.entity_extraction_service import extract_full_entities
from backend.app.services.deduplication_service import (
    normalize_canonical_url, compute_content_hash,
    compute_headline_fingerprint, compute_simhash, is_near_duplicate
)

logger = logging.getLogger(__name__)

async def fetch_feed_entries(feed_url: str) -> List[Dict[str, Any]]:
    """Safely retrieves and parses an RSS/Atom feed."""
    is_safe, reason = is_safe_url(feed_url)
    if not is_safe:
        logger.warning(f"Rejecting unsafe feed URL: {feed_url} - {reason}")
        return []

    try:
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(feed_url, headers={"User-Agent": "CyberVerify-Intelligence-Collector/2.0"})
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} fetching feed: {feed_url}")
                return []
            
            feed = feedparser.parse(resp.text)
            entries = []
            for entry in feed.entries[:15]:  # Process up to 15 latest entries per poll
                link = entry.get("link", "")
                title = entry.get("title", "")
                pub_date = entry.get("published", entry.get("updated", None))
                summary = entry.get("summary", "")
                if link and title:
                    entries.append({
                        "url": link,
                        "title": title,
                        "publication_date": pub_date,
                        "summary": summary
                    })
            return entries
    except Exception as e:
        logger.warning(f"Feed fetch failed for {feed_url}: {e}")
        return []

async def process_and_store_article(
    url: str,
    title: str,
    source: SourceRegistryItem,
    pub_date: Optional[str] = None,
    summary: Optional[str] = None
) -> Optional[Article]:
    """Ingests, cleans, extracts entities, and stores a novel article in MongoDB."""
    articles_col = get_articles_collection()
    canonical = normalize_canonical_url(url)
    
    # 1. Check if URL already exists
    existing = await articles_col.find_one({"$or": [{"url": url}, {"canonical_url": canonical}]})
    if existing:
        return None

    # 2. Extract article content using resilient Trafilatura/BeautifulSoup scraper
    scraped = await extract_article_content(url)
    if not scraped or not scraped.get("content"):
        # Fall back to summary if provided in feed
        content = summary or ""
        if len(content.strip()) < 50:
            return None
    else:
        content = scraped["content"]
        pub_date = pub_date or scraped.get("publication_date")

    content_hash = compute_content_hash(content)
    
    # 3. Check exact duplicate hash
    if await articles_col.find_one({"content_hash": content_hash}):
        return None

    simhash = compute_simhash(content)
    syndication_group = compute_headline_fingerprint(title)

    # 4. Check near-duplicate SimHash among recent articles
    recent_cursor = articles_col.find().sort("retrieval_timestamp", -1).limit(50)
    async for recent in recent_cursor:
        if recent.get("simhash") and is_near_duplicate(simhash, recent["simhash"]):
            logger.debug(f"Near duplicate detected for {title} (matches {recent.get('title')})")
            # Reuse syndication group
            syndication_group = recent.get("syndication_group_id", syndication_group)

    # 5. Entity & IOC extraction
    entities = extract_full_entities(content, title=title)
    
    art_id = f"art_{uuid.uuid4().hex[:12]}"
    article = Article(
        article_id=art_id,
        title=title,
        url=url,
        canonical_url=canonical,
        domain=source.domain,
        publisher=source.name,
        source_id=source.source_id,
        source_category=source.source_type,
        reliability_score=source.base_reliability,
        is_official=source.is_official,
        content=content,
        summary=summary or content[:300],
        content_hash=content_hash,
        simhash=simhash,
        syndication_group_id=syndication_group,
        publication_date=pub_date,
        retrieval_timestamp=datetime.now(timezone.utc),
        entities=entities,
        cves=entities["cves"],
        iocs=entities["iocs"],
        relevance_score=entities["relevance_score"],
        is_cyber_relevant=entities["is_cyber_relevant"]
    )

    await articles_col.insert_one(article.model_dump())
    logger.info(f"Ingested novel article: [{article.publisher}] {article.title[:60]} (CVEs: {len(article.cves)})")
    return article

async def poll_single_source(source: SourceRegistryItem) -> Dict[str, Any]:
    """Polls a single registered source and ingests its new articles."""
    if not source.feed_url:
        return {"source_id": source.source_id, "status": "SKIPPED", "ingested": 0}

    logger.info(f"Polling source: {source.name} ({source.feed_url})")
    entries = await fetch_feed_entries(source.feed_url)
    if not entries:
        await update_source_status(source.source_id, "FAILED", "No entries retrieved or feed unreachable")
        return {"source_id": source.source_id, "status": "FAILED", "ingested": 0}

    ingested_count = 0
    for entry in entries:
        art = await process_and_store_article(
            url=entry["url"],
            title=entry["title"],
            source=source,
            pub_date=entry.get("publication_date"),
            summary=entry.get("summary")
        )
        if art:
            ingested_count += 1

    await update_source_status(source.source_id, "SUCCESS")
    return {"source_id": source.source_id, "status": "SUCCESS", "ingested": ingested_count}

async def run_full_ingestion_cycle() -> Dict[str, Any]:
    """Executes a full continuous collection cycle across all enabled sources in the registry."""
    sources = await get_all_registered_sources(enabled_only=True)
    start_time = datetime.now(timezone.utc)
    
    # Process sources with controlled concurrency
    semaphore = asyncio.Semaphore(4)
    
    async def bounded_poll(src: SourceRegistryItem):
        async with semaphore:
            return await poll_single_source(src)

    tasks = [bounded_poll(s) for s in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_ingested = 0
    success_count = 0
    failure_count = 0
    
    for r in results:
        if isinstance(r, dict):
            if r.get("status") == "SUCCESS":
                success_count += 1
                total_ingested += r.get("ingested", 0)
            elif r.get("status") == "FAILED":
                failure_count += 1

    end_time = datetime.now(timezone.utc)
    duration_sec = round((end_time - start_time).total_seconds(), 2)

    log_entry = {
        "timestamp": start_time,
        "duration_seconds": duration_sec,
        "sources_polled": len(sources),
        "success_sources": success_count,
        "failed_sources": failure_count,
        "new_articles_ingested": total_ingested
    }
    
    try:
        log_col = get_ingestion_logs_collection()
        await log_col.insert_one(log_entry)
    except Exception as e:
        logger.error(f"Failed to record ingestion log: {e}")

    logger.info(f"Ingestion cycle completed in {duration_sec}s: {total_ingested} articles from {success_count}/{len(sources)} sources.")
    return log_entry
