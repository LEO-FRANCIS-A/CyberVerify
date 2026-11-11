import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, ShieldX, HelpCircle, FileSearch, ArrowRight, 
  Search, TrendingUp, BarChart3, PieChart as PieIcon, RefreshCw, 
  Sparkles, CheckCircle2, AlertTriangle, ExternalLink
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, CartesianGrid, Legend
} from 'recharts';
import { fetchDashboardStats, fetchInvestigations } from '../services/api';
import VerdictBadge from '../components/VerdictBadge';

export default function Dashboard({ onInvestigate, onOpenReport }) {
  const [stats, setStats] = useState(null);
  const [recentList, setRecentList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, recents] = await Promise.all([
        fetchDashboardStats(),
        fetchInvestigations('', '', 8),
      ]);
      setStats(statsData);
      setRecentList(recents);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onInvestigate(searchQuery.trim());
    }
  };

  const sampleClaims = [
    "Did OpenAI suffer a data breach exposing user information?",
    "Was CrowdStrike targeted by a nation-state zero-day exploit?",
    "Did Snowflake customers get breached due to credential stuffing?",
    "Was Microsoft Copilot source code leaked on GitHub?",
  ];

  // Chart data formatting
  const verdictColors = {
    'VERIFIED': '#16A34A',
    'LIKELY TRUE': '#2563EB',
    'FALSE': '#DC2626',
    'MISLEADING': '#D97706',
    'UNVERIFIED': '#64748B',
  };

  const pieData = stats?.verdict_distribution?.filter(v => v.count > 0) || [];
  
  const evidencePieData = stats?.evidence_distribution ? [
    { name: 'Supporting', value: stats.evidence_distribution.Supporting || 0, color: '#16A34A' },
    { name: 'Contradicting', value: stats.evidence_distribution.Contradicting || 0, color: '#DC2626' },
    { name: 'Neutral', value: stats.evidence_distribution.Neutral || 0, color: '#6366F1' },
    { name: 'Inconclusive', value: stats.evidence_distribution.Inconclusive || 0, color: '#94A3B8' },
  ].filter(d => d.value > 0) : [];

  return (
    <div className="space-y-8 pb-12">
      {/* Hero / Prominent Search Section */}
      <div className="bg-gradient-to-b from-white via-slate-50 to-slate-100/60 border border-slate-200/80 rounded-2xl p-6 md:p-10 shadow-xs relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-100/40 rounded-full blur-3xl -z-10 pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-indigo-100/30 rounded-full blur-2xl -z-10 pointer-events-none" />

        <div className="max-w-3xl mx-auto text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
            <Sparkles size={14} />
            <span>Multi-Source Intelligence Verification Engine</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-950">
            Verify Cybersecurity Incident Claims with Mathematical Rigor
          </h1>
          <p className="text-sm sm:text-base text-slate-600 max-w-2xl mx-auto">
            Analyze online rumors, security claims, and breach allegations against official advisories, vendor disclosures, and independent technical reporting.
          </p>

          {/* Prominent Search Box */}
          <form onSubmit={handleSearchSubmit} className="pt-4 relative max-w-2xl mx-auto">
            <div className="relative flex items-center shadow-lg rounded-xl overflow-hidden border border-slate-300 bg-white focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all">
              <Search size={20} className="absolute left-4 text-slate-400 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter a cybersecurity incident or news claim to investigate..."
                className="w-full pl-12 pr-36 py-4 text-sm sm:text-base text-slate-900 placeholder-slate-400 focus:outline-none"
              />
              <button
                type="submit"
                disabled={!searchQuery.trim()}
                className="absolute right-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-medium text-sm shadow-xs transition-all flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
              >
                <span>Investigate</span>
                <ArrowRight size={16} />
              </button>
            </div>

            {/* Example Queries */}
            <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500">
              <span className="font-semibold text-slate-600">Try investigating:</span>
              {sampleClaims.map((claim, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setSearchQuery(claim);
                    onInvestigate(claim);
                  }}
                  className="bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-md px-2.5 py-1 text-[11px] transition-colors cursor-pointer text-left truncate max-w-xs"
                >
                  "{claim.replace('Did ', '').replace('Was ', '')}"
                </button>
              ))}
            </div>
          </form>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Investigations</span>
            <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700">
              <FileSearch size={18} />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">{stats?.total_investigations ?? 0}</div>
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <span>Evaluated with mathematical consensus</span>
          </p>
        </div>

        {/* Card 2: Verified */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700">Verified Claims</span>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
              <ShieldCheck size={18} />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-700">{stats?.verified_claims ?? 0}</div>
          <p className="text-xs text-slate-500 mt-1">Official vendor or advisory confirmation</p>
        </div>

        {/* Card 3: False Claims */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-rose-700">False / Refuted</span>
            <div className="w-9 h-9 rounded-lg bg-rose-50 flex items-center justify-center text-rose-600">
              <ShieldX size={18} />
            </div>
          </div>
          <div className="text-2xl font-bold text-rose-700">{stats?.false_claims ?? 0}</div>
          <p className="text-xs text-slate-500 mt-1">Explicitly debunked or fabricated rumors</p>
        </div>

        {/* Card 4: Unverified Claims */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">Unverified Claims</span>
            <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
              <HelpCircle size={18} />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-700">{stats?.unverified_claims ?? 0}</div>
          <p className="text-xs text-slate-500 mt-1">Insufficient independent intelligence</p>
        </div>
      </div>

      {/* Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart 1: Verdict Distribution */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <BarChart3 size={16} className="text-blue-600" />
              Verdict Distribution
            </h3>
            <span className="text-xs text-slate-400">Classified Outcomes</span>
          </div>
          <div className="h-60 w-full">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={pieData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fontSize: 10, fill: '#64748B' }} 
                    angle={-20} 
                    textAnchor="end"
                  />
                  <YAxis tick={{ fontSize: 10, fill: '#64748B' }} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0F172A', borderRadius: '8px', color: '#FFF', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={verdictColors[entry.name] || '#3B82F6'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <BarChart3 size={32} className="mb-2 text-slate-300" />
                <span>No investigation metrics recorded yet.</span>
              </div>
            )}
          </div>
        </div>

        {/* Chart 2: Investigation Activity Timeline */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp size={16} className="text-blue-600" />
              Investigation Activity
            </h3>
            <span className="text-xs text-slate-400">Activity Over Time</span>
          </div>
          <div className="h-60 w-full">
            {stats?.recent_activity && stats.recent_activity.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.recent_activity} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                  <defs>
                    <linearGradient id="colorActivity" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563EB" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748B' }} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0F172A', borderRadius: '8px', color: '#FFF', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="investigations" stroke="#2563EB" strokeWidth={2} fillOpacity={1} fill="url(#colorActivity)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <TrendingUp size={32} className="mb-2 text-slate-300" />
                <span>No timeline activity logged yet.</span>
              </div>
            )}
          </div>
        </div>

        {/* Chart 3: Evidence Distribution */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <PieIcon size={16} className="text-indigo-600" />
              Evidence Distribution
            </h3>
            <span className="text-xs text-slate-400">Aggregated Stances</span>
          </div>
          <div className="h-60 w-full">
            {evidencePieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={evidencePieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {evidencePieData.map((entry, index) => (
                      <Cell key={`slice-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0F172A', borderRadius: '8px', color: '#FFF', fontSize: '12px' }}
                  />
                  <Legend 
                    verticalAlign="bottom" 
                    height={36} 
                    iconType="circle"
                    wrapperStyle={{ fontSize: '11px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <PieIcon size={32} className="mb-2 text-slate-300" />
                <span>No evidence distribution data.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Investigations Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Recent Investigations</h3>
            <p className="text-xs text-slate-500 mt-0.5">Latest verified cybersecurity incident inquiries</p>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>

        {recentList.length > 0 ? (
          <div className="divide-y divide-slate-100 overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/75 text-slate-500 text-xs font-semibold">
                  <th className="py-3 px-4">Claim Title / Allegation</th>
                  <th className="py-3 px-4">Organisation</th>
                  <th className="py-3 px-4">Verdict</th>
                  <th className="py-3 px-4 text-center">Confidence</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentList.map((item) => (
                  <tr 
                    key={item.investigation_id}
                    onClick={() => onOpenReport(item.investigation_id)}
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 max-w-md">
                      <div className="font-medium text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                        {item.original_claim}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {item.incident_category} • {item.total_sources} sources collected
                      </div>
                    </td>
                    <td className="py-3 px-4 text-xs font-medium text-slate-700">
                      {item.organisation}
                    </td>
                    <td className="py-3 px-4">
                      <VerdictBadge verdict={item.verdict} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="inline-flex items-center gap-1.5 font-semibold text-xs text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
                        <span>{Math.round(item.confidence_score * 100)}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500 whitespace-nowrap">
                      {item.investigation_date.split(' ')[0] || 'Recent'}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenReport(item.investigation_id);
                        }}
                        className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800"
                      >
                        <span>View Report</span>
                        <ArrowRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-400 text-sm">
            <FileSearch size={36} className="mx-auto mb-2 text-slate-300" />
            <p className="font-medium text-slate-600">No investigations completed yet.</p>
            <p className="text-xs text-slate-400 mt-1">Submit your first cybersecurity claim to begin verification.</p>
          </div>
        )}
      </div>
    </div>
  );
}
