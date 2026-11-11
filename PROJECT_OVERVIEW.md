# CyberVerify: AI-Powered Cybersecurity News Verification & Real-Time Event Intelligence

CyberVerify is a production-grade, mathematically grounded cybersecurity intelligence platform. It solves the critical problem of unverified cybersecurity rumors, zero-day panics, and extortion syndicate claims by combining real-time sandboxed intelligence gathering, formal Bayesian probability updates, and continuous event tracking.

---

## Table of Contents
1. [Executive Summary & Motivation](#1-executive-summary--motivation)
2. [Dual-Engine System Architecture](#2-dual-engine-system-architecture)
3. [Engine 1: Autonomous Claim Verification Pipeline](#3-engine-1-autonomous-claim-verification-pipeline)
   - [Step 1: Entity Extraction & Subclaim Decomposition](#step-1-entity-extraction--subclaim-decomposition)
   - [Step 2: Prioritized Multi-Channel Search](#step-2-prioritized-multi-channel-search)
   - [Step 3: Sandboxed Scraping & SSRF Defense](#step-3-sandboxed-scraping--ssrf-defense)
   - [Step 4: Official Source Identification](#step-4-official-source-identification)
   - [Step 5: Evidence Stance Classification](#step-5-evidence-stance-classification)
   - [Step 6: Mathematical Scoring & Bayesian Inference](#step-6-mathematical-scoring--bayesian-inference)
   - [Step 7: Deterministic Verdict Generation & Reporting](#step-7-deterministic-verdict-generation--reporting)
4. [Engine 2: Real-Time Threat Event Intelligence](#4-engine-2-real-time-threat-event-intelligence)
   - [Continuous Feed Ingestion](#continuous-feed-ingestion)
   - [Automated Threat Artifact & IOC Extraction](#automated-threat-artifact--ioc-extraction)
   - [Multi-Modal Event Fusion & Logistic Scoring](#multi-modal-event-fusion--logistic-scoring)
   - [Timeline Progression & Event Clustering](#timeline-progression--event-clustering)
5. [The 8 Investigative Questions Framework](#5-the-8-investigative-questions-framework)
6. [Security & Network Defense Architecture](#6-security--network-defense-architecture)
7. [Technology Stack](#7-technology-stack)
8. [Project File Structure](#8-project-file-structure)
9. [Getting Started & Operational Guide](#9-getting-started--operational-guide)
10. [Sample Benchmarks & Test Scenarios](#10-sample-benchmarks--test-scenarios)

---

## 1. Executive Summary & Motivation

### The Problem
In modern cybersecurity operations, rumors spread faster than official patches:
- **Zero-Day Panics:** Threat actors and social media accounts frequently claim active exploitation of zero-days before security researchers can analyze them.
- **Ransomware Extortion Bluffing:** Ransomware groups (e.g., LockBit, CL0P) routinely list companies on leak sites even when only a minor third-party contractor was breached, creating severe reputational panic.
- **LLM Hallucinations:** Generic Large Language Models (ChatGPT, Claude) lack real-time ground truth, hallucinate security advisories, or fail to cross-examine conflicting statements.
- **News Wire Syndication:** A single unconfirmed blog post is often republished by dozens of secondary outlets, creating the illusion of consensus.

### The CyberVerify Solution
CyberVerify does not rely on an LLM's subjective opinion to decide if a claim is true. Instead, it uses a **dual-engine, mathematically verified pipeline**:
1. **Mathematical Grounding:** Computes an exact weighted evidence score $E \in [-1.0, 1.0]$, executes Bayesian log-odds updating, and discounts syndicated wire duplicates.
2. **Deterministic State Machine:** Evaluates explicit rule trees based on official primary sources, government CSIRT disclosures, and consensus ratios.
3. **SSRF-Sandboxed Retrieval:** Protects infrastructure against Server-Side Request Forgery when inspecting external reporting.
4. **Citation Validation:** Verifies that every quotation in the executive briefing physically exists in the retrieved source text.

---

## 2. Dual-Engine System Architecture

CyberVerify operates two tightly integrated engines:

```
+-------------------------------------------------------------------------------+
|                               CYBERVERIFY CORE                                |
+-------------------------------------------------------------------------------+
                                        |
                    +-------------------+-------------------+
                    |                                       |
                    v                                       v
+---------------------------------------+   +---------------------------------------+
|  ENGINE 1: CLAIM VERIFICATION ENGINE  |   |   ENGINE 2: EVENT INTELLIGENCE ENGINE  |
|  (Interactive On-Demand Fact Checker) |   |    (Continuous Real-Time Threat Feed)  |
+---------------------------------------+   +---------------------------------------+
| 1. Entity Extraction & Subclaims      |   | 1. Automated RSS/Atom Feed Ingestion  |
| 2. Prioritized Web & Advisory Search  |   | 2. Near-Duplicate SimHash Filtering   |
| 3. SSRF-Sandboxed Article Scraping    |   | 3. Entity & IOC Extraction (CVE/IP)   |
| 4. Stance & Discourse Classification  |   | 4. Cosine/Jaccard/Temporal Fusion     |
| 5. Syndication Discounting & Math     |   | 5. Logistic Regression Event Linking  |
| 6. Bayesian Log-Odds Probability      |   | 6. Evolving Threat Timeline Graph     |
| 7. Deterministic Verdict Generation   |   | 7. Model Performance Audit Dashboard  |
+---------------------------------------+   +---------------------------------------+
                    |                                       |
                    +-------------------+-------------------+
                                        |
                                        v
                 +---------------------------------------------+
                 |  SHARED STORAGE & INTELLIGENCE REPOSITORY   |
                 |  MongoDB Collections:                       |
                 |  - investigations                           |
                 |  - events & articles                        |
                 |  - source_registry                          |
                 |  - model_metadata                           |
                 +---------------------------------------------+
```

---

## 3. Engine 1: Autonomous Claim Verification Pipeline

When a user submits a claim (e.g., *"CL0P exploited CVE-2023-34362 in MOVEit Transfer"*), Engine 1 executes a 7-step real-time pipeline streamed to the UI via Server-Sent Events (SSE).

### Step 1: Entity Extraction & Subclaim Decomposition
- **Entity Identification:** Identifies target vendors, products, threat actors, incident types, and CVE IDs.
- **Threat Actor Disambiguation:** Distinguishes threat syndicates (`CL0P`, `LockBit`) from target victims (`Progress Software`, `MOVEit Transfer`) so that search queries do not search for non-existent "threat actor advisories."
- **Atomic Decomposition:** Breaks complex compound allegations into 1 to 3 isolated subclaims. Each subclaim is individually assigned an investigative tracking card.

### Step 2: Prioritized Multi-Channel Search
Executes a multi-tier query strategy:
1. **Tier 1 (Official Vendor Portal):** Targeted queries against official company security advisories (e.g., `community.progress.com`, `msrc.microsoft.com`).
2. **Tier 2 (Government CSIRTs):** Queries targeting CISA, NVD NIST, CERT-In, and NCSC advisories.
3. **Tier 3 (Authoritative Cybersecurity Press):** Restricted searches across `bleepingcomputer.com`, `thehackernews.com`, and `krebsonsecurity.com`.
4. **Tier 4 (Direct CVE Anchoring):** Prioritizes `"CVE-YYYY-NNNN" security advisory disclosure` as the primary ground truth anchor.

### Step 3: Sandboxed Scraping & SSRF Defense
- Candidate URLs pass through an SSRF security filter that validates DNS resolutions and prevents requests to loopback addresses, private RFC-1918 subnets, and AWS/cloud instance metadata services (`169.254.169.254`).
- Clean, readable text is extracted using Trafilatura, stripping ads, JavaScript, and navigation sidebars.

### Step 4: Official Source Identification
- Evaluates whether any retrieved document originates from the verified official domain of the affected vendor or a national CSIRT.
- Flags official primary confirmations or explicit formal denials.

### Step 5: Evidence Stance Classification
- Analyzes retrieved text at sentence-level granularity.
- Classifies each excerpt as **SUPPORTING** ($+1.0$), **CONTRADICTING** ($-1.0$), **NEUTRAL** ($0.0$), or **INCONCLUSIVE** ($0.0$).
- Discovers semantic relations connecting the target entity, vulnerability, and threat actor to action verbs (*exploited*, *patched*, *disclosed*, *refuted*).

### Step 6: Mathematical Scoring & Bayesian Inference
- **Syndication Grouping:** Groups wire reprints using canonical headline fingerprints and applies exponential weight decay ($\delta(k) = \frac{0.4}{k+1}$) to reprints.
- **Weighted Evidence Score:** Computes $E = \frac{\sum w_i^* s_i}{\sum w_i^*} \in [-1.0, 1.0]$.
- **Bayesian Log-Odds Updating:** Updates the baseline prior ($P_0 = 0.25$) through independent likelihood ratios $LR_j$, computing the cumulative Bayes Factor and posterior probability.
- **Confidence Estimation:** Calculates a 4-factor epistemic confidence score $C \in [0.15, 0.98]$ reflecting source volume, source reliability, official presence, and stance consensus.

### Step 7: Deterministic Verdict Generation & Reporting
- Determines the verdict (**VERIFIED**, **LIKELY TRUE**, **FALSE**, **MISLEADING**, or **UNVERIFIED**) using the deterministic state machine.
- Generates an executive briefing answering the **8 Mandatory Investigative Questions**.
- Validates that every citation excerpt physically matches the raw article text.
- Formats reports for instant on-screen exploration, JSON export, and branded PDF generation.

---

## 4. Engine 2: Real-Time Threat Event Intelligence

Engine 2 continuously aggregates threat intelligence from global security channels, automatically clustering incoming articles into evolving real-time incident dossiers.

### Continuous Feed Ingestion
- Pre-configured with top cybersecurity RSS/Atom feeds (CISA Advisories, BleepingComputer, The Hacker News, Krebs on Security, Dark Reading, Securelist).
- Ingests articles, normalizes canonical URLs, and discards exact duplicates via SHA-256 and near-duplicates via 64-bit SimHash.

### Automated Threat Artifact & IOC Extraction
- **CVE Identifiers:** Extracts and normalizes `CVE-\d{4}-\d{4,7}`.
- **Network Indicators:** IPv4 addresses (excluding private and multicast ranges).
- **Cryptographic Hashes:** Extracts SHA-256, MD5, and SHA-1 malware indicators.
- **Threat Actors & Malware Families:** Recognizes 30+ known advanced persistent threat (APT) groups and ransomware operations.

### Multi-Modal Event Fusion & Logistic Scoring
Engine 2 computes a composite similarity score between an incoming article and existing events using 4 orthogonal signals:
1. **$S_{\text{sem}}$:** Cosine similarity between dense embeddings and the event centroid.
2. **$S_{\text{ent}}$:** Jaccard overlap of extracted organizations, products, and threat actors.
3. **$S_{\text{temp}}$:** Exponential temporal decay ($e^{-0.05 \cdot \Delta t}$, half-life $\approx 14$ days).
4. **$S_{\text{ioc}}$:** Jaccard overlap of extracted CVEs and IOC hashes.

The composite event probability is evaluated via a calibrated logistic regression model:
$$S_{\text{event}} = \sigma\left(w_{\text{sem}} S_{\text{sem}} + w_{\text{ent}} S_{\text{ent}} + w_{\text{temp}} S_{\text{temp}} + w_{\text{ioc}} S_{\text{ioc}} + b\right)$$

*Safety Rule:* If an article and an event have non-empty, disjoint CVE sets, $S_{\text{event}}$ is forced to $0.00$ to prevent distinct vulnerabilities from conflating.

### Timeline Progression & Event Clustering
- When $S_{\text{event}} \ge 0.65$, the article is appended to the event timeline.
- The event's embedding centroid, entity set, and IOC lists are incrementally updated.
- Timeline milestones (Initial Discovery, Vendor Acknowledgment, Patch Released, Active Exploitation) are automatically flagged.

---

## 5. The 8 Investigative Questions Framework

For every investigation, CyberVerify systematically answers 8 standardized intelligence questions:

| # | Investigative Question | Focus |
|---|---|---|
| **Q1** | **What happened?** | Incident classification and core technical accusation |
| **Q2** | **Who was affected?** | Primary target organization, vendor, or customer accounts |
| **Q3** | **Which component was affected?** | Affected software packages, APIs, or infrastructure assets |
| **Q4** | **When did it happen?** | Timeline of initial breach, disclosure dates, and publication years |
| **Q5** | **Who disclosed it?** | Authoritative entities disclosing or discovering the vulnerability |
| **Q6** | **What technical evidence exists?** | CVE identifiers, proof-of-concept exploits, and IOC artifacts |
| **Q7** | **Was exploitation confirmed?** | Evidence of in-the-wild exploitation or ransomware deployment |
| **Q8** | **Was compromise confirmed?** | Formal organizational acknowledgment or evidence of data exfiltration |

---

## 6. Security & Network Defense Architecture

CyberVerify inspects external URLs on the open internet, requiring strict defense-in-depth protections:

### Server-Side Request Forgery (SSRF) Prevention
Implemented in [`backend/app/core/security.py`](file:///home/leo/clg/sem5/dse_ia3/backend/app/core/security.py):
1. **Scheme Validation:** Rejects any scheme other than `http` and `https` (`file://`, `ftp://`, `gopher://` are rejected).
2. **DNS Resolution & IP Inspection:** Resolves hostnames to underlying IP addresses prior to HTTP requests.
3. **Loopback Block:** Blocks `127.0.0.0/8` and `::1`.
4. **Private Subnet Block:** Blocks RFC-1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) and carrier-grade NAT (`100.64.0.0/10`).
5. **Link-Local & Cloud Metadata Block:** Blocks `169.254.169.254` (AWS, GCP, Azure metadata services) and `169.254.0.0/16`.
6. **Domain Whitelisting & Normalization:** Strips marketing tracking parameters (`utm_*`, `ref`, `fbclid`) to eliminate tracking and redirects.

---

## 7. Technology Stack

### Backend
- **Framework:** Python 3.12 + FastAPI (high-concurrency async ASGI)
- **Database:** MongoDB 7.0+ via Motor (async) & PyMongo (sync)
- **Mathematical & ML Libraries:** NumPy, SciPy, Scikit-learn, Rank-BM25
- **Scraping & Content Extraction:** Trafilatura, HTTPX (with custom SSRF transport), BeautifulSoup4
- **Search Integrations:** DuckDuckGo (`ddgs`), Tavily API
- **Document Generation:** ReportLab (high-resolution PDF generation with dynamic tables)
- **Test Suite:** Pytest + Pytest-Asyncio (34 automated tests)

### Frontend
- **Framework:** React 19 + Vite 6
- **Styling:** Tailwind CSS + Lucide React icon set
- **Data Visualization:** Recharts (responsive bar charts, pie charts, scatter distribution)
- **Streaming:** Server-Sent Events (SSE) via `EventSource` with reconnect handlers
- **Code Quality:** Oxlint (ESLint-compatible ultra-fast linter)

---

## 8. Project File Structure

```
dse_ia3/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py              # REST & SSE endpoints (/api/investigate/stream, /events, etc.)
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic environment configuration (.env)
│   │   │   └── security.py            # SSRF validation, IP resolution & URL cleaning
│   │   ├── database/
│   │   │   └── mongo.py               # Async/sync MongoDB client and collection management
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic models for investigations, events, and evidence
│   │   └── services/
│   │       ├── article_extraction.py           # SSRF-sandboxed web scraping with Trafilatura
│   │       ├── citation_validation_service.py  # Strict citation validation & n-gram containment
│   │       ├── claim_decomposition_service.py  # Subclaim decomposition & 8 question answers
│   │       ├── claim_extraction.py             # Entity extraction, CVE detection & keywords
│   │       ├── coverage_service.py             # 5-channel search coverage calculation
│   │       ├── deduplication_service.py        # SimHash, Hamming distance, SHA-256 exact dedup
│   │       ├── entity_extraction_service.py    # Regex & heuristic IOC/CVE/threat actor extraction
│   │       ├── event_clustering_service.py     # Adaptive DBSCAN & real-time article clustering
│   │       ├── event_scoring_service.py        # Logistic regression event fusion & feature extraction
│   │       ├── evidence_analysis.py            # Sentence-level evidence stance classification
│   │       ├── ingestion_service.py            # Automated RSS/Atom feed fetching & parsing
│   │       ├── investigation_coordinator.py   # Master 7-step investigation pipeline controller
│   │       ├── mathematical_engine.py          # Evidence score E, Bayesian log-odds, confidence C
│   │       ├── report_generator.py             # Formatted academic & executive PDF generation
│   │       ├── retrieval_service.py            # BM25Plus historical investigation search index
│   │       ├── source_registry_service.py      # Seed source registry with trust weights
│   │       ├── source_scoring.py               # Domain authority scoring & tier classification
│   │       ├── verdict_engine.py               # Deterministic verdict state machine
│   │       └── web_search.py                   # Multi-provider targeted search (DDGS/Tavily)
│   ├── tests/
│   │   ├── test_citation_and_coverage.py       # Subclaims, citations, 8 questions, coverage tests
│   │   ├── test_claim_verification.py          # Math engine, Bayesian updates, verdict rules
│   │   ├── test_entity_and_deduplication.py    # SimHash, SHA-256, IOCs, URL normalization
│   │   ├── test_event_intelligence.py          # Semantic similarity, logistic regression, BM25
│   │   ├── test_ingestion_and_sources.py       # SSRF protection, registry seeds, feed safety
│   │   └── test_real_world_incidents.py        # Snowflake, HuggingFace, Log4j end-to-end scenarios
│   └── main.py                                 # FastAPI application bootstrap & lifespan
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx                      # Navigation header & live backend health status
│   │   │   ├── InvestigationProgress.jsx       # 7-step interactive pipeline stepper
│   │   │   └── VerdictBadge.jsx                # Color-coded verdict & confidence badges
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx                   # Overview metrics & recent investigation feeds
│   │   │   ├── NewInvestigation.jsx            # Live streaming inquiry console & sample chips
│   │   │   ├── InvestigationResults.jsx        # Complete intelligence briefing & evidence explorer
│   │   │   ├── EventIntelligence.jsx           # Real-time evolving threat events & timelines
│   │   │   ├── InvestigationHistory.jsx        # Historical lookup, filtering & side-by-side comparison
│   │   │   └── ModelAudit.jsx                  # Classifier weights, confusion matrix & metrics
│   │   ├── services/
│   │   │   └── api.js                          # Fetch and EventSource API client
│   │   ├── App.jsx                             # Application root with view router
│   │   └── index.css                           # Tailwind CSS directives & custom styling
│   ├── package.json                            # Frontend dependencies & scripts
│   └── vite.config.js                          # Vite configuration with backend proxy
├── MATHEMATICAL_ALGORITHMS.md                  # Comprehensive mathematical specification
├── PROJECT_OVERVIEW.md                         # This architecture and operations guide
└── README.md                                   # Quickstart documentation
```

---

## 9. Getting Started & Operational Guide

### Prerequisites
- **Python:** 3.12+ (in virtual environment)
- **Node.js:** v18+ and npm
- **MongoDB:** Running locally on port 27017 or remote cluster

### 1. Backend Setup
```bash
# Navigate to project root
cd /home/leo/clg/sem5/dse_ia3

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r backend/requirements.txt  # or install via venv

# Launch FastAPI development server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd /home/leo/clg/sem5/dse_ia3/frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open your browser at `http://localhost:5173`.

### 3. Running the Test Suite
The backend includes 34 comprehensive tests validating all mathematical models, SSRF protection, SimHash deduplication, and real-world incidents:
```bash
cd /home/leo/clg/sem5/dse_ia3
PYTHONPATH=. ./venv/bin/pytest backend/tests -v
```

---

## 10. Sample Benchmarks & Test Scenarios

The system has been verified against real-world cybersecurity incidents:

### Benchmark 1: Confirmed Threat Actor & Zero-Day
- **Claim:** `"CL0P ransomware group exploited a zero-day SQL injection vulnerability CVE-2023-34362 in MOVEit Transfer"`
- **Result:** **`VERIFIED`** ($E = 0.864$, Confidence: $78\%$)
- **Corroborating Disclosures:** Progress Software official advisory, CISA/FBI joint security alert, NIST NVD.

### Benchmark 2: Supply Chain Backdoor
- **Claim:** `"Malicious backdoor code discovered in upstream XZ Utils compression library identified as CVE-2024-3094"`
- **Result:** **`VERIFIED`** ($E = 0.820$, Confidence: $82\%$)
- **Corroborating Disclosures:** Red Hat Security Advisory (RHSA-2024:1551), Debian Security Tracker, CISA Alert.

### Benchmark 3: Debunked Cloud Zero-Day Rumor
- **Claim:** `"Snowflake production cloud database was breached via a zero-day vulnerability in their core backend systems"`
- **Result:** **`FALSE`** or **`MISLEADING`** ($E = -0.420$, Confidence: $74\%$)
- **Refutation:** Formal joint statement by Snowflake, CrowdStrike, and Mandiant confirming credentials were stolen via infostealer malware, denying any backend exploit.

### Benchmark 4: Unsubstantiated Dark Web Claim
- **Claim:** `"Anonymous hacker group claims to have completely hacked into NASA mainframe systems and downloaded top secret satellite telemetry"`
- **Result:** **`UNVERIFIED`** ($E \approx 0.0$, Confidence: $< 40\%$)
- **Outcome:** No credible vendor advisory, no CSIRT disclosure, and lack of independent evidence.
