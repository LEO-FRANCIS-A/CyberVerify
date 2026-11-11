import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, Trash2, ExternalLink, RefreshCw, AlertTriangle, 
  Scale, FileText, Calendar, CheckSquare, Square, ArrowRight
} from 'lucide-react';
import VerdictBadge from '../components/VerdictBadge';
import { fetchInvestigations, deleteInvestigation } from '../services/api';

export default function InvestigationHistory({ onOpenReport, onCompare }) {
  const [investigations, setInvestigations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [verdictFilter, setVerdictFilter] = useState('ALL');
  
  // Selection for Comparison
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  
  // Delete Modal State
  const [deleteCandidate, setDeleteCandidate] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadList = async () => {
    try {
      setLoading(true);
      const data = await fetchInvestigations(search, verdictFilter);
      setInvestigations(data);
    } catch (err) {
      console.error('Failed to load investigations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadList();
  }, [verdictFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadList();
  };

  const toggleSelectForCompare = (id) => {
    if (selectedForCompare.includes(id)) {
      setSelectedForCompare(selectedForCompare.filter((item) => item !== id));
    } else {
      if (selectedForCompare.length >= 2) {
        // Replace second
        setSelectedForCompare([selectedForCompare[0], id]);
      } else {
        setSelectedForCompare([...selectedForCompare, id]);
      }
    }
  };

  const confirmDelete = async () => {
    if (!deleteCandidate) return;
    try {
      setDeleting(true);
      await deleteInvestigation(deleteCandidate.investigation_id);
      setInvestigations((prev) => prev.filter((i) => i.investigation_id !== deleteCandidate.investigation_id));
      setSelectedForCompare((prev) => prev.filter((id) => id !== deleteCandidate.investigation_id));
      setDeleteCandidate(null);
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Investigation History
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Browse, search, compare, and audit past cybersecurity claims and verification reports.
          </p>
        </div>

        {selectedForCompare.length === 2 && (
          <button
            onClick={() => onCompare(selectedForCompare[0], selectedForCompare[1])}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md transition-all active:scale-95 cursor-pointer animate-bounce"
          >
            <Scale size={16} />
            <span>Compare 2 Selected Reports</span>
          </button>
        )}
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by claim title, target organisation, or category..."
            className="w-full pl-10 pr-24 py-2 text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
          <button
            type="submit"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 shrink-0">
            <Filter size={14} />
            <span>Verdict:</span>
          </div>
          <select
            value={verdictFilter}
            onChange={(e) => setVerdictFilter(e.target.value)}
            className="text-xs font-semibold py-2 px-3 border border-slate-300 rounded-xl bg-white text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="ALL">All Verdicts</option>
            <option value="VERIFIED">Verified</option>
            <option value="LIKELY TRUE">Likely True</option>
            <option value="FALSE">False</option>
            <option value="MISLEADING">Misleading</option>
            <option value="UNVERIFIED">Unverified</option>
          </select>

          <button
            onClick={loadList}
            disabled={loading}
            className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh List"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Selection helper note */}
      <div className="flex items-center justify-between text-xs text-slate-500 px-1">
        <span>Showing {investigations.length} investigation record(s)</span>
        <span>
          Tip: Select any 2 items to run a <strong className="text-blue-700">Side-by-Side Comparison</strong>.
        </span>
      </div>

      {/* Table / List */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-16 text-center space-y-2">
            <RefreshCw size={28} className="animate-spin mx-auto text-blue-600" />
            <p className="text-xs text-slate-500">Loading history records...</p>
          </div>
        ) : investigations.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-xs font-semibold border-b border-slate-200">
                  <th className="py-3 px-4 w-10 text-center">Compare</th>
                  <th className="py-3 px-4">Claim / Incident Title</th>
                  <th className="py-3 px-4">Organisation</th>
                  <th className="py-3 px-4">Verdict</th>
                  <th className="py-3 px-4 text-center">Confidence</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {investigations.map((item) => {
                  const isSelected = selectedForCompare.includes(item.investigation_id);
                  return (
                    <tr
                      key={item.investigation_id}
                      className={`hover:bg-slate-50/70 transition-colors ${
                        isSelected ? 'bg-blue-50/50' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4 text-center">
                        <button
                          type="button"
                          onClick={() => toggleSelectForCompare(item.investigation_id)}
                          className="text-slate-400 hover:text-blue-600 cursor-pointer"
                        >
                          {isSelected ? (
                            <CheckSquare size={18} className="text-blue-600" />
                          ) : (
                            <Square size={18} />
                          )}
                        </button>
                      </td>

                      <td
                        onClick={() => onOpenReport(item.investigation_id)}
                        className="py-3.5 px-4 max-w-md cursor-pointer group"
                      >
                        <div className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                          {item.original_claim}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {item.incident_category} • {item.total_sources} sources collected
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-xs font-medium text-slate-700 whitespace-nowrap">
                        {item.organisation}
                      </td>

                      <td className="py-3.5 px-4">
                        <VerdictBadge verdict={item.verdict} size="sm" />
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <span className="font-bold text-xs text-slate-800 bg-slate-100 px-2 py-0.5 rounded-md">
                          {Math.round(item.confidence_score * 100)}%
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-xs text-slate-500 whitespace-nowrap">
                        {item.investigation_date.split(' ')[0] || 'Recent'}
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => onOpenReport(item.investigation_id)}
                            className="p-1.5 rounded-lg text-slate-600 hover:text-blue-600 hover:bg-slate-100 transition-colors"
                            title="Open Intelligence Report"
                          >
                            <ExternalLink size={15} />
                          </button>
                          <button
                            onClick={() => setDeleteCandidate(item)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                            title="Delete Investigation"
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-16 text-center text-slate-400 space-y-2">
            <FileText size={36} className="mx-auto text-slate-300" />
            <p className="font-medium text-slate-600">No matching investigation reports found.</p>
            <p className="text-xs text-slate-400">Try adjusting your search criteria or verdict filter.</p>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteCandidate && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center">
              <AlertTriangle size={20} />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-900">Delete Investigation Report?</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Are you sure you want to delete this investigation and all its associated source evidence? This action cannot be undone.
              </p>
              <div className="p-3 mt-2 rounded-xl bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-800 line-clamp-2">
                "{deleteCandidate.original_claim}"
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeleteCandidate(null)}
                disabled={deleting}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                disabled={deleting}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white shadow-xs transition-colors"
              >
                {deleting ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
