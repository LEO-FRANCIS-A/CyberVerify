import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, Sparkles, AlertCircle, CheckCircle2, Loader2, ArrowRight, 
  Terminal, ShieldCheck, Globe, Database, Cpu, Calculator, Award
} from 'lucide-react';
import { streamInvestigation } from '../services/api';

const PIPELINE_STEPS = [
  { id: 1, title: 'Extracting Claim Information', desc: 'Identify targets, incident types, allegation details & keywords', icon: Cpu },
  { id: 2, title: 'Searching the Internet', desc: 'Prioritize official vendor portals, CERT advisories & security press', icon: Globe },
  { id: 3, title: 'Collecting Relevant Articles', desc: 'SSRF-protected extraction of primary reporting & deduplication', icon: Database },
  { id: 4, title: 'Identifying Official Sources', desc: 'Evaluate official company disclosures & government advisories', icon: ShieldCheck },
  { id: 5, title: 'Analysing Evidence Stance', desc: 'Classify supporting, contradicting, and neutral passages', icon: Terminal },
  { id: 6, title: 'Performing Mathematical Calculations', desc: 'Weighted evidence scoring, syndication clustering & Bayesian updates', icon: Calculator },
  { id: 7, title: 'Generating Final Verdict', desc: 'Deterministic verdict evaluation and executive summary briefing', icon: Award },
];

