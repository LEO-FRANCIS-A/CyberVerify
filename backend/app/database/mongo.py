import logging
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

db_instance = MongoDB()

async def connect_to_mongo():
    """Initializes MongoDB connection and creates required indexes for all 11 collections."""
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        db_instance.db = db_instance.client[settings.DATABASE_NAME]
        
        # Test connection
        await db_instance.client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}, DB: {settings.DATABASE_NAME}")
        
        # 1. investigations collection
        investigations = db_instance.db["investigations"]
        await investigations.create_index("investigation_id", unique=True)
        await investigations.create_index("created_at")
        await investigations.create_index("verdict")
        await investigations.create_index("original_claim")
        
        # 2. sources collection
        sources = db_instance.db["sources"]
        await sources.create_index("source_id", unique=True)
        await sources.create_index("investigation_id")
        await sources.create_index("url")
        
        # 3. articles collection
        articles = db_instance.db["articles"]
        await articles.create_index("article_id", unique=True)
        await articles.create_index("url", unique=True)
        await articles.create_index("canonical_url")
        await articles.create_index("content_hash")
        await articles.create_index("cves")
        await articles.create_index("domain")
        await articles.create_index("retrieval_timestamp")
        await articles.create_index("assigned_event_id")
        
        # 4. events collection
        events = db_instance.db["events"]
        await events.create_index("event_id", unique=True)
        await events.create_index("event_status")
        await events.create_index("event_classification")
        await events.create_index("first_seen")
        await events.create_index("latest_update")
        await events.create_index("cves")
        await events.create_index("organizations")
        
        # 5. event_articles collection (junction)
        event_articles = db_instance.db["event_articles"]
        await event_articles.create_index([("event_id", 1), ("article_id", 1)], unique=True)
        
        # 6. source_registry collection
        source_registry = db_instance.db["source_registry"]
        await source_registry.create_index("source_id", unique=True)
        await source_registry.create_index("domain")
        await source_registry.create_index("enabled")
        
        # 7. entity_registry collection
        entity_registry = db_instance.db["entity_registry"]
        await entity_registry.create_index("entity_name", unique=True)
        await entity_registry.create_index("entity_type")
        await entity_registry.create_index("cve_id")
        
        # 8. evidence_records collection
        evidence_records = db_instance.db["evidence_records"]
        await evidence_records.create_index("evidence_id", unique=True)
        await evidence_records.create_index("investigation_id")
        await evidence_records.create_index("subclaim_id")
        await evidence_records.create_index("citation_validation_status")
        
        # 9. article_event_pairs collection
        article_event_pairs = db_instance.db["article_event_pairs"]
        await article_event_pairs.create_index("pair_id", unique=True)
        await article_event_pairs.create_index([("article_id", 1), ("event_id", 1)])
        
        # 10. model_metadata collection
        model_metadata = db_instance.db["model_metadata"]
        await model_metadata.create_index("model_id", unique=True)
        await model_metadata.create_index("is_active")
        
        # 11. ingestion_logs and event_audit_logs collections
        ingestion_logs = db_instance.db["ingestion_logs"]
        await ingestion_logs.create_index("timestamp")
        
        event_audit_logs = db_instance.db["event_audit_logs"]
        await event_audit_logs.create_index("audit_id", unique=True)
        await event_audit_logs.create_index("timestamp")
        
        logger.info("Created indexes across all 11 MongoDB collections.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")

async def close_mongo_connection():
    """Closes MongoDB connection."""
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_database() -> AsyncIOMotorDatabase:
    if db_instance.db is None:
        raise RuntimeError("Database connection not initialized")
    return db_instance.db

def get_investigations_collection():
    return get_database()["investigations"]

def get_sources_collection():
    return get_database()["sources"]

def get_articles_collection():
    return get_database()["articles"]

def get_events_collection():
    return get_database()["events"]

def get_event_articles_collection():
    return get_database()["event_articles"]

def get_source_registry_collection():
    return get_database()["source_registry"]

def get_entity_registry_collection():
    return get_database()["entity_registry"]

def get_evidence_records_collection():
    return get_database()["evidence_records"]

def get_article_event_pairs_collection():
    return get_database()["article_event_pairs"]

def get_model_metadata_collection():
    return get_database()["model_metadata"]

def get_ingestion_logs_collection():
    return get_database()["ingestion_logs"]

def get_event_audit_logs_collection():
    return get_database()["event_audit_logs"]
