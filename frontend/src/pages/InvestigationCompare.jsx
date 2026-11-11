import React, { useState, useEffect } from 'react';
import { 
  Scale, ArrowLeft, RefreshCw, AlertTriangle, ArrowRight, 
  TrendingUp, TrendingDown, Minus, CheckCircle2, ShieldCheck, FileText 
} from 'lucide-react';
import { compareInvestigations } from '../services/api';
import VerdictBadge from '../components/VerdictBadge';

export default function InvestigationCompare({ id1, id2, onBack, onOpenReport }) {
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (id1 && id2) {
      setLoading(true);
      compareInvestigations(id1, id2)
        .then((res) => {
          setComparison(res);
          setError(null);
        })
        .catch((err) => {
          setError(err.message || 'Failed to compare reports');
        })
        .finally(() => setLoading(false));
    }
  }, [id1, id2]);

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <RefreshCw size={32} className="animate-spin mx-auto text-blue-600" />
        <h3 className="text-base font-bold text-slate-800">Generating Side-by-Side Comparison...</h3>
        <p className="text-xs text-slate-500">Calculating delta metrics between investigation iterations.</p>
      </div>
    );
  }

  if (error || !comparison) {
    return (
      <div className="py-16 text-center space-y-4 max-w-md mx-auto">
        <AlertTriangle size={36} className="mx-auto text-rose-500" />
        <h3 className="text-base font-bold text-slate-900">Comparison Failed</h3>
        <p className="text-xs text-slate-500">{error || 'Could not load both reports.'}</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold"
        >
          Back to History
        </button>
      </div>
    );
  }

  const { investigation_1: inv1, investigation_2: inv2, comparison_summary: delta } = comparison;

  return (
    <div className="space-y-6 pb-20">
      {/* Top Bar */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors cursor-pointer"
        >
          <ArrowLeft size={16} />
          <span>Back</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-500">Comparing Reports:</span>
          <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
            {inv1.investigation_id}
          </span>
          <span className="text-slate-400">vs</span>
          <span className="font-mono text-xs font-semibold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
            {inv2.investigation_id}
          </span>
        </div>
      </div>

      {/* Delta Metric Summary Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Scale size={18} className="text-blue-600" />
          Comparative Delta Analysis
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Verdict Shift</span>
            <div className="text-sm font-bold mt-1 text-slate-900">
              {delta.verdict_changed ? (
                <span className="text-amber-600 flex items-center gap-1">
                  <span>Verdict Changed</span>
                </span>
              ) : (
                <span className="text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 size={14} />
                  <span>Identical Verdict</span>
                </span>
              )}
            </div>
            <span className="text-[11px] text-slate-500 mt-0.5 block truncate">
              {inv1.verdict} → {inv2.verdict}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Confidence Delta</span>
            <div className="text-sm font-bold mt-1 text-slate-900 flex items-center gap-1">
              {delta.confidence_delta > 0 ? (
                <span className="text-emerald-600 flex items-center gap-1">
                  <TrendingUp size={14} />
                  +{Math.round(delta.confidence_delta * 100)}%
                </span>
              ) : delta.confidence_delta < 0 ? (
                <span className="text-rose-600 flex items-center gap-1">
                  <TrendingDown size={14} />
                  {Math.round(delta.confidence_delta * 100)}%
                </span>
              ) : (
                <span className="text-slate-600 flex items-center gap-1">
                  <Minus size={14} />
                  0%
                </span>
              )}
            </div>
            <span className="text-[11px] text-slate-500 mt-0.5 block">
              {Math.round(inv1.confidence_score * 100)}% → {Math.round(inv2.confidence_score * 100)}%
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Weighted Score Delta (ΔE)</span>
            <div className="text-sm font-bold mt-1 text-slate-900">
              {delta.score_delta > 0 ? `+${delta.score_delta}` : delta.score_delta}
            </div>
            <span className="text-[11px] text-slate-500 mt-0.5 block">
              {inv1.mathematical_results?.weighted_evidence_score} → {inv2.mathematical_results?.weighted_evidence_score}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Sources Delta</span>
            <div className="text-sm font-bold mt-1 text-slate-900">
              {delta.sources_delta >= 0 ? `+${delta.sources_delta} sources` : `${delta.sources_delta} sources`}
            </div>
            <span className="text-[11px] text-slate-500 mt-0.5 block">
              {inv1.sources?.length || 0} vs {inv2.sources?.length || 0} sources
            </span>
          </div>
        </div>
      </div>

      {/* Side by Side Comparative Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Report 1 Column */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Investigation #1</span>
              <div className="text-xs font-mono text-slate-700">{inv1.investigation_id}</div>
            </div>
            <button
              onClick={() => onOpenReport(inv1.investigation_id)}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800"
            >
              Open Full Report →
            </button>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Claim</span>
            <p className="text-sm font-semibold text-slate-900">"{inv1.original_claim}"</p>
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Verdict</span>
              <VerdictBadge verdict={inv1.verdict} size="lg" />
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Confidence</span>
              <span className="text-base font-extrabold text-slate-900">{Math.round(inv1.confidence_score * 100)}%</span>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Target Organisation:</span>
              <span className="font-semibold text-slate-900">{inv1.extracted_entities?.organisation}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Weighted Score (E):</span>
              <span className="font-mono font-bold text-slate-900">{inv1.mathematical_results?.weighted_evidence_score}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Bayesian Posterior P(H):</span>
              <span className="font-semibold text-slate-900">{Math.round((inv1.mathematical_results?.bayesian_analysis?.posterior_probability || 0) * 100)}%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Independent Clusters:</span>
              <span className="font-semibold text-slate-900">{inv1.mathematical_results?.independent_source_count}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Official Sources Found:</span>
              <span className="font-semibold text-slate-900">{inv1.mathematical_results?.official_sources_count}</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
            <span className="font-bold text-slate-900 block">AI Summary Conclusion:</span>
            <p className="text-[11px] leading-relaxed text-slate-600">
              {inv1.ai_summary?.final_assessment}
            </p>
          </div>
        </div>

        {/* Report 2 Column */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Investigation #2</span>
              <div className="text-xs font-mono text-slate-700">{inv2.investigation_id}</div>
            </div>
            <button
              onClick={() => onOpenReport(inv2.investigation_id)}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800"
            >
              Open Full Report →
            </button>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Claim</span>
            <p className="text-sm font-semibold text-slate-900">"{inv2.original_claim}"</p>
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Verdict</span>
              <VerdictBadge verdict={inv2.verdict} size="lg" />
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Confidence</span>
              <span className="text-base font-extrabold text-slate-900">{Math.round(inv2.confidence_score * 100)}%</span>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Target Organisation:</span>
              <span className="font-semibold text-slate-900">{inv2.extracted_entities?.organisation}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Weighted Score (E):</span>
              <span className="font-mono font-bold text-slate-900">{inv2.mathematical_results?.weighted_evidence_score}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Bayesian Posterior P(H):</span>
              <span className="font-semibold text-slate-900">{Math.round((inv2.mathematical_results?.bayesian_analysis?.posterior_probability || 0) * 100)}%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Independent Clusters:</span>
              <span className="font-semibold text-slate-900">{inv2.mathematical_results?.independent_source_count}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Official Sources Found:</span>
              <span className="font-semibold text-slate-900">{inv2.mathematical_results?.official_sources_count}</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
            <span className="font-bold text-slate-900 block">AI Summary Conclusion:</span>
            <p className="text-[11px] leading-relaxed text-slate-600">
              {inv2.ai_summary?.final_assessment}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