export default function NewInvestigation({ initialClaim = '', onInvestigationComplete }) {
  const [claim, setClaim] = useState(initialClaim);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [statusLogs, setStatusLogs] = useState([]);
  const [error, setError] = useState(null);
  const [cancelStream, setCancelStream] = useState(null);
  const logsEndRef = useRef(null);
  const hasStartedRef = useRef(false);
  const isInvestigatingRef = useRef(false);

  // Auto-start if initialClaim provided (guarded against double execution)
  useEffect(() => {
    if (initialClaim && !hasStartedRef.current && !isInvestigatingRef.current) {
      hasStartedRef.current = true;
      setClaim(initialClaim);
      startPipeline(initialClaim);
    }
  }, [initialClaim]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [statusLogs]);

  const startPipeline = (claimToInvestigate) => {
    if (isInvestigatingRef.current) return;
    const text = claimToInvestigate || claim;
    if (!text.trim() || text.length < 5) {
      setError('Please provide a specific cybersecurity claim of at least 5 characters.');
      return;
    }

    isInvestigatingRef.current = true;
    setError(null);
    setIsInvestigating(true);
    setCurrentStep(1);
    setStatusLogs([{
      timestamp: new Date().toLocaleTimeString(),
      step: 1,
      message: 'Investigation engine initialized. Connecting to verification pipeline...',
    }]);

    const stop = streamInvestigation(
      text,
      (progressEvent) => {
        setCurrentStep(progressEvent.step);
        setStatusLogs((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString(),
            step: progressEvent.step,
            message: progressEvent.message,
            meta: progressEvent.meta,
          },
        ]);
      },
      (completeData) => {
        isInvestigatingRef.current = false;
        setIsInvestigating(false);
        setCurrentStep(7);
        setStatusLogs((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString(),
            step: 7,
            message: 'Investigation successfully completed! Opening intelligence report...',
          },
        ]);
        setTimeout(() => {
          onInvestigationComplete(completeData);
        }, 1200);
      },
      (errorMessage) => {
        isInvestigatingRef.current = false;
        setIsInvestigating(false);
        setError(errorMessage);
        setStatusLogs((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString(),
            step: currentStep,
            message: `Engine halted with error: ${errorMessage}`,
            isError: true,
          },
        ]);
      }
    );

    setCancelStream(() => stop);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    startPipeline();
  };

  const sampleInquiries = [
    {
      title: "OpenAI Breach Allegation",
      claim: "Did OpenAI suffer a data breach exposing user information?",
    },
    {
      title: "CrowdStrike Outage & Exploitation",
      claim: "Was CrowdStrike Falcon targeted by a nation-state zero-day exploit?",
    },
    {
      title: "Snowflake Customer Compromise",
      claim: "Did Snowflake suffer a central database hack exposing customer records?",
    },
    {
      title: "Hugging Face Space Tokens",
      claim: "Did Hugging Face suffer a security breach compromising user API tokens?",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Initiate New Investigation
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          Submit a cybersecurity incident, rumor, or news claim. The AI engine will collect multi-source intelligence, calculate Bayesian consensus, and produce an explainable verdict.
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="claim-input" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
              Cybersecurity Claim / Incident Rumor to Verify
            </label>
            <textarea
              id="claim-input"
              rows={3}
              disabled={isInvestigating}
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              placeholder="e.g. Did OpenAI suffer a major database breach leaking user ChatGPT chat logs and passwords?"
              className="w-full p-3.5 text-sm sm:text-base border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-slate-50 disabled:text-slate-500 outline-none transition-all resize-y"
            />
          </div>

          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle size={16} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
            <div className="text-xs text-slate-400">
              Pipeline automatically validates against vendor advisories and CVE databases.
            </div>

            <button
              type="submit"
              disabled={isInvestigating || !claim.trim()}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-semibold text-sm shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
            >
              {isInvestigating ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Investigating Live...</span>
                </>
              ) : (
                <>
                  <Send size={16} />
                  <span>Start Investigation</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Quick presets */}
        {!isInvestigating && (
          <div className="mt-6 pt-5 border-t border-slate-100">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2.5">
              Or pick an incident scenario:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {sampleInquiries.map((sample, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => {
                    setClaim(sample.claim);
                    startPipeline(sample.claim);
                  }}
                  className="p-2.5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 text-left transition-all group cursor-pointer"
                >
                  <div className="text-xs font-bold text-slate-800 group-hover:text-blue-600 flex items-center justify-between">
                    <span>{sample.title}</span>
                    <ArrowRight size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <div className="text-[11px] text-slate-500 truncate mt-0.5">
                    "{sample.claim}"
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Real-time Progress Display */}
      {isInvestigating || currentStep > 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Loader2 size={18} className={isInvestigating ? "animate-spin text-blue-600" : "hidden"} />
                Investigation Pipeline Execution
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Stage {currentStep} of 7 • Real-time backend processing
              </p>
            </div>
            {isInvestigating && (
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
                Processing
              </span>
            )}
          </div>

          {/* Stepper Progress Visualizer */}
          <div className="space-y-3">
            {PIPELINE_STEPS.map((step) => {
              const StepIcon = step.icon;
              const isPast = currentStep > step.id;
              const isCurrent = currentStep === step.id;
              const isPending = currentStep < step.id;

              return (
                <div
                  key={step.id}
                  className={`flex items-start gap-3.5 p-3 rounded-xl border transition-all ${
                    isCurrent
                      ? 'bg-blue-50/70 border-blue-200 shadow-xs ring-1 ring-blue-300'
                      : isPast
                      ? 'bg-emerald-50/40 border-emerald-200'
                      : 'bg-slate-50/50 border-slate-100 opacity-60'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {isPast ? (
                      <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center shadow-xs">
                        <CheckCircle2 size={16} />
                      </div>
                    ) : isCurrent ? (
                      <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center animate-pulse shadow-xs">
                        <Loader2 size={16} className="animate-spin" />
                      </div>
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center text-xs font-bold">
                        {step.id}
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold ${isCurrent ? 'text-blue-900' : isPast ? 'text-emerald-900' : 'text-slate-600'}`}>
                        {step.id}. {step.title}
                      </span>
                      {isCurrent && (
                        <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 animate-pulse">
                          Active
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {step.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Live Engine Console Output */}
          <div className="rounded-xl bg-slate-900 p-4 text-slate-200 font-mono text-xs shadow-inner">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-slate-400 text-[11px]">
              <div className="flex items-center gap-2">
                <Terminal size={14} className="text-emerald-400" />
                <span>Live Verification Engine Feed</span>
              </div>
              <span className="text-[10px]">STDOUT STREAM</span>
            </div>

            <div className="mt-3 max-h-48 overflow-y-auto space-y-1.5 scrollbar-thin">
              {statusLogs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2 text-[11px] leading-relaxed">
                  <span className="text-slate-500 shrink-0">[{log.timestamp}]</span>
                  <span className="text-blue-400 shrink-0">Step {log.step}:</span>
                  <span className={log.isError ? "text-rose-400" : "text-slate-200"}>
                    {log.message}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
