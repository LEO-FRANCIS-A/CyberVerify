from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def get_now_utc():
    return datetime.now(timezone.utc)

class InvestigateRequest(BaseModel):
    claim: str = Field(..., min_length=5, max_length=1500, description="The cybersecurity news claim or rumor to investigate")

class ExtractedEntities(BaseModel):
    subject: str = Field(..., description="Main entity or technology involved")
    organisation: str = Field(..., description="Target company or organization")
    incident_type: str = Field(..., description="Breach, Ransomware, Zero-day, Phishing, Denial, etc.")
    allegation: str = Field(..., description="Core factual claim being made")
    relevant_dates: List[str] = Field(default_factory=list, description="Dates or timeframes mentioned")
    affected_products: List[str] = Field(default_factory=list, description="Products, systems, or platforms affected")
    search_keywords: List[str] = Field(default_factory=list, description="Optimal keywords for targeted search")

class Subclaim(BaseModel):
    subclaim_id: str
    subclaim_text: str
    target_org: Optional[str] = None
    threat_actor: Optional[str] = None
    incident_type: str = "General Incident"
    affected_product: Optional[str] = None
    cve: Optional[str] = None
    allegation: str
    status: str = "UNVERIFIED"  # VERIFIED, LIKELY TRUE, FALSE, MISLEADING, UNVERIFIED
    confidence: float = 0.0
    evidence_ids: List[str] = Field(default_factory=list)
    answers: Dict[str, str] = Field(default_factory=dict)  # 8 investigative answers

class EvidenceRecord(BaseModel):
    evidence_id: str
    investigation_id: str
    subclaim_id: Optional[str] = None
    source_title: str
    source_url: str
    canonical_url: str
    source_domain: str
    source_category: str
    publication_date: Optional[str] = None
    retrieval_timestamp: datetime = Field(default_factory=get_now_utc)
    extracted_passage: str
    passage_location: str = "body"  # body, title, snippet
    evidence_stance: str = "NEUTRAL"  # SUPPORTING, CONTRADICTING, NEUTRAL, INCONCLUSIVE
    source_reliability: float = 0.5
    syndication_group_id: str = ""
    citation_validation_status: str = "VALIDATED"  # VALIDATED, UNCONFIRMED_PASSAGE, URL_INACCESSIBLE, REJECTED_UNSUPPORTED
    nli_entailment_score: Optional[float] = None
    is_primary_evidence: bool = False
    is_official: bool = False

class SourceItem(BaseModel):
    source_id: str
    investigation_id: str
    title: str
    publisher: str
    url: str
    publication_date: Optional[str] = None
    source_category: str
    reliability_score: float
    evidence_classification: str  # SUPPORTING, CONTRADICTING, NEUTRAL, INCONCLUSIVE
    extracted_passages: List[str] = Field(default_factory=list)
    source_group_id: str  # Identifies syndicated/republished groups
    is_primary_evidence: bool = False
    is_official: bool = False

class EvidenceDistribution(BaseModel):
    supporting_count: int = 0
    contradicting_count: int = 0
    neutral_count: int = 0
    inconclusive_count: int = 0
    supporting_percentage: float = 0.0
    contradicting_percentage: float = 0.0
    neutral_percentage: float = 0.0
    inconclusive_percentage: float = 0.0

class BayesianAnalysis(BaseModel):
    prior_probability: float
    posterior_probability: float
    bayes_factor: float
    log_odds: float
    evidence_weight_sum: float
    explanation: str

class MathematicalResults(BaseModel):
    weighted_evidence_score: float = Field(..., description="E = Σ(w_i * s_i) / Σw_i, bounded between -1.0 and +1.0")
    total_sources: int
    independent_source_count: int
    official_sources_count: int
    evidence_distribution: EvidenceDistribution
    bayesian_analysis: Optional[BayesianAnalysis] = None
    confidence_score: float = Field(..., description="Heuristic confidence indicator [0.0 - 1.0]")
    confidence_explanation: str
    reliability_weights_breakdown: List[Dict[str, Any]] = Field(default_factory=list)

class OfficialSourcesReport(BaseModel):
    official_sources_found: List[Dict[str, Any]] = Field(default_factory=list)
    official_sources_checked: List[str] = Field(default_factory=list)
    status_summary: str
    has_primary_confirmation: bool = False
    has_primary_denial: bool = False

class InvestigationCoverage(BaseModel):
    queries_executed: List[str] = Field(default_factory=list)
    providers_queried: List[str] = Field(default_factory=list)
    official_sources_checked: List[str] = Field(default_factory=list)
    government_sources_checked: List[str] = Field(default_factory=list)
    researcher_sources_checked: List[str] = Field(default_factory=list)
    relevant_articles_retrieved: int = 0
    successful_extractions: int = 0
    independent_evidence_groups: int = 0
    failed_retrievals: List[Dict[str, str]] = Field(default_factory=list)
    missing_source_coverage: List[str] = Field(default_factory=list)
    channel_statuses: Dict[str, str] = Field(default_factory=dict)
    coverage_percentage: float = 0.0
    coverage_explanation: str = ""

class AISummary(BaseModel):
    what_reportedly_happened: str
    supporting_evidence_summary: str
    contradicting_evidence_summary: str
    official_sources_position: str
    uncertainties_and_gaps: str
    final_assessment: str

