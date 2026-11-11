import React, { useState, useEffect } from 'react';
import {
  Activity, ShieldAlert, AlertTriangle, CheckCircle2, RefreshCw, Search,
  Calendar, Building, Tag, ExternalLink, ChevronDown, ChevronUp, Layers,
  Clock, Shield, Radio, Sparkles, Filter, Cpu
} from 'lucide-react';
import { fetchEvents, triggerIngestion, triggerEventAudit, fetchEventAudits } from '../services/api';

const CLASSIFICATION_COLORS = {
  DISCLOSURE: 'bg-purple-50 text-purple-700 border-purple-200',
  ADVISORY: 'bg-blue-50 text-blue-700 border-blue-200',
  ANALYSIS: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  EXPLOITATION: 'bg-red-50 text-red-700 border-red-200 font-bold',
  PATCH: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  WARNING: 'bg-amber-50 text-amber-700 border-amber-200',
};

const TIMELINE_TYPE_ICONS = {
  EXPLOITATION: ShieldAlert,
  PATCH: CheckCircle2,
  ADVISORY: Radio,
  ANALYSIS: Cpu,
  WARNING: AlertTriangle,
  DISCLOSURE: Calendar,
};

export default function EventIntelligence() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Search & Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [cveFilter, setCveFilter] = useState('');
  
  // Action States
  const [ingesting, setIngesting] = useState(false);
  const [auditing, setAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [expandedEventId, setExpandedEventId] = useState(null);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await fetchEvents(search, statusFilter, cveFilter);
      setEvents(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadEvents();
  };

  const handleTriggerIngest = async () => {
    try {
      setIngesting(true);
      const res = await triggerIngestion();
      alert(`Ingestion completed! ${res.ingestion_summary.new_articles_ingested} new articles ingested from ${res.ingestion_summary.success_sources} sources.`);
      await loadEvents();
    } catch (err) {
      alert(`Ingestion error: ${err.message}`);
    } finally {
      setIngesting(false);
    }
  };

  const handleTriggerAudit = async () => {
    try {
      setAuditing(true);
      const res = await triggerEventAudit();
      setAuditResult(res);
    } catch (err) {
      alert(`HDBSCAN Audit error: ${err.message}`);
    } finally {
      setAuditing(false);
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Cybersecurity Event Intelligence</h1>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live Feed
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Continuous ingestion, entity extraction, BM25 semantic candidate retrieval, and logistic regression event clustering.
          </p>
        </div>

        {/* Global Pipeline Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleTriggerIngest}
            disabled={ingesting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold border border-blue-200 transition-all disabled:opacity-50"
          >
            <RefreshCw size={13} className={ingesting ? 'animate-spin' : ''} />
            <span>{ingesting ? 'Ingesting Feeds...' : 'Trigger Ingestion'}</span>
          </button>

          <button
            onClick={handleTriggerAudit}
            disabled={auditing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs font-semibold border border-purple-200 transition-all disabled:opacity-50"
          >
            <Sparkles size={13} className={auditing ? 'animate-spin' : ''} />
            <span>{auditing ? 'Auditing HDBSCAN...' : 'Run HDBSCAN Audit'}</span>
          </button>
        </div>
      </div>

      {/* HDBSCAN Audit Banner (if triggered) */}
      {auditResult && (
        <div className="p-4 rounded-xl bg-purple-50/70 border border-purple-200 text-xs text-purple-900 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-bold flex items-center gap-1.5">
              <Sparkles size={15} className="text-purple-600" />
              HDBSCAN Diagnostic Audit ({auditResult.audit_id})
            </span>
            <button
              onClick={() => setAuditResult(null)}
              className="text-purple-500 hover:text-purple-700 font-bold"
            >
              ✕ Dismiss
            </button>
          </div>
          <p>
            Evaluated <strong>{auditResult.total_events_audited}</strong> events and <strong>{auditResult.total_articles_audited}</strong> articles.
            Identified <strong>{auditResult.clusters_identified}</strong> dense semantic clusters and <strong>{auditResult.outliers_detected}</strong> outliers.
          </p>
          {auditResult.recommendations?.length > 0 && (
            <ul className="list-disc list-inside space-y-1 text-purple-800">
              {auditResult.recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Search & Filter Bar */}
      <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3 bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search events by keywords, organizations, or actors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">CVE:</span>
          <input
            type="text"
            placeholder="e.g. CVE-2021-44228"
            value={cveFilter}
            onChange={(e) => setCveFilter(e.target.value)}
            className="w-36 px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="MONITORING">MONITORING</option>
            <option value="RESOLVED">RESOLVED</option>
          </select>
        </div>

        <button
          type="submit"
          className="px-4 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-xs"
        >
          Apply Filters
        </button>
      </form>

      {/* Events List */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <RefreshCw size={32} className="animate-spin mx-auto text-blue-600" />
          <p className="text-xs text-slate-500 font-medium">Loading clustered cyber events...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      ) : events.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-2xl border border-slate-200 p-8 space-y-3">
          <ShieldAlert size={36} className="mx-auto text-slate-400" />
          <h3 className="text-sm font-bold text-slate-800">No Clustered Events Found</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            No events match the current filter criteria, or the continuous ingestion pipeline has not yet ingested articles.
          </p>
          <button
            onClick={handleTriggerIngest}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-all"
          >
            Trigger First Ingestion Cycle
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {events.map((ev) => {
            const isExpanded = expandedEventId === ev.event_id;
            const classColor = CLASSIFICATION_COLORS[ev.event_classification] || 'bg-slate-50 text-slate-700 border-slate-200';

            return (
              <div
                key={ev.event_id}
                className="bg-white rounded-xl border border-slate-200 hover:border-slate-300 shadow-xs transition-all overflow-hidden"
              >
                {/* Event Card Header */}
                <div className="p-4 sm:p-5 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-sm text-[11px] font-semibold border ${classColor}`}>
                        {ev.event_classification}
                      </span>
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-sm bg-slate-100 text-slate-700">
                        {ev.event_status}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        ID: {ev.event_id}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500">
                      <span className="flex items-center gap-1">
                        <Clock size={12} className="text-slate-400" />
                        Updated: {new Date(ev.latest_update).toLocaleDateString()}
                      </span>
                      <span className="font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-sm border border-blue-100">
                        {ev.sources_count || ev.article_ids?.length || 1} Source(s)
                      </span>
                    </div>
                  </div>

                  <div>
                    <h2 className="text-sm font-bold text-slate-900 hover:text-blue-600 transition-colors">
                      {ev.title}
                    </h2>
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                      {ev.description}
                    </p>
                  </div>

                  {/* Entities & Badges */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    {ev.cves?.map((cve) => (
                      <span
                        key={cve}
                        onClick={() => {
                          setCveFilter(cve);
                          loadEvents();
                        }}
                        className="px-2 py-0.5 rounded-sm text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 cursor-pointer hover:bg-amber-100"
                      >
                        {cve}
                      </span>
                    ))}

                    {ev.organizations?.map((org) => (
                      <span
                        key={org}
                        className="px-2 py-0.5 rounded-sm text-[10px] font-medium bg-slate-100 text-slate-700 flex items-center gap-1"
                      >
                        <Building size={10} className="text-slate-400" />
                        {org}
                      </span>
                    ))}

                    {ev.threat_actors?.map((actor) => (
                      <span
                        key={actor}
                        className="px-2 py-0.5 rounded-sm text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200"
                      >
                        Actor: {actor}
                      </span>
                    ))}
                  </div>

                  {/* Toggle Timeline Button */}
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                    <button
                      onClick={() => setExpandedEventId(isExpanded ? null : ev.event_id)}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      <span>{isExpanded ? 'Hide Event Timeline' : `View Chronological Timeline (${ev.timeline?.length || 1} updates)`}</span>
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </div>
                </div>

                {/* Collapsible Chronological Timeline */}
                {isExpanded && (
                  <div className="bg-slate-50/70 p-4 sm:p-5 border-t border-slate-200 space-y-4">
                    <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Clock size={13} className="text-blue-600" />
                      Event Evolution & Incident Timeline
                    </h3>

                    {ev.timeline && ev.timeline.length > 0 ? (
                      <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                        {ev.timeline.map((entry, idx) => {
                          const Icon = TIMELINE_TYPE_ICONS[entry.entry_type] || Calendar;
                          const tColor = CLASSIFICATION_COLORS[entry.entry_type] || 'bg-slate-100 text-slate-700';

                          return (
                            <div key={idx} className="relative space-y-1">
                              {/* Dot */}
                              <div className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-white border-2 border-blue-600 flex items-center justify-center">
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                              </div>

                              <div className="flex items-center gap-2">
                                <span className="text-[11px] font-bold text-slate-700 font-mono">
                                  {entry.date_str || new Date(entry.timestamp).toLocaleDateString()}
                                </span>
                                <span className={`px-1.5 py-0.5 rounded-xs text-[10px] font-bold border ${tColor}`}>
                                  {entry.entry_type}
                                </span>
                              </div>

                              <h4 className="text-xs font-semibold text-slate-900">
                                {entry.title}
                              </h4>
                              <p className="text-[11px] text-slate-600">
                                {entry.description}
                              </p>

                              {entry.source_url && (
                                <a
                                  href={entry.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:underline pt-0.5"
                                >
                                  <span>Source: {entry.source_title || 'Article'}</span>
                                  <ExternalLink size={10} />
                                </a>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500">Initial disclosure recorded.</p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
