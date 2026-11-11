# Mathematical Foundations and Algorithms of CyberVerify

CyberVerify replaces subjective, hallucination-prone LLM verdicts with mathematically grounded, deterministic decision systems. The platform couples Bayesian probability theory, information retrieval ranking, locality-sensitive hashing, and multi-factor vector scoring across its verification and event intelligence engines.

This document details every mathematical algorithm, equation, statistical property, and operational parameter implemented in the codebase.

---

## Table of Contents
1. [Engine 1: Claim Verification Mathematics](#1-engine-1-claim-verification-mathematics)
   - [1.1 Source Reliability Weighting](#11-source-reliability-weighting)
   - [1.2 Evidence Stance Mapping](#12-evidence-stance-mapping)
   - [1.3 Syndication Decay Function](#13-syndication-decay-function)
   - [1.4 Normalized Weighted Evidence Score ($E$)](#14-normalized-weighted-evidence-score-e)
   - [1.5 Bayesian Log-Odds Evidence Updating](#15-bayesian-log-odds-evidence-updating)
   - [1.6 Multi-Factor Confidence Score ($C$)](#16-multi-factor-confidence-score-c)
   - [1.7 Deterministic Verdict State Machine](#17-deterministic-verdict-state-machine)
   - [1.8 Investigation Coverage Metric ($Cov$)](#18-investigation-coverage-metric-cov)
2. [Engine 2: Real-Time Event Intelligence Mathematics](#2-engine-2-real-time-event-intelligence-mathematics)
   - [2.1 Dense Semantic Cosine Similarity ($S_{\text{sem}}$)](#21-dense-semantic-cosine-similarity-s_textsem)
   - [2.2 Named Entity Jaccard Overlap ($S_{\text{ent}}$)](#22-named-entity-jaccard-overlap-s_textent)
   - [2.3 Threat Artifact / IOC Jaccard Overlap ($S_{\text{ioc}}$)](#23-threat-artifact--ioc-jaccard-overlap-s_textioc)
   - [2.4 Exponential Temporal Proximity Decay ($S_{\text{temp}}$)](#24-exponential-temporal-proximity-decay-s_texttemp)
   - [2.5 Calibrated Logistic Regression Event Fusion ($S_{\text{event}}$)](#25-calibrated-logistic-regression-event-fusion-s_textevent)
   - [2.6 Hard Disjoint CVE Consistency Constraint](#26-hard-disjoint-cve-consistency-constraint)
   - [2.7 Adaptive DBSCAN Event Clustering](#27-adaptive-dbscan-event-clustering)
3. [Deduplication & Information Retrieval Algorithms](#3-deduplication--information-retrieval-algorithms)
   - [3.1 64-Bit SimHash Locality-Sensitive Hashing](#31-64-bit-simhash-locality-sensitive-hashing)
   - [3.2 Bitwise Hamming Distance](#32-bitwise-hamming-distance)
   - [3.3 BM25Plus Lexical Retrieval Ranking](#33-bm25plus-lexical-retrieval-ranking)
   - [3.4 Exact SHA-256 & Headline Fingerprinting](#34-exact-sha-256--headline-fingerprinting)

---

## 1. Engine 1: Claim Verification Mathematics

### 1.1 Source Reliability Weighting
Every retrieved source $i$ is assigned a domain authority weight $w_i \in [0.10, 1.00]$ based on its publishing tier:

$$\text{Tier}(i) \implies w_i$$

| Source Tier | Examples | Nominal Weight $w_i$ |
|---|---|---|
| **Official Company Announcement** | `openai.com`, `microsoft.com`, `progress.com`, `cisco.com` | **$1.00$** |
| **Government Advisory / CSIRT / CERT** | `cisa.gov`, `nvd.nist.gov`, `ncsc.gov.uk`, `cert-in.org.in` | **$0.95$** |
| **Established Cybersecurity Press** | `bleepingcomputer.com`, `krebsonsecurity.com`, `thehackernews.com` | **$0.85$** |
| **Independent Security Researchers** | `googleprojectzero.blogspot.com`, `mandiant.com`, `unit42` | **$0.80$** |
| **General News Publications** | `reuters.com`, `bloomberg.com`, `apnews.com` | **$0.65$** |
| **General Web Sources** | Uncategorized public blogs, secondary outlets | **$0.50$** |
| **Community Platforms** | `reddit.com`, `x.com` / Twitter, Telegram, Forums | **$0.35$** |

---

### 1.2 Evidence Stance Mapping
Each extracted sentence or paragraph is classified into a ternary directional stance $s_i \in \{-1.0, 0.0, +1.0\}$:

$$s_i = \begin{cases} 
+1.0 & \text{if Stance} = \text{SUPPORTING (affirms the claim/exploit/breach)} \\
-1.0 & \text{if Stance} = \text{CONTRADICTING (explicitly refutes, denies, or debunks)} \\
0.0 & \text{if Stance} \in \{\text{NEUTRAL, INCONCLUSIVE (mentions without confirmation)}\}
\end{cases}$$

---

### 1.3 Syndication Decay Function
News outlets frequently syndicate identical wire reports (e.g., 20 blogs re-posting the same AP wire). Treating reprints as independent evidence causes false consensus. 

Articles are clustered into syndication groups $G_j$ using headline fingerprints and content hashes. Within cluster $G_j$, articles are ranked in descending order of reliability. The effective weight $w_{ij}^*$ of article $k$ (where $k=0$ is the cluster primary) is decayed:

$$w_{ij}^* = w_{ij} \cdot \delta(k)$$

$$\delta(k) = \begin{cases}
1.0 & \text{for } k = 0 \text{ (primary representative)} \\
\dfrac{0.4}{k + 1} & \text{for } k \ge 1 \text{ (syndicated reprints)}
\end{cases}$$

This guarantees that a single viral wire story republished 50 times cannot artificially inflate verification confidence.

---

### 1.4 Normalized Weighted Evidence Score ($E$)
The aggregate directional evidence score $E \in [-1.0, +1.0]$ is computed as the normalized dot product of effective weights and stance values:

$$E = \frac{\sum_{i=1}^N w_i^* \cdot s_i}{\sum_{i=1}^N w_i^*}$$

**Mathematical Properties:**
- **Boundary Invariance:** $-1.0 \le E \le +1.0$
- **Unanimity Property:** If all sources affirm the claim ($s_i = +1.0$), $E = +1.0$ regardless of individual source weights.
- **Symmetric Balance:** If supporting and contradicting evidence are of equal total weight, $E = 0.0$.
- **Null Safety:** If $\sum w_i^* = 0$, $E = 0.0$.

---

### 1.5 Bayesian Log-Odds Evidence Updating
To compute the true probabilistic posterior $P(\text{Claim} \mid \text{Evidence})$, CyberVerify uses Bayesian log-odds updating over independent source clusters.

#### A. Prior Probability
An unverified cybersecurity rumor on the internet has a conservative prior probability:
$$P_0 = P(\text{Claim}) = 0.25$$

The prior log-odds $\mathcal{O}_0$ is:
$$\mathcal{O}_0 = \ln \left( \frac{P_0}{1 - P_0} \right) = \ln \left( \frac{0.25}{0.75} \right) = \ln \left( \frac{1}{3} \right) \approx -1.0986$$

#### B. Likelihood Ratio (Bayes Factor Component)
For each independent source group $G_j$, the representative source with weight $w_j$ updates the likelihood ratio $LR_j$:

$$LR_j = \begin{cases}
1.0 + 4.0 \cdot w_j & \text{if } s_j = +1.0 \text{ (SUPPORTING)} \\
\dfrac{1.0}{1.0 + 6.0 \cdot w_j} & \text{if } s_j = -1.0 \text{ (CONTRADICTING)} \\
1.0 & \text{if } s_j = 0.0 \text{ (NEUTRAL / INCONCLUSIVE)}
\end{cases}$$

*Example Scaling:*
- An official vendor confirmation ($w=1.0$) yields $LR = 1.0 + 4.0(1.0) = 5.0$.
- An official vendor denial ($w=1.0$) yields $LR = \frac{1}{1 + 6.0(1.0)} = \frac{1}{7} \approx 0.143$.

#### C. Cumulative Bayes Factor & Posterior Log-Odds
The cumulative Bayes Factor $BF$ across $M$ independent source groups is:

$$BF = \prod_{j=1}^M LR_j$$

In log-odds space:

$$\mathcal{O}_{\text{post}} = \mathcal{O}_0 + \sum_{j=1}^M \ln(LR_j)$$

#### D. Sigmoid Posterior Probability Mapping
The final posterior probability $P(\text{Claim} \mid \mathbf{E}) \in [0.01, 0.99]$ is obtained via the logistic sigmoid transform:

$$P(\text{Claim} \mid \mathbf{E}) = \sigma(\mathcal{O}_{\text{post}}) = \frac{1}{1 + e^{-\mathcal{O}_{\text{post}}}}$$

---

### 1.6 Multi-Factor Confidence Score ($C$)
Confidence measures **epistemic certainty** (the quantity, diversity, and quality of evidence), strictly distinguished from claim veracity probability. 

The confidence score $C \in [0.15, 0.98]$ is composed of 4 orthogonal components:

$$C = \min\Big(0.98, \, \max\big(0.15, \, f_{\text{volume}} + f_{\text{quality}} + f_{\text{official}} + f_{\text{consensus}}\big)\Big)$$

Where each factor contributes up to $0.25$:

1. **Volume Factor ($f_{\text{volume}}$):** Rewards independent source diversity (saturates at 5+ independent clusters):
   $$f_{\text{volume}} = \min\left(1.0, \, \frac{M_{\text{groups}}}{5}\right) \times 0.25$$

2. **Quality Factor ($f_{\text{quality}}$):** Mean reliability of collected sources:
   $$f_{\text{quality}} = \left( \frac{1}{N} \sum_{i=1}^N w_i \right) \times 0.25$$

3. **Official / Primary Factor ($f_{\text{official}}$):**
   $$f_{\text{official}} = \begin{cases}
   0.25 & \text{if official vendor or government CSIRT advisory found} \\
   0.10 & \text{if secondary primary reporting found} \\
   0.05 & \text{otherwise}
   \end{cases}$$

4. **Consensus Factor ($f_{\text{consensus}}$):** Penalizes conflicting reports; rewards directional agreement among active sources ($N_{\text{active}} = N_{\text{sup}} + N_{\text{con}}$):
   $$f_{\text{consensus}} = \begin{cases}
   \dfrac{|N_{\text{sup}} - N_{\text{con}}|}{N_{\text{active}}} \times 0.25 & \text{if } N_{\text{active}} > 0 \\
   0.10 & \text{if all sources are neutral}
   \end{cases}$$

---

### 1.7 Deterministic Verdict State Machine
The verdict engine eliminates subjective drift through a deterministic decision matrix:

```
                            [ Collected Sources ]
                                      |
                      Is independent clusters < 2 OR
                   (Supporting == 0 AND Contradicting == 0)?
                                  /       \
                              YES           NO
                              /               \
                       [ UNVERIFIED ]    Has official denial OR
                                       (E <= -0.40 AND Contradicting >= 2)?
                                               /       \
                                           YES           NO
                                           /               \
                                      [ FALSE ]      (Official confirmation AND E >= 0.35) OR
                                                    (E >= 0.50 AND Conf >= 0.50 AND Supporting >= 2)?
                                                             /       \
                                                         YES           NO
                                                         /               \
                                                  [ VERIFIED ]     (Supporting > 0 AND Contradicting > 0 AND |E| < 0.40)?
                                                                         /       \
                                                                     YES           NO
                                                                     /               \
                                                              [ MISLEADING ]    (E >= 0.30 AND Groups >= 2 AND Supporting >= 2)?
                                                                                        /       \
                                                                                    YES           NO
                                                                                    /               \
                                                                             [ LIKELY TRUE ]   [ UNVERIFIED ]
```

---

### 1.8 Investigation Coverage Metric ($Cov$)
Coverage assesses the thoroughness of the investigative search space across 5 search channels:

$$Cov = \sum_{c=1}^5 \alpha_c \cdot I_c \quad \in [0.0, 1.0]$$

$$\alpha_1 = 0.25 \text{ (Official Vendor Portal)}, \quad \alpha_2 = 0.25 \text{ (Government CSIRT / CISA)},$$
$$\alpha_3 = 0.20 \text{ (Specialized Security Press)}, \quad \alpha_4 = 0.15 \text{ (Independent Researchers)},$$
$$\alpha_5 = 0.15 \text{ (Multi-Provider Web Search)}$$

$$I_c = \begin{cases} 1.0 & \text{if channel was queried and yielded candidate articles} \\ 0.0 & \text{otherwise} \end{cases}$$

---

## 2. Engine 2: Real-Time Event Intelligence Mathematics

Engine 2 clusters continuously ingested security articles into real-time evolving threat events.

### 2.1 Dense Semantic Cosine Similarity ($S_{\text{sem}}$)
Given dense article embedding $\mathbf{u} \in \mathbb{R}^D$ and event centroid $\mathbf{c} \in \mathbb{R}^D$:

$$S_{\text{sem}} = \cos(\mathbf{u}, \mathbf{c}) = \frac{\mathbf{u} \cdot \mathbf{c}}{\|\mathbf{u}\|_2 \cdot \|\mathbf{c}\|_2} = \frac{\sum_{k=1}^D u_k c_k}{\sqrt{\sum_{k=1}^D u_k^2} \sqrt{\sum_{k=1}^D c_k^2}}$$

Bounded to $[0.0, 1.0]$:
$$S_{\text{sem}} \leftarrow \max(0.0, \min(1.0, S_{\text{sem}}))$$

Centroids update incrementally when article $m$ joins event $E$:
$$\mathbf{c}_{t+1} = \frac{n \cdot \mathbf{c}_t + \mathbf{u}_m}{n + 1}$$

---

### 2.2 Named Entity Jaccard Overlap ($S_{\text{ent}}$)
Computes the set similarity of extracted organizations, products, and threat actors between article $A$ and event $E$:

$$S_{\text{ent}} = \mathcal{J}(E_A, E_E) = \frac{|E_A \cap E_E|}{|E_A \cup E_E|} \quad \in [0.0, 1.0]$$

If $|E_A \cup E_E| = 0$, then $S_{\text{ent}} = 0.0$.

---

### 2.3 Threat Artifact / IOC Jaccard Overlap ($S_{\text{ioc}}$)
Computes exact set overlap over technical artifacts (CVE IDs, IPv4 addresses, SHA-256 hashes, MD5 hashes, and SHA-1 hashes):

$$T_A = \text{CVEs}_A \cup \text{IPs}_A \cup \text{Hashes}_A$$
$$T_E = \text{CVEs}_E \cup \text{IPs}_E \cup \text{Hashes}_E$$

$$S_{\text{ioc}} = \mathcal{J}(T_A, T_E) = \frac{|T_A \cap T_E|}{|T_A \cup T_E|} \quad \in [0.0, 1.0]$$

---

### 2.4 Exponential Temporal Proximity Decay ($S_{\text{temp}}$)
Cybersecurity incidents follow rapid information dispersion. Articles published weeks apart are significantly less likely to describe the same acute event:

$$S_{\text{temp}} = e^{-\lambda \cdot \Delta t}$$

Where:
- $\Delta t = |t_{\text{article}} - t_{\text{event}}| \text{ in days}$
- $\lambda = 0.05 \text{ day}^{-1}$

**Half-Life Calculation:**
$$t_{1/2} = \frac{\ln(2)}{\lambda} = \frac{0.69315}{0.05} \approx 13.86 \text{ days}$$

- $\Delta t = 0 \text{ days} \implies S_{\text{temp}} = 1.000$
- $\Delta t = 7 \text{ days} \implies S_{\text{temp}} = e^{-0.35} \approx 0.7047$
- $\Delta t = 14 \text{ days} \implies S_{\text{temp}} = e^{-0.70} \approx 0.4966$
- $\Delta t = 60 \text{ days} \implies S_{\text{temp}} = e^{-3.00} \approx 0.0498$

---

### 2.5 Calibrated Logistic Regression Event Fusion ($S_{\text{event}}$)
The 4 similarity features form a vector $\mathbf{x} = [S_{\text{sem}}, S_{\text{ent}}, S_{\text{temp}}, S_{\text{ioc}}]^T$. The composite probability that an article belongs to an existing event is computed via logistic regression:

$$z = \mathbf{w}^T \mathbf{x} + b = w_{\text{sem}} S_{\text{sem}} + w_{\text{ent}} S_{\text{ent}} + w_{\text{temp}} S_{\text{temp}} + w_{\text{ioc}} S_{\text{ioc}} + b$$

$$S_{\text{event}} = P(\text{Same Event} \mid \mathbf{x}) = \sigma(z) = \frac{1}{1 + e^{-z}}$$

#### Default Calibrated Fallback Weights:
Until sufficient labeled pairs are collected, the engine uses mathematically calibrated priors:
- $w_{\text{sem}} = 0.40$ (Dense semantics carry the primary signal)
- $w_{\text{ent}} = 0.25$ (Entity overlap confirms target/vendor alignment)
- $w_{\text{ioc}} = 0.20$ (CVE/IOC matches provide high-precision linking)
- $w_{\text{temp}} = 0.15$ (Temporal alignment filters historic recurrences)
- $b = -0.10$ (Conservative negative bias)

#### Supervised Training & Calibration:
When trained on labeled article pairs, parameters $\mathbf{w}, b$ are optimized by minimizing L2-regularized binary cross-entropy:

$$\mathcal{L}(\mathbf{w}, b) = -\frac{1}{M}\sum_{i=1}^M \left[ y_i \ln(\sigma(z_i)) + (1 - y_i)\ln(1 - \sigma(z_i)) \right] + \frac{1}{2C}\|\mathbf{w}\|_2^2$$

Probabilities are evaluated using Brier score loss:
$$\text{Brier} = \frac{1}{M} \sum_{i=1}^M (\sigma(z_i) - y_i)^2$$

---

### 2.6 Hard Disjoint CVE Consistency Constraint
To prevent distinct security vulnerabilities affecting the same vendor from incorrectly collapsing into one event:

$$\text{If } |\text{CVEs}_A| > 0 \text{ AND } |\text{CVEs}_E| > 0 \text{ AND } \left(\text{CVEs}_A \cap \text{CVEs}_E = \emptyset\right):$$

$$S_{\text{event}} \leftarrow 0.00$$

*Example:* An advisory for `CVE-2023-34362` and an advisory for `CVE-2024-3094` will **never** be merged into the same event, even if both articles discuss SQL injection and file transfers.

---

### 2.7 Adaptive DBSCAN Event Clustering
For batch clustering of unassigned articles, CyberVerify implements Density-Based Spatial Clustering of Applications with Noise (DBSCAN).

#### Distance Metric:
$$D(u, v) = 1.0 - S_{\text{event}}(u, v)$$

#### Adaptive Epsilon ($\varepsilon$):
Instead of a fixed radius, $\varepsilon$ adapts to the corpus density:

$$\varepsilon = \text{Percentile}_{15}\Big(\{D(u, v) \mid u \neq v\}\Big)$$

Constrained within $\varepsilon \in [0.20, 0.45]$, with $\text{MinPts} = 2$.

---

## 3. Deduplication & Information Retrieval Algorithms

### 3.1 64-Bit SimHash Locality-Sensitive Hashing
To identify near-duplicate articles and syndicated content in $O(1)$ time, CyberVerify implements Charikar's 64-bit SimHash:

1. Tokenize text $T$ into meaningful words $W = \{w_1, w_2, \dots, w_k\}$.
2. Initialize an accumulator vector $\mathbf{V} = [0, 0, \dots, 0] \in \mathbb{R}^{64}$.
3. For each word $w \in W$:
   - Compute its 64-bit MD5 prefix hash $h(w) \in \{0, 1\}^{64}$.
   - For bit index $i \in [0, 63]$:
     $$V_i \leftarrow V_i + \begin{cases} +1 & \text{if bit } i \text{ of } h(w) = 1 \\ -1 & \text{if bit } i \text{ of } h(w) = 0 \end{cases}$$
4. Construct the 64-bit fingerprint $F \in \{0, 1\}^{64}$:
   $$F_i = \begin{cases} 1 & \text{if } V_i > 0 \\ 0 & \text{if } V_i \le 0 \end{cases}$$

---

### 3.2 Bitwise Hamming Distance
Given two SimHash fingerprints $F_1, F_2 \in \{0, 1\}^{64}$, their bitwise distance is:

$$D_H(F_1, F_2) = \sum_{i=0}^{63} (F_{1, i} \oplus F_{2, i}) = \text{popcount}(F_1 \oplus F_2)$$

**Deduplication Criterion:**
$$\text{IsNearDuplicate}(F_1, F_2) = \begin{cases} \text{True} & \text{if } D_H(F_1, F_2) \le 3 \\ \text{False} & \text{otherwise} \end{cases}$$

A Hamming distance $\le 3$ corresponds to approximately $\ge 95\%$ text similarity, catching minor rewrites, different bylines, or altered ad paragraphs.

---

### 3.3 BM25Plus Lexical Retrieval Ranking
Lexical matching across past investigations and event intelligence uses **BM25+** (Rank-BM25 with lower-bound correction $\delta$ to prevent zero-IDF distortion on short queries):

$$\text{Score}(D, Q) = \sum_{q_i \in Q} \text{IDF}(q_i) \cdot \left[ \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)} + \delta \right]$$

#### Parameters in CyberVerify:
- $k_1 = 1.5$ (Term frequency saturation parameter)
- $b = 0.75$ (Document length normalization parameter)
- $\delta = 1.00$ (BM25+ lower bound smoothing constant)

#### Inverse Document Frequency ($\text{IDF}$):
$$\text{IDF}(q_i) = \ln \left( \frac{N_{\text{docs}} - n(q_i) + 0.5}{n(q_i) + 0.5} + 1 \right)$$

Where:
- $f(q_i, D)$ is the frequency of keyword $q_i$ in document $D$.
- $|D|$ is the length of document $D$ in words.
- $\text{avgdl}$ is the average document length across the index.
- $N_{\text{docs}}$ is the total number of indexed documents.
- $n(q_i)$ is the number of documents containing keyword $q_i$.

---

### 3.4 Exact SHA-256 & Headline Fingerprinting

#### Content Exact Duplicate Hash:
$$H_{\text{content}} = \text{SHA-256}\Big(\text{NormalizeWhitespace}(\text{Lower}(T))\Big)$$

#### Headline Canonical Fingerprint:
To rapidly group wire syndications without full-body comparison:
1. Strip all non-alphanumeric characters.
2. Filter tokens with $\text{length} > 3$.
3. Sort the first 6 tokens alphabetically and join with hyphens.
4. Compute:
   $$H_{\text{headline}} = \text{MD5}\Big(\text{FingerprintTokenString}\Big)[:8]$$

Two articles with identical core headline keywords produce identical 8-character fingerprints and are mapped to the same syndication group in $O(1)$ time.

---

## 4. Summary of System Constants & Thresholds

| Symbol | Parameter | Value | Location in Codebase |
|---|---|---|---|
| $P_0$ | Base Prior Rumor Probability | $0.25$ | `mathematical_engine.py:8` |
| $\lambda$ | Temporal Decay Rate | $0.05 \text{ day}^{-1}$ | `event_scoring_service.py:26` |
| $D_H^{\text{max}}$ | Maximum Near-Duplicate Distance | $3 \text{ bits}$ | `deduplication_service.py:77` |
| $\delta(k)$ | Syndication Discount Constant | $0.4 / (k+1)$ | `mathematical_engine.py:188` |
| $k_1, b, \delta$ | BM25+ Constants | $1.5, 0.75, 1.0$ | `retrieval_service.py:34` |
| $E_{\text{verified}}$ | Verdict Verification Threshold | $\ge 0.50$ (or $0.35$ with official) | `verdict_engine.py:47` |
| $E_{\text{false}}$ | Verdict Denial Threshold | $\le -0.40$ (or official denial) | `verdict_engine.py:39` |
| $C_{\text{min}}, C_{\text{max}}$ | Confidence Bounding Limits | $[0.15, 0.98]$ | `mathematical_engine.py:140` |
