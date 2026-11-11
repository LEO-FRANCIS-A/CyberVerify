import math
import numpy as np
import scipy.stats as stats
from typing import List, Dict, Any, Tuple
from backend.app.models.schemas import SourceItem, MathematicalResults, EvidenceDistribution, BayesianAnalysis

# Base prior probability for an unverified cybersecurity rumor on the internet
BASE_PRIOR_PROBABILITY = 0.25

STANCE_VALUES = {
    "SUPPORTING": 1.0,
    "CONTRADICTING": -1.0,
    "NEUTRAL": 0.0,
    "INCONCLUSIVE": 0.0
}

def calculate_evidence_distribution(sources: List[SourceItem]) -> EvidenceDistribution:
    """Calculates counts and exact percentages of each evidence stance."""
    total = len(sources)
    if total == 0:
        return EvidenceDistribution()
        
    sup = sum(1 for s in sources if s.evidence_classification == "SUPPORTING")
    con = sum(1 for s in sources if s.evidence_classification == "CONTRADICTING")
    neu = sum(1 for s in sources if s.evidence_classification == "NEUTRAL")
    inc = sum(1 for s in sources if s.evidence_classification == "INCONCLUSIVE")
    
    return EvidenceDistribution(
        supporting_count=sup,
        contradicting_count=con,
        neutral_count=neu,
        inconclusive_count=inc,
        supporting_percentage=round((sup / total) * 100, 1),
        contradicting_percentage=round((con / total) * 100, 1),
        neutral_percentage=round((neu / total) * 100, 1),
        inconclusive_percentage=round((inc / total) * 100, 1),
    )

def perform_bayesian_update(
    independent_groups: Dict[str, List[SourceItem]],
    prior_prob: float = BASE_PRIOR_PROBABILITY
) -> BayesianAnalysis:
    """
    Performs rigorous Bayesian evidence updating using independent source clusters.
    Avoids treating syndicated reprints as independent confirmations.
    """
    # Guard bounds for prior
    prior_prob = max(0.05, min(0.95, prior_prob))
    prior_log_odds = math.log(prior_prob / (1.0 - prior_prob))
    
    total_delta_log_odds = 0.0
    bayes_factor_product = 1.0
    weight_sum = 0.0

    for group_id, group_sources in independent_groups.items():
        # Representative source is the highest reliability source in the syndication group
        representative = max(group_sources, key=lambda s: s.reliability_score)
        w = representative.reliability_score
        stance = representative.evidence_classification
        weight_sum += w

        # Calculate likelihood ratio (Bayes Factor component)
        if stance == "SUPPORTING":
            # Higher reliability source provides stronger Bayes factor
            # e.g., w=1.0 -> LR=5.0, w=0.85 -> LR=4.4, w=0.35 -> LR=2.4
            lr = 1.0 + (4.0 * w)
        elif stance == "CONTRADICTING":
            # Refutation by high-reliability source is decisive
            # e.g., w=1.0 -> LR=0.14, w=0.85 -> LR=0.16
            lr = 1.0 / (1.0 + (6.0 * w))
        else:
            # Neutral / Inconclusive yields no shift
            lr = 1.0

        bayes_factor_product *= lr
        total_delta_log_odds += math.log(lr)

    posterior_log_odds = prior_log_odds + total_delta_log_odds
    
    # Sigmoid conversion to probability
    posterior_prob = 1.0 / (1.0 + math.exp(-posterior_log_odds))
    posterior_prob = round(max(0.01, min(0.99, posterior_prob)), 3)
    bayes_factor = round(bayes_factor_product, 3)

    explanation = (
        f"Prior probability P(Claim) started at {round(prior_prob * 100, 1)}%. "
        f"Evaluating {len(independent_groups)} independent source group(s) produced a cumulative "
        f"Bayes Factor of {bayes_factor}. "
        f"Posterior probability updated to {round(posterior_prob * 100, 1)}%."
    )

    return BayesianAnalysis(
        prior_probability=prior_prob,
        posterior_probability=posterior_prob,
        bayes_factor=bayes_factor,
        log_odds=round(posterior_log_odds, 3),
        evidence_weight_sum=round(weight_sum, 2),
        explanation=explanation
    )

