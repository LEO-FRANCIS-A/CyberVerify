import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldAlert, ShieldCheck, Download, RefreshCw, ArrowLeft, ExternalLink,
  Calendar, Building, Tag, FileText, CheckCircle2, XCircle, AlertTriangle,
  HelpCircle, ChevronDown, ChevronUp, Filter, Share2, Layers, Cpu, Award,
  SlidersHorizontal, Scale, BarChart2, Info, Radar, FileCheck, Check
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell, Legend, CartesianGrid, ScatterChart, Scatter, ZAxis
} from 'recharts';
import VerdictBadge from '../components/VerdictBadge';
import { 
  fetchInvestigation, reinvestigateClaim, getExportPdfUrl, getExportJsonUrl 
} from '../services/api';

export default function InvestigationResults({ investigationId, initialData, onBack, onCompareSelect }) {
  const [data, setData] = useState(initialData || null);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState(null);
  const [reinvestigating, setReinvestigating] = useState(false);
  
  // Filter for Evidence Explorer
  const [sourceFilter, setSourceFilter] = useState('ALL'); // ALL, SUPPORTING, CONTRADICTING, NEUTRAL, OFFICIAL
  const [showMathDetails, setShowMathDetails] = useState(true);

  // State to toggle subclaim 8-question cards (Must be at top level for React Rules of Hooks)
  const [expandedSubclaims, setExpandedSubclaims] = useState({});

  const toggleSubclaim = (id) => {
    setExpandedSubclaims((prev) => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Build evidence map by source_url and source_id (Must be at top level for React Rules of Hooks)
  const evidenceMap = useMemo(() => {
    const map = {};
    const evRecords = data?.evidence_records || [];
    evRecords.forEach((er) => {
      if (er.source_url) map[er.source_url] = er;
      if (er.canonical_url) map[er.canonical_url] = er;
    });
    return map;
  }, [data?.evidence_records]);

  useEffect(() => {
    if (investigationId && (!data || data.investigation_id !== investigationId)) {
      setLoading(true);
      fetchInvestigation(investigationId)
        .then((res) => {
          setData(res);
          setError(null);
        })
        .catch((err) => {
          setError(err.message || 'Failed to load investigation details');
        })
        .finally(() => setLoading(false));
    }
  }, [investigationId]);

  const handleReinvestigate = async () => {
    if (!data?.investigation_id) return;
    try {
      setReinvestigating(true);
      const updated = await reinvestigateClaim(data.investigation_id);
      setData(updated);
    } catch (err) {
      alert(`Reinvestigation error: ${err.message}`);
    } finally {
      setReinvestigating(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-4">
        <RefreshCw size={36} className="animate-spin mx-auto text-blue-600" />
        <h3 className="text-base font-bold text-slate-800">Loading Investigation Intelligence...</h3>
        <p className="text-xs text-slate-500">Retrieving mathematical metrics and classified sources from database.</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="py-16 text-center space-y-4 max-w-md mx-auto">
        <AlertTriangle size={40} className="mx-auto text-rose-500" />
        <h3 className="text-lg font-bold text-slate-900">Failed to Load Investigation</h3>
        <p className="text-xs text-slate-500">{error || 'Investigation could not be located.'}</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const {
    original_claim,
    extracted_entities: entities,
    incident_category,
    investigation_date,
    verdict,
    confidence_score,
    verdict_explanation,
    official_sources,
    sources = [],
    mathematical_results: math,
    ai_summary: ai,
    subclaims = [],
    evidence_records = [],
    coverage = null
  } = data;

  // Filter sources
  const filteredSources = sources.filter((s) => {
    if (sourceFilter === 'ALL') return true;
    if (sourceFilter === 'OFFICIAL') return s.is_official || (s.source_category && s.source_category.includes('Official'));
    return s.evidence_classification === sourceFilter;
  });

  // Recharts Data Prep
  const stanceBarData = [
    { name: 'Supporting', count: math?.evidence_distribution?.supporting_count || 0, fill: '#16A34A' },
    { name: 'Contradicting', count: math?.evidence_distribution?.contradicting_count || 0, fill: '#DC2626' },
    { name: 'Neutral', count: math?.evidence_distribution?.neutral_count || 0, fill: '#6366F1' },
    { name: 'Inconclusive', count: math?.evidence_distribution?.inconclusive_count || 0, fill: '#94A3B8' },
  ];

  const distributionPieData = [
    { name: 'Supporting', value: math?.evidence_distribution?.supporting_percentage || 0, fill: '#16A34A' },
    { name: 'Contradicting', value: math?.evidence_distribution?.contradicting_percentage || 0, fill: '#DC2626' },
    { name: 'Neutral', value: math?.evidence_distribution?.neutral_percentage || 0, fill: '#6366F1' },
    { name: 'Inconclusive', value: math?.evidence_distribution?.inconclusive_percentage || 0, fill: '#94A3B8' },
  ].filter(d => d.value > 0);

  // Group by category for category chart
  const categoryCounts = {};
  sources.forEach((s) => {
    categoryCounts[s.source_category] = (categoryCounts[s.source_category] || 0) + 1;
  });
  const categoryData = Object.entries(categoryCounts).map(([cat, count]) => ({
    category: cat.replace(' Established', '').replace(' Publication', '').replace(' Announcement', ''),
    count,
  }));

  // Timeline / Reliability Scatter
  const reliabilityScatterData = sources.map((s, idx) => ({
    index: idx + 1,
    reliability: s.reliability_score,
    publisher: s.publisher,
    stance: s.evidence_classification,
    isOfficial: s.is_official,
  }));

  return (
    <div className="space-y-8 pb-20">
      {/* Top Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors cursor-pointer"
        >
          <ArrowLeft size={16} />
          <span>Back to Dashboard</span>
        </button>

        <div className="flex flex-wrap items-center gap-2">
          {/* Compare Button */}
          {onCompareSelect && (
            <button
              onClick={() => onCompareSelect(data.investigation_id)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Scale size={14} className="text-slate-500" />
              <span>Compare Report</span>
            </button>
          )}

          {/* Reinvestigate Button */}
          <button
            onClick={handleReinvestigate}
            disabled={reinvestigating}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={reinvestigating ? "animate-spin text-blue-600" : "text-slate-500"} />
            <span>{reinvestigating ? "Re-verifying..." : "Reinvestigate"}</span>
          </button>

          {/* PDF Export */}
          <a
            href={getExportPdfUrl(data.investigation_id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <Download size={14} />
            <span>Export PDF Briefing</span>
          </a>

          {/* JSON Export */}
          <a
            href={getExportJsonUrl(data.investigation_id)}
            download
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <span>JSON</span>
          </a>
        </div>
      </div>

      {/* SECTION 1: VERDICT CARD */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Official Intelligence Determination
              </span>
              <span className="text-slate-300">•</span>
              <div className="flex items-center gap-1 text-xs text-slate-500">
                <Calendar size={13} />
                <span>{investigation_date}</span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <VerdictBadge verdict={verdict} size="xl" />
              <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-100 border border-slate-200">
                <span className="text-xs text-slate-500 font-medium">Confidence Score:</span>
                <span className="text-sm font-extrabold text-slate-900">{Math.round(confidence_score * 100)}%</span>
              </div>
            </div>

            <p className="text-sm sm:text-base text-slate-700 leading-relaxed font-medium">
              {verdict_explanation}
            </p>
          </div>

          {/* Mathematical Gauge Box */}
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 sm:p-5 text-center min-w-[220px] shrink-0">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
              Weighted Evidence Score
            </span>
            <div className="text-3xl font-black text-slate-900 tracking-tight">
              {math?.weighted_evidence_score > 0 ? `+${math.weighted_evidence_score}` : math?.weighted_evidence_score}
            </div>
            <span className="text-[10px] text-slate-400 block mt-0.5">Scale: -1.0 (Refuted) to +1.0 (Confirmed)</span>

            <div className="mt-3 pt-3 border-t border-slate-200/60 grid grid-cols-2 gap-2 text-left text-xs">
              <div>
                <span className="text-slate-400 text-[10px] block">Independent Clusters:</span>
                <span className="font-bold text-slate-800">{math?.independent_source_count || 0}</span>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] block">Posterior P(H):</span>
                <span className="font-bold text-slate-800">{Math.round((math?.bayesian_analysis?.posterior_probability || 0) * 100)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 2: CLAIM OVERVIEW */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <FileText size={18} className="text-blue-600" />
          Claim Overview & Extracted Entities
        </h2>

        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm font-semibold text-slate-900">
            "{original_claim}"
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-xl border border-slate-200 bg-white">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Target Organisation</span>
              <span className="text-sm font-bold text-slate-900 mt-1 block flex items-center gap-1.5">
                <Building size={14} className="text-blue-600" />
                {entities?.organisation || 'Not specified'}
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-white">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Incident Category</span>
              <span className="text-sm font-bold text-slate-900 mt-1 block flex items-center gap-1.5">
                <Tag size={14} className="text-indigo-600" />
                {incident_category}
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-white">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Affected Products / CVEs</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {entities?.affected_products?.length > 0 ? (
                  entities.affected_products.map((p, i) => (
                    <span key={i} className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                      {p}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500">General Infrastructure</span>
                )}
              </div>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-white">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Target Keywords</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {entities?.search_keywords?.slice(0, 3).map((kw, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 2.5: INVESTIGATION COVERAGE INDICATOR */}
      {coverage && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <Radar size={18} className="text-blue-600" />
                <h2 className="text-base font-bold text-slate-900">Investigation Coverage Indicator</h2>
                <span className="text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                  {Math.round(coverage.coverage_percentage || 0)}% Evaluated
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Completeness of evidence inquiry across official vendor, government CERT, and cyber press channels.
              </p>
            </div>
            
            {/* Progress bar */}
            <div className="w-full sm:w-48 bg-slate-100 rounded-full h-2.5 overflow-hidden border border-slate-200">
              <div
                className={`h-2.5 rounded-full transition-all duration-500 ${
                  coverage.coverage_percentage >= 70 ? 'bg-emerald-500' :
                  coverage.coverage_percentage >= 40 ? 'bg-blue-500' : 'bg-amber-500'
                }`}
                style={{ width: `${Math.min(100, Math.max(5, coverage.coverage_percentage || 0))}%` }}
              />
            </div>
          </div>

          {/* Channel Status Matrix */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
            {[
              { id: 'OFFICIAL_VENDOR', label: 'Official Vendor Portal', desc: 'Target org advisories & releases' },
              { id: 'GOVERNMENT_CSIRT', label: 'Government CSIRT', desc: 'CISA, CERT-In, NVD catalogues' },
              { id: 'SECURITY_PRESS', label: 'Security Press & Intel', desc: 'Authoritative reporting & blogs' },
              { id: 'COMMUNITY_FORUM', label: 'Community & Open Intel', desc: 'OSINT & researcher discourse' }
            ].map((ch) => {
              const status = coverage.channel_statuses?.[ch.id] || 'NOT_CHECKED';
              const statusConfig = {
                CHECKED_FOUND: { label: 'Evidence Confirmed', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200', icon: CheckCircle2, iconColor: 'text-emerald-600' },
                CHECKED_NOT_FOUND: { label: 'Checked (No Notice)', bg: 'bg-amber-50 text-amber-800 border-amber-200', icon: AlertTriangle, iconColor: 'text-amber-600' },
                NOT_ACCESSIBLE: { label: 'Access Blocked', bg: 'bg-rose-50 text-rose-800 border-rose-200', icon: XCircle, iconColor: 'text-rose-600' },
                NOT_CHECKED: { label: 'Not Queried', bg: 'bg-slate-100 text-slate-700 border-slate-200', icon: HelpCircle, iconColor: 'text-slate-500' }
              };
              const cfg = statusConfig[status] || statusConfig.NOT_CHECKED;
              const IconComp = cfg.icon;

              return (
                <div key={ch.id} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{ch.label}</span>
                    <IconComp size={14} className={cfg.iconColor} />
                  </div>
                  <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-md border ${cfg.bg}`}>
                    {cfg.label}
                  </span>
                  <span className="text-[10px] text-slate-400 block">{ch.desc}</span>
                </div>
              );
            })}
          </div>

          {/* Explanation & Identified Gaps */}
          {coverage.coverage_explanation && (
            <div className="p-3 bg-blue-50/60 border border-blue-200 rounded-xl text-xs text-blue-900 leading-relaxed">
              <span className="font-bold">Investigation Audit: </span>
              {coverage.coverage_explanation}
            </div>
          )}

          {coverage.missing_source_coverage?.length > 0 && (
            <div className="p-3 bg-amber-50/50 border border-amber-200 rounded-xl space-y-1">
              <span className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                <AlertTriangle size={13} className="text-amber-600" />
                Coverage Gaps Identified:
              </span>
              <ul className="list-disc pl-5 space-y-0.5 text-[11px] text-amber-800">
                {coverage.missing_source_coverage.map((gap, i) => (
                  <li key={i}>{gap}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* SECTION 2.6: CLAIM DECOMPOSITION & 8 INVESTIGATIVE QUESTIONS */}
      {subclaims && subclaims.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileCheck size={18} className="text-blue-600" />
                Claim Decomposition & 8 Mandatory Investigative Questions
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Atomic breakdown of factual subclaims with systematic verification answers.
              </p>
            </div>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
              {subclaims.length} Subclaim{subclaims.length > 1 ? 's' : ''} Evaluated
            </span>
          </div>

          <div className="space-y-4">
            {subclaims.map((sc, idx) => {
              const isExpanded = expandedSubclaims[sc.subclaim_id] ?? true;
              const qLabels = [
                { key: 'incident_occurrence', label: '1. Incident Occurrence', q: 'Did the cybersecurity incident actually take place?' },
                { key: 'target_identity', label: '2. Target Confirmation', q: 'Is the specific targeted organization or entity confirmed?' },
                { key: 'attack_vector', label: '3. Vector / Mechanism', q: 'What mechanism, exploit, or vector was utilized?' },
                { key: 'impact_scale', label: '4. Impact & Scale', q: 'What was the scope of data theft, downtime, or damage?' },
                { key: 'attribution', label: '5. Threat Attribution', q: 'Is the threat actor or source of attack substantiated?' },
                { key: 'remediation_patch', label: '6. Remediation / Patch', q: 'Have mitigation guidance, workarounds, or patches been published?' },
                { key: 'official_acknowledgement', label: '7. Official Position', q: 'Has the vendor or national CERT issued an official statement?' },
                { key: 'timeline_consistency', label: '8. Timeline Consistency', q: 'Are disclosed incident timestamps consistent across reports?' },
              ];

              return (
                <div
                  key={sc.subclaim_id || idx}
                  className="rounded-xl border border-slate-200 bg-slate-50/40 overflow-hidden transition-all"
                >
                  <div
                    onClick={() => toggleSubclaim(sc.subclaim_id)}
                    className="p-4 bg-white flex flex-wrap items-center justify-between gap-3 cursor-pointer hover:bg-slate-50/80 transition-colors border-b border-slate-100"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-lg bg-blue-100 text-blue-800 text-xs font-extrabold flex items-center justify-center shrink-0">
                        {idx + 1}
                      </span>
                      <div>
                        <div className="text-xs font-bold text-slate-900">{sc.subclaim_text}</div>
                        <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-slate-500">
                          {sc.target_org && <span>Target: <strong className="text-slate-700">{sc.target_org}</strong></span>}
                          {sc.incident_type && <span>• Type: <strong className="text-slate-700">{sc.incident_type}</strong></span>}
                          {sc.cve && <span className="font-mono text-blue-600 bg-blue-50 px-1 rounded">{sc.cve}</span>}
                          {sc.threat_actor && <span>• Actor: <strong className="text-slate-700">{sc.threat_actor}</strong></span>}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        sc.status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' :
                        sc.status === 'LIKELY TRUE' ? 'bg-blue-50 text-blue-800 border-blue-200' :
                        sc.status === 'FALSE' ? 'bg-rose-50 text-rose-800 border-rose-200' :
                        sc.status === 'MISLEADING' ? 'bg-amber-50 text-amber-800 border-amber-200' :
                        'bg-slate-100 text-slate-700 border-slate-200'
                      }`}>
                        {sc.status} ({Math.round((sc.confidence || confidence_score || 0) * 100)}%)
                      </span>
                      {isExpanded ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3 bg-slate-50/50">
                      {qLabels.map(({ key, label, q }) => {
                        const answer = sc.answers?.[key];
                        return (
                          <div key={key} className="p-3 bg-white rounded-lg border border-slate-200/80 space-y-1">
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="font-bold text-slate-800">{label}</span>
                            </div>
                            <p className="text-[10px] text-slate-400">{q}</p>
                            <p className="text-xs text-slate-700 font-medium pt-1">
                              {answer || 'Evidence inconclusive on this question.'}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SECTION 3: EVIDENCE STATISTICS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs text-center">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Sources</span>
          <div className="text-xl font-bold text-slate-900 mt-1">{math?.total_sources || 0}</div>
          <span className="text-[10px] text-slate-400">Scraped & analyzed</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs text-center">
          <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider block">Supporting</span>
          <div className="text-xl font-bold text-emerald-700 mt-1">{math?.evidence_distribution?.supporting_count || 0}</div>
          <span className="text-[10px] text-slate-400">{math?.evidence_distribution?.supporting_percentage || 0}% of evidence</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs text-center">
          <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider block">Contradicting</span>
          <div className="text-xl font-bold text-rose-700 mt-1">{math?.evidence_distribution?.contradicting_count || 0}</div>
          <span className="text-[10px] text-slate-400">{math?.evidence_distribution?.contradicting_percentage || 0}% of evidence</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs text-center">
          <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider block">Neutral</span>
          <div className="text-xl font-bold text-indigo-700 mt-1">{math?.evidence_distribution?.neutral_count || 0}</div>
          <span className="text-[10px] text-slate-400">{math?.evidence_distribution?.neutral_percentage || 0}% of evidence</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs text-center">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Independent Groups</span>
          <div className="text-xl font-bold text-slate-800 mt-1">{math?.independent_source_count || 0}</div>
          <span className="text-[10px] text-slate-400">Deduplicated clusters</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs text-center">
          <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block">Official Sources</span>
          <div className="text-xl font-bold text-blue-700 mt-1">{math?.official_sources_count || 0}</div>
          <span className="text-[10px] text-slate-400">Company & Gov CERT</span>
        </div>
      </div>

      {/* SECTION 4: EVIDENCE VISUALISATION */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <BarChart2 size={18} className="text-blue-600" />
          Interactive Evidence Visualisation
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart A: Supporting vs Contradicting */}
          <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50">
            <h3 className="text-xs font-bold text-slate-700 mb-3">Supporting vs. Contradicting Count</h3>
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stanceBarData} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748B' }} allowDecimals={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: '8px', fontSize: '11px' }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {stanceBarData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart B: Evidence Distribution Pie */}
          <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50">
            <h3 className="text-xs font-bold text-slate-700 mb-3">Evidence Distribution Percentage</h3>
            <div className="h-52 w-full">
              {distributionPieData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={distributionPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {distributionPieData.map((entry, index) => (
                        <Cell key={`slice-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(val) => [`${val}%`, 'Share']}
                      contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: '8px', fontSize: '11px' }}
                    />
                    <Legend verticalAlign="bottom" height={32} iconType="circle" wrapperStyle={{ fontSize: '10px' }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">No data</div>
              )}
            </div>
          </div>

          {/* Chart C: Source Category Distribution */}
          <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50">
            <h3 className="text-xs font-bold text-slate-700 mb-3">Source Categories Evaluated</h3>
            <div className="h-52 w-full">
              {categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categoryData} layout="vertical" margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                    <XAxis type="number" tick={{ fontSize: 10, fill: '#64748B' }} allowDecimals={false} />
                    <YAxis dataKey="category" type="category" tick={{ fontSize: 9, fill: '#475569' }} width={90} />
                    <Tooltip contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: '8px', fontSize: '11px' }} />
                    <Bar dataKey="count" fill="#4F46E5" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">No data</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 5: OFFICIAL SOURCES */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck size={18} className="text-emerald-600" />
            Official Vendor Announcements & Government Security Advisories
          </h2>
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
            official_sources?.official_sources_found?.length > 0
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'bg-amber-50 text-amber-700 border border-amber-200'
          }`}>
            {official_sources?.official_sources_found?.length > 0 ? 'Official Statement Found' : 'No Official Advisory Found'}
          </span>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          {official_sources?.status_summary}
        </p>

        {official_sources?.official_sources_found?.length > 0 ? (
          <div className="space-y-2 mt-3">
            <span className="text-xs font-bold text-slate-700">Verified Official Portals Checked:</span>
            {official_sources.official_sources_found.map((src, i) => (
              <div key={i} className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-200 flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-slate-900">{src.title}</div>
                  <div className="text-[11px] text-slate-500">{src.publisher} • Stance: {src.stance}</div>
                </div>
                <a
                  href={src.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-900"
                >
                  <span>Open Advisory</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 space-y-1">
            <div className="font-semibold text-slate-700">Authoritative Channels Queried:</div>
            <ul className="list-disc pl-5 space-y-0.5 text-[11px]">
              {official_sources?.official_sources_checked?.map((q, i) => (
                <li key={i} className="font-mono text-slate-600">{q}</li>
              )) || <li>Target organization security portal and CISA advisory feeds</li>}
            </ul>
          </div>
        )}
      </div>

      {/* SECTION 6: EVIDENCE EXPLORER */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Layers size={18} className="text-blue-600" />
              Evidence Explorer ({filteredSources.length} Sources)
            </h2>
            <p className="text-xs text-slate-500">Individual article classifications, passages, and reliability scores</p>
          </div>

          {/* Stance Filter Buttons */}
          <div className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-100 rounded-xl">
            {[
              { id: 'ALL', label: 'All' },
              { id: 'SUPPORTING', label: 'Supporting' },
              { id: 'CONTRADICTING', label: 'Contradicting' },
              { id: 'NEUTRAL', label: 'Neutral' },
              { id: 'OFFICIAL', label: 'Official Only' },
            ].map((btn) => (
              <button
                key={btn.id}
                onClick={() => setSourceFilter(btn.id)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  sourceFilter === btn.id
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* Source Cards */}
        <div className="space-y-3 pt-2">
          {filteredSources.length > 0 ? (
            filteredSources.map((source) => {
              const stanceColors = {
                SUPPORTING: 'bg-emerald-50 text-emerald-700 border-emerald-200',
                CONTRADICTING: 'bg-rose-50 text-rose-700 border-rose-200',
                NEUTRAL: 'bg-indigo-50 text-indigo-700 border-indigo-200',
                INCONCLUSIVE: 'bg-slate-100 text-slate-700 border-slate-200',
              };

              const evRecord = evidenceMap[source.url] || (evidence_records || []).find(e => e.evidence_id === source.source_id);
              const citationStatus = evRecord?.citation_validation_status || (source.extracted_passages?.length > 0 ? 'VALIDATED' : 'UNCONFIRMED_PASSAGE');

              const citationBadges = {
                VALIDATED: { label: 'Passage Verified', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200', icon: CheckCircle2, iconColor: 'text-emerald-600' },
                UNCONFIRMED_PASSAGE: { label: 'Unconfirmed Passage', bg: 'bg-amber-50 text-amber-800 border-amber-200', icon: AlertTriangle, iconColor: 'text-amber-600' },
                URL_INACCESSIBLE: { label: 'URL Inaccessible', bg: 'bg-slate-100 text-slate-700 border-slate-200', icon: XCircle, iconColor: 'text-slate-500' },
                REJECTED_UNSUPPORTED: { label: 'Rejected Unsupported', bg: 'bg-rose-50 text-rose-800 border-rose-200', icon: XCircle, iconColor: 'text-rose-600' }
              };
              const citCfg = citationBadges[citationStatus] || citationBadges.VALIDATED;
              const CitIcon = citCfg.icon;

              return (
                <div
                  key={source.source_id}
                  className="p-4 rounded-xl border border-slate-200 hover:border-slate-300 bg-white transition-all space-y-2.5 shadow-2xs"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900">{source.publisher}</span>
                      <span className="text-[10px] text-slate-400">•</span>
                      <span className="text-xs text-slate-500">{source.source_category}</span>
                      {source.is_official && (
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                          Official
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      {/* Citation Validation Badge */}
                      <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md border ${citCfg.bg}`}>
                        <CitIcon size={11} className={citCfg.iconColor} />
                        {citCfg.label}
                      </span>

                      {/* Optional NLI Score */}
                      {evRecord?.nli_entailment_score !== null && evRecord?.nli_entailment_score !== undefined && (
                        <span className="text-[10px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-mono">
                          NLI: {Math.round(evRecord.nli_entailment_score * 100)}%
                        </span>
                      )}

                      <div className="flex items-center gap-1 text-[11px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                        <span>Reliability:</span>
                        <span className="font-bold text-slate-800">{source.reliability_score}</span>
                      </div>
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${stanceColors[source.evidence_classification] || 'bg-slate-100 text-slate-700'}`}>
                        {source.evidence_classification}
                      </span>
                    </div>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 hover:text-blue-600 transition-colors">
                    <a href={source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1">
                      <span>{source.title}</span>
                      <ExternalLink size={12} className="shrink-0 text-slate-400" />
                    </a>
                  </h4>

                  {/* Extracted Key Passages */}
                  {source.extracted_passages && source.extracted_passages.length > 0 && (
                    <div className="bg-slate-50 rounded-lg p-3 border-l-2 border-blue-500 space-y-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                        Extracted Evidence Passage:
                      </span>
                      {source.extracted_passages.map((passage, idx) => (
                        <p key={idx} className="text-xs text-slate-700 italic">
                          "{passage}"
                        </p>
                      ))}
                    </div>
                  )}

                  <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-1 gap-2">
                    <div className="flex items-center gap-2">
                      <span>Cluster ID: {source.source_group_id}</span>
                      {evRecord?.canonical_url && evRecord.canonical_url !== source.url && (
                        <span className="text-[10px] text-slate-400 truncate max-w-[200px]" title={evRecord.canonical_url}>
                          • Canonical: {evRecord.canonical_url}
                        </span>
                      )}
                    </div>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
                    >
                      <span>Read Original Source</span>
                      <ExternalLink size={11} />
                    </a>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-8 text-center text-xs text-slate-400">
              No sources match the selected filter.
            </div>
          )}
        </div>
      </div>

      {/* SECTION 7: MATHEMATICAL ANALYSIS */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Scale size={18} className="text-blue-600" />
            Mathematical & Bayesian Verification Calculations
          </h2>
          <button
            onClick={() => setShowMathDetails(!showMathDetails)}
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 cursor-pointer"
          >
            <span>{showMathDetails ? 'Collapse Details' : 'Expand Formulations'}</span>
            {showMathDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          CyberVerify calculates evidence mathematically rather than guessing. The final verdict is driven strictly by weighted evidence sums, syndication discounting, and Bayesian log-odds updating.
        </p>

        {showMathDetails && (
          <div className="space-y-4 pt-2">
            {/* Formula Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Formula 1: Weighted Score */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800">1. Weighted Evidence Score (E)</span>
                  <span className="font-mono text-xs font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                    E = Σ(wᵢ × sᵢ) / Σwᵢ
                  </span>
                </div>
                <p className="text-[11px] text-slate-600">
                  Where wᵢ is source reliability weight (Official: 1.0, Gov: 0.95, Cyber Press: 0.85, General News: 0.65, Social: 0.35) and sᵢ is stance (Supporting: +1, Contradicting: -1, Neutral: 0). Syndicated reprints are decayed to prevent duplicate amplification.
                </p>
                <div className="pt-1 text-xs font-bold text-slate-900">
                  Calculated Result: <span className="text-blue-600">{math?.weighted_evidence_score}</span>
                </div>
              </div>

              {/* Formula 2: Bayesian Analysis */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800">2. Bayesian Evidence Updating</span>
                  <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded">
                    P(H|E) = σ(logit(P(H)) + Σ ln(LRᵢ))
                  </span>
                </div>
                <p className="text-[11px] text-slate-600">
                  Prior base rate P(Claim) = {Math.round((math?.bayesian_analysis?.prior_probability || 0.25) * 100)}%. Evaluated {math?.independent_source_count} independent source clusters producing a cumulative Bayes Factor of {math?.bayesian_analysis?.bayes_factor || 1.0}.
                </p>
                <div className="pt-1 text-xs font-bold text-slate-900">
                  Posterior Probability: <span className="text-indigo-600">{Math.round((math?.bayesian_analysis?.posterior_probability || 0) * 100)}%</span>
                </div>
              </div>
            </div>

            {/* Confidence Explanation */}
            <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 text-xs text-blue-900 space-y-1">
              <span className="font-bold flex items-center gap-1.5 text-blue-950">
                <Info size={14} />
                Multi-Factor Confidence Indicator ({Math.round((confidence_score || 0) * 100)}%):
              </span>
              <p className="text-[11px] text-blue-800 leading-relaxed">
                {math?.confidence_explanation}
              </p>
              <p className="text-[10px] text-blue-700 pt-1 italic">
                *Note: Confidence measures evidence volume, diversity, and consistency. It is clearly distinguished from the truth probability of the claim itself.
              </p>
            </div>

            {/* Source Weights Breakdown Table */}
            {math?.reliability_weights_breakdown && math.reliability_weights_breakdown.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-700">Detailed Source Math Breakdown:</span>
                <div className="overflow-x-auto border border-slate-200 rounded-xl">
                  <table className="w-full text-left border-collapse text-[11px]">
                    <thead>
                      <tr className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                        <th className="py-2 px-3">Publisher</th>
                        <th className="py-2 px-3">Category</th>
                        <th className="py-2 px-3 text-center">Nominal (wᵢ)</th>
                        <th className="py-2 px-3 text-center">Effective Weight</th>
                        <th className="py-2 px-3 text-center">Stance (sᵢ)</th>
                        <th className="py-2 px-3 text-right">Contribution (wᵢ × sᵢ)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {math.reliability_weights_breakdown.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-50/60">
                          <td className="py-2 px-3 font-medium text-slate-800 truncate max-w-[140px]">{row.publisher}</td>
                          <td className="py-2 px-3 text-slate-500 truncate max-w-[120px]">{row.category}</td>
                          <td className="py-2 px-3 text-center text-slate-700">{row.nominal_weight}</td>
                          <td className="py-2 px-3 text-center font-mono text-slate-800">{row.effective_weight}</td>
                          <td className="py-2 px-3 text-center">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              row.stance === 'SUPPORTING' ? 'bg-emerald-100 text-emerald-800' :
                              row.stance === 'CONTRADICTING' ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-700'
                            }`}>
                              {row.stance} ({row.stance_value > 0 ? `+${row.stance_value}` : row.stance_value})
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right font-mono font-bold text-slate-900">
                            {row.contribution > 0 ? `+${row.contribution}` : row.contribution}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* SECTION 8: AI INVESTIGATION SUMMARY */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Award size={18} className="text-blue-600" />
          Structured AI Intelligence Briefing
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-800 text-[11px] flex items-center justify-center font-bold">1</span>
              What reportedly happened?
            </span>
            <p className="text-xs text-slate-700 leading-relaxed pl-6.5">
              {ai?.what_reportedly_happened || 'Incident allegation recorded.'}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] flex items-center justify-center font-bold">2</span>
              What evidence supports the claim?
            </span>
            <p className="text-xs text-slate-700 leading-relaxed pl-6.5">
              {ai?.supporting_evidence_summary || 'No direct corroboration found.'}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-rose-100 text-rose-800 text-[11px] flex items-center justify-center font-bold">3</span>
              What evidence contradicts it?
            </span>
            <p className="text-xs text-slate-700 leading-relaxed pl-6.5">
              {ai?.contradicting_evidence_summary || 'No explicit public denials logged.'}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-800 text-[11px] flex items-center justify-center font-bold">4</span>
              What do official sources say?
            </span>
            <p className="text-xs text-slate-700 leading-relaxed pl-6.5">
              {ai?.official_sources_position || 'Checking official advisories.'}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 text-[11px] flex items-center justify-center font-bold">5</span>
              What remains uncertain?
            </span>
            <p className="text-xs text-slate-700 leading-relaxed pl-6.5">
              {ai?.uncertainties_and_gaps || 'Verification factors noted.'}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-1.5">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-800 text-[11px] flex items-center justify-center font-bold">6</span>
              Final Assessment
            </span>
            <p className="text-xs text-slate-700 leading-relaxed pl-6.5 font-medium">
              {ai?.final_assessment || 'Assessment completed.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
