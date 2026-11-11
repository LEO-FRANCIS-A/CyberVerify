import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.models.schemas import SourceRegistryItem
from backend.app.database.mongo import get_source_registry_collection

logger = logging.getLogger(__name__)

DEFAULT_SOURCES = [
    {
        "source_id": "src_cisa_advisories",
        "name": "CISA Cybersecurity Advisories",
        "domain": "cisa.gov",
        "source_type": "Government Security Advisory",
        "feed_url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "collection_method": "rss",
        "base_reliability": 0.95,
        "is_official": True,
        "polling_interval_minutes": 30
    },
    {
        "source_id": "src_nvd_cve",
        "name": "NIST National Vulnerability Database",
        "domain": "nvd.nist.gov",
        "source_type": "Vulnerability Database",
        "feed_url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
        "collection_method": "rss",
        "base_reliability": 0.95,
        "is_official": True,
        "polling_interval_minutes": 60
    },
    {
        "source_id": "src_bleeping_computer",
        "name": "BleepingComputer",
        "domain": "bleepingcomputer.com",
        "source_type": "Established Cybersecurity Publication",
        "feed_url": "https://www.bleepingcomputer.com/feed/",
        "collection_method": "rss",
        "base_reliability": 0.85,
        "is_official": False,
        "polling_interval_minutes": 30
    },
    {
        "source_id": "src_the_hacker_news",
        "name": "The Hacker News",
        "domain": "thehackernews.com",
        "source_type": "Established Cybersecurity Publication",
        "feed_url": "https://feeds.feedburner.com/TheHackersNews",
        "collection_method": "rss",
        "base_reliability": 0.85,
        "is_official": False,
        "polling_interval_minutes": 30
    },
    {
        "source_id": "src_krebs_security",
        "name": "Krebs on Security",
        "domain": "krebsonsecurity.com",
        "source_type": "Established Cybersecurity Publication",
        "feed_url": "https://krebsonsecurity.com/feed/",
        "collection_method": "rss",
        "base_reliability": 0.85,
        "is_official": False,
        "polling_interval_minutes": 60
    },
    {
        "source_id": "src_dark_reading",
        "name": "Dark Reading",
        "domain": "darkreading.com",
        "source_type": "Established Cybersecurity Publication",
        "feed_url": "https://www.darkreading.com/rss.xml",
        "collection_method": "rss",
        "base_reliability": 0.85,
        "is_official": False,
        "polling_interval_minutes": 60
    },
    {
        "source_id": "src_microsoft_security",
        "name": "Microsoft Security Blog",
        "domain": "microsoft.com",
        "source_type": "Official Company Announcement",
        "feed_url": "https://www.microsoft.com/en-us/security/blog/feed/",
        "collection_method": "rss",
        "base_reliability": 1.00,
        "is_official": True,
        "polling_interval_minutes": 60
    },
    {
        "source_id": "src_google_security",
        "name": "Google Online Security Blog",
        "domain": "security.googleblog.com",
        "source_type": "Official Company Announcement",
        "feed_url": "https://security.googleblog.com/feeds/posts/default?alt=rss",
        "collection_method": "rss",
        "base_reliability": 1.00,
        "is_official": True,
        "polling_interval_minutes": 60
    },
    {
        "source_id": "src_unit42",
        "name": "Palo Alto Networks Unit 42",
        "domain": "unit42.paloaltonetworks.com",
        "source_type": "Independent Security Researcher",
        "feed_url": "https://unit42.paloaltonetworks.com/feed/",
        "collection_method": "rss",
        "base_reliability": 0.80,
        "is_official": False,
        "polling_interval_minutes": 60
    }
]

async def seed_source_registry() -> int:
    """Initializes the source registry collection with authoritative cybersecurity sources."""
    try:
        col = get_source_registry_collection()
        count = 0
        for item in DEFAULT_SOURCES:
            existing = await col.find_one({"source_id": item["source_id"]})
            if not existing:
                src_item = SourceRegistryItem(**item)
                await col.insert_one(src_item.model_dump())
                count += 1
        logger.info(f"Source registry initialized: {count} new sources added.")
        return count
    except Exception as e:
        logger.error(f"Error seeding source registry: {e}")
        return 0

async def get_all_registered_sources(enabled_only: bool = False) -> List[SourceRegistryItem]:
    """Retrieves all registered sources from MongoDB."""
    try:
        col = get_source_registry_collection()
        query = {"enabled": True} if enabled_only else {}
        cursor = col.find(query)
        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(SourceRegistryItem(**doc))
        if not results:
            await seed_source_registry()
            cursor = col.find(query)
            async for doc in cursor:
                doc.pop("_id", None)
                results.append(SourceRegistryItem(**doc))
        return results
    except Exception as e:
        logger.error(f"Error getting sources from registry: {e}")
        return [SourceRegistryItem(**item) for item in DEFAULT_SOURCES]

async def update_source_status(
    source_id: str,
    status: str,
    error_message: Optional[str] = None
):
    """Updates the status and polling timestamp of a registered source."""
    try:
        col = get_source_registry_collection()
        now = datetime.now(timezone.utc)
        update_doc = {
            "$set": {
                "last_polled_at": now,
                "last_status": status,
                "error_message": error_message
            }
        }
        if status == "FAILED":
            update_doc["$inc"] = {"consecutive_failures": 1}
        else:
            update_doc["$set"]["consecutive_failures"] = 0

        await col.update_one({"source_id": source_id}, update_doc)
    except Exception as e:
        logger.error(f"Failed to update source status for {source_id}: {e}")