def calculate_confidence_score(
    sources: List[SourceItem],
    independent_group_count: int,
    has_official_source: bool,
    weighted_score: float
) -> Tuple[float, str]:
    """
    Computes a multi-factor heuristic confidence indicator [0.0 - 1.0].
    Distinguished strictly from claim truth probability.
    Factors:
    1. Independent source cluster volume (up to 0.25)
    2. Average source reliability (up to 0.25)
    3. Primary/Official evidence presence (up to 0.25)
    4. Evidence consistency/consensus (up to 0.25)
    """
    if not sources:
        return 0.10, "No relevant sources collected to establish confidence."

    # 1. Volume factor (max at 5+ independent clusters)
    f_volume = min(1.0, independent_group_count / 5.0) * 0.25

    # 2. Source quality factor (mean reliability)
    avg_rel = np.mean([s.reliability_score for s in sources])
    f_quality = float(avg_rel) * 0.25

    # 3. Official / Primary factor
    f_official = 0.25 if has_official_source else 0.10 if any(s.is_primary_evidence for s in sources) else 0.05

    # 4. Consistency factor
    # Measures whether sources agree (+1 vs -1) or are heavily conflicting
    active_stances = [STANCE_VALUES[s.evidence_classification] for s in sources if s.evidence_classification in ("SUPPORTING", "CONTRADICTING")]
    if not active_stances:
        f_consistency = 0.10  # Only neutral/inconclusive
    else:
        # Distance from 0 relative to total
        agreement_ratio = abs(sum(active_stances)) / len(active_stances)
        f_consistency = agreement_ratio * 0.25

    total_confidence = round(f_volume + f_quality + f_official + f_consistency, 2)
    total_confidence = max(0.15, min(0.98, total_confidence))

    explanation = (
        f"Confidence is {int(total_confidence * 100)}% based on: "
        f"{independent_group_count} independent source cluster(s) (volume: {round(f_volume*4, 2)}), "
        f"mean source reliability of {round(avg_rel, 2)} (quality: {round(f_quality*4, 2)}), "
        f"{'official source presence (+0.25)' if has_official_source else 'secondary reporting only (+0.10)'}, "
        f"and evidence stance consensus ratio of {round(f_consistency*4, 2)}."
    )

    return total_confidence, explanation

def compute_mathematical_results(sources: List[SourceItem]) -> MathematicalResults:
    """
    Executes the full mathematical verification engine:
    - Weighted Evidence Score E = Σ(w_i * s_i) / Σw_i
    - Syndication clustering
    - Bayesian updating
    - Multi-factor confidence estimation
    """
    if not sources:
        return MathematicalResults(
            weighted_evidence_score=0.0,
            total_sources=0,
            independent_source_count=0,
            official_sources_count=0,
            evidence_distribution=EvidenceDistribution(),
            bayesian_analysis=None,
            confidence_score=0.10,
            confidence_explanation="No sources available for mathematical assessment.",
            reliability_weights_breakdown=[]
        )

    # 1. Group by syndication cluster to discount duplicate reprints
    groups: Dict[str, List[SourceItem]] = {}
    for s in sources:
        groups.setdefault(s.source_group_id, []).append(s)

    # 2. Calculate Weighted Evidence Score E = Σ(w_i * s_i) / Σw_i
    # For syndicated articles within same cluster, decay weights to prevent reprint dominance
    numerator = 0.0
    denominator = 0.0
    breakdown = []

    for group_id, group_items in groups.items():
        # Sort so highest reliability comes first
        sorted_items = sorted(group_items, key=lambda x: x.reliability_score, reverse=True)
        for idx, item in enumerate(sorted_items):
            decay = 1.0 if idx == 0 else (0.4 / (idx + 1))  # First item gets full weight, reprints decayed
            effective_weight = item.reliability_score * decay
            stance_val = STANCE_VALUES.get(item.evidence_classification, 0.0)
            
            numerator += (effective_weight * stance_val)
            denominator += effective_weight

            breakdown.append({
                "title": item.title,
                "publisher": item.publisher,
                "category": item.source_category,
                "nominal_weight": item.reliability_score,
                "effective_weight": round(effective_weight, 3),
                "stance": item.evidence_classification,
                "stance_value": stance_val,
                "contribution": round(effective_weight * stance_val, 3)
            })

    weighted_score = round(numerator / denominator, 3) if denominator > 0 else 0.0
    # Bound between -1.0 and 1.0
    weighted_score = max(-1.0, min(1.0, weighted_score))

    # 3. Evidence Distribution
    dist = calculate_evidence_distribution(sources)

    # 4. Bayesian Analysis
    bayesian = perform_bayesian_update(groups)

    # 5. Confidence Score
    official_count = sum(1 for s in sources if s.is_official)
    confidence, conf_expl = calculate_confidence_score(
        sources=sources,
        independent_group_count=len(groups),
        has_official_source=(official_count > 0),
        weighted_score=weighted_score
    )

    return MathematicalResults(
        weighted_evidence_score=weighted_score,
        total_sources=len(sources),
        independent_source_count=len(groups),
        official_sources_count=official_count,
        evidence_distribution=dist,
        bayesian_analysis=bayesian,
        confidence_score=confidence,
        confidence_explanation=conf_expl,
        reliability_weights_breakdown=breakdown
    )