class Investigation(BaseModel):
    investigation_id: str
    original_claim: str
    extracted_entities: ExtractedEntities
    incident_category: str
    investigation_date: str
    verdict: str  # VERIFIED, LIKELY TRUE, FALSE, MISLEADING, UNVERIFIED
    confidence_score: float
    verdict_explanation: str
    official_sources: OfficialSourcesReport
    sources: List[SourceItem] = Field(default_factory=list)
    mathematical_results: MathematicalResults
    ai_summary: AISummary
    subclaims: List[Subclaim] = Field(default_factory=list)
    evidence_records: List[EvidenceRecord] = Field(default_factory=list)
    coverage: Optional[InvestigationCoverage] = None
    status: str = "COMPLETED"  # PROCESSING, COMPLETED, FAILED
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=get_now_utc)
    version: int = 1
    previous_investigation_id: Optional[str] = None

class InvestigationListItem(BaseModel):
    investigation_id: str
    original_claim: str
    organisation: str
    incident_category: str
    investigation_date: str
    verdict: str
    confidence_score: float
    total_sources: int
    official_sources_count: int
    created_at: datetime

class DashboardStats(BaseModel):
    total_investigations: int
    verified_claims: int
    likely_true_claims: int
    false_claims: int
    misleading_claims: int
    unverified_claims: int
    verdict_distribution: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    evidence_distribution: Dict[str, int]
    average_confidence: float

# ==========================================================
# EVENT INTELLIGENCE SCHEMAS
# ==========================================================

class SourceRegistryItem(BaseModel):
    source_id: str
    name: str
    domain: str
    source_type: str  # Official Company Announcement, Government Security Advisory, Established Cybersecurity Publication, Independent Security Researcher, General News Publication, Vulnerability Database
    feed_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    collection_method: str = "rss"  # rss, api, web_scrape
    base_reliability: float = 0.50
    is_official: bool = False
    enabled: bool = True
    polling_interval_minutes: int = 60
    last_polled_at: Optional[datetime] = None
    last_status: str = "IDLE"  # IDLE, SUCCESS, FAILED
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    created_at: datetime = Field(default_factory=get_now_utc)

class Article(BaseModel):
    article_id: str
    title: str
    url: str
    canonical_url: str
    domain: str
    publisher: str
    source_id: Optional[str] = None
    source_category: str = "General Web Source"
    reliability_score: float = 0.50
    is_official: bool = False
    content: str
    summary: Optional[str] = None
    content_hash: str  # SHA-256
    simhash: Optional[str] = None  # 64-bit hex for near-duplicate
    syndication_group_id: str = ""
    publication_date: Optional[str] = None
    retrieval_timestamp: datetime = Field(default_factory=get_now_utc)
    entities: Dict[str, Any] = Field(default_factory=dict)
    cves: List[str] = Field(default_factory=list)
    iocs: Dict[str, List[str]] = Field(default_factory=dict)
    relevance_score: float = 0.0
    is_cyber_relevant: bool = True
    assigned_event_id: Optional[str] = None
    created_at: datetime = Field(default_factory=get_now_utc)

class EventTimelineEntry(BaseModel):
    entry_id: str
    timestamp: datetime = Field(default_factory=get_now_utc)
    date_str: str
    entry_type: str = "DISCLOSURE"  # DISCLOSURE, ADVISORY, ANALYSIS, EXPLOITATION, WARNING, PATCH
    title: str
    description: str
    source_url: str
    source_title: str
    cves: List[str] = Field(default_factory=list)

class CyberEvent(BaseModel):
    event_id: str
    title: str
    description: str
    event_classification: str = "DISCLOSURE"  # DISCLOSURE, ADVISORY, ANALYSIS, EXPLOITATION, WARNING
    event_status: str = "ACTIVE"  # ACTIVE, RESOLVED, MONITORING
    first_seen: datetime = Field(default_factory=get_now_utc)
    latest_update: datetime = Field(default_factory=get_now_utc)
    embedding_centroid: Optional[List[float]] = None
    organizations: List[str] = Field(default_factory=list)
    vendors: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
    threat_actors: List[str] = Field(default_factory=list)
    cves: List[str] = Field(default_factory=list)
    iocs: Dict[str, List[str]] = Field(default_factory=dict)
    article_ids: List[str] = Field(default_factory=list)
    sources_count: int = 0
    independent_sources_count: int = 0
    timeline: List[EventTimelineEntry] = Field(default_factory=list)
    last_hdbscan_cluster: Optional[int] = None
    created_at: datetime = Field(default_factory=get_now_utc)

class EventAuditLog(BaseModel):
    audit_id: str
    timestamp: datetime = Field(default_factory=get_now_utc)
    total_events_audited: int
    total_articles_audited: int
    clusters_identified: int
    outliers_detected: int
    potential_merges: List[Dict[str, Any]] = Field(default_factory=list)
    potential_splits: List[Dict[str, Any]] = Field(default_factory=list)
    misassigned_articles: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class ArticleEventPair(BaseModel):
    pair_id: str
    article_id: str
    event_id: str
    s_sem: float
    s_ent: float
    s_temp: float
    s_ioc: float
    s_event: float = 0.0
    label: int = 0  # 1 = same event, 0 = different
    split: str = "train"  # train, val, test

class ModelMetadata(BaseModel):
    model_id: str
    model_version: str = "1.0.0"
    model_type: str = "logistic_regression"
    weights: Dict[str, float] = Field(default_factory=dict)  # s_sem, s_ent, s_temp, s_ioc, intercept
    is_trained: bool = False
    training_sample_count: int = 0
    metrics: Dict[str, float] = Field(default_factory=dict)  # precision, recall, f1, accuracy, brier_score
    confusion_matrix: Optional[List[List[int]]] = None
    trained_at: Optional[datetime] = None
    is_active: bool = True
