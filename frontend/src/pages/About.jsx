import React from 'react';
import { 
  ShieldCheck, Calculator, Network, Globe, AlertTriangle, 
  Layers, CheckCircle2, Award, BookOpen, Scale, Sparkles 
} from 'lucide-react';

export default function About() {
  return (
    <div className="max-w-4xl mx-auto space-y-10 pb-20">
      {/* Header */}
      <div className="border-b border-slate-200 pb-6 space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold">
          <BookOpen size={14} />
          <span>System Architecture & Verification Methodology</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          How CyberVerify Works
        </h1>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
          An automated, explainable intelligence platform designed to eliminate hallucinations, blind consensus bias, and sensationalist cybersecurity rumors.
        </p>
      </div>

      {/* 1. What CyberVerify Does */}
      <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <ShieldCheck size={20} className="text-blue-600" />
          1. What CyberVerify Does
        </h2>
        <p className="text-sm text-slate-700 leading-relaxed">
          CyberVerify is an autonomous threat intelligence and fact-checking engine built specifically for cybersecurity rumors, data breach allegations, and vulnerability reports. In an era where a single unverified social media leak can trigger PR panic, stock declines, and false alarm responses, CyberVerify separates verifiable technical evidence from hype.
        </p>
        <p className="text-sm text-slate-700 leading-relaxed">
          Unlike general-purpose conversational LLMs, CyberVerify never speculates, invents citations, or relies on subjective opinion. Every verdict is mathematically computed from real-time web intelligence, vendor security advisories, and government CSIRT bulletins.
        </p>
      </section>

      {/* 2. The 7-Step Investigation Pipeline */}
      <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-6">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Layers size={20} className="text-indigo-600" />
          2. The 7-Step Investigation Pipeline
        </h2>

        <div className="space-y-4">
          {[
            {
              num: 1,
              title: "Claim Decomposition & Entity Extraction",
              desc: "Extracts key technical entities: targeted vendor, incident category (breach, 0-day, extortion), allegation details, CVE IDs, and formulates high-precision search query vectors."
            },
            {
              num: 2,
              title: "Multi-Tiered Internet Search",
              desc: "Executes targeted searches across prioritized channels: official vendor portals, CERT/CISA advisories, established cybersecurity press (BleepingComputer, The Hacker News, Krebs), and general news."
            },
            {
              num: 3,
              title: "SSRF-Safe Article Scraping & Sanitization",
              desc: "Safely scrapes and sanitizes full article bodies while blocking SSRF attacks, cloud metadata endpoints, and stripping prompt injection vectors."
            },
            {
              num: 4,
              title: "Official Source Verification",
              desc: "Identifies whether target organizations or government cyber agencies have published primary advisories, incident acknowledgments, or public denials."
            },
            {
              num: 5,
              title: "Discourse & Stance Classification",
              desc: "Analyzes extracted paragraphs to classify stance: Supporting (+1), Contradicting (-1), Neutral (0), or Inconclusive (0), extracting verbatim quotes for full explainability."
            },
            {
              num: 6,
              title: "Mathematical Scoring & Bayesian Updating",
              desc: "Applies syndication deduplication, weighted evidence scoring, and Bayesian log-odds probability updating to derive a reliable mathematical consensus."
            },
            {
              num: 7,
              title: "Deterministic Verdict Generation & Executive Briefing",
              desc: "Issues one of 5 strict verdicts (VERIFIED, LIKELY TRUE, FALSE, MISLEADING, UNVERIFIED) alongside a structured 6-point intelligence briefing."
            }
          ].map((step) => (
            <div key={step.num} className="flex items-start gap-4 p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
              <span className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                {step.num}
              </span>
              <div>
                <h3 className="text-sm font-bold text-slate-900">{step.title}</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. Mathematical Techniques */}
      <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-5">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Calculator size={20} className="text-blue-600" />
          3. Mathematical Formulation
        </h2>

        <div className="space-y-4">
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">A. Weighted Evidence Score (E)</h3>
            <div className="font-mono text-xs font-bold text-blue-700 bg-white p-2.5 rounded-lg border border-slate-200 inline-block">
              E = Σ (wᵢ × sᵢ) / Σ wᵢ
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Where wᵢ is the source reliability weight and sᵢ ∈ &#123;-1, 0, +1&#125; is the evidence stance. The resulting score E is bounded between -1.0 (decisively contradicted) and +1.0 (authoritatively corroborated).
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">B. Bayesian Evidence Updating</h3>
            <div className="font-mono text-xs font-bold text-indigo-700 bg-white p-2.5 rounded-lg border border-slate-200 inline-block">
              logit(P(H|E)) = logit(P(H)) + Σ ln(LRₖ)
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              We initialize a realistic prior base rate P(Claim) for unverified internet chatter (~25%). As independent source clusters k are evaluated, the posterior probability is updated in log-odds space using the Bayes Factor likelihood ratio LRₖ of each independent cluster.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">C. Multi-Factor Confidence Index</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Confidence is explicitly separated from the truth probability of the claim. It synthesizes: (1) independent source cluster volume, (2) mean credibility weights, (3) primary vendor disclosure availability, and (4) stance consensus entropy.
            </p>
          </div>
        </div>
      </section>

      {/* 4. Why Source Reliability Matters */}
      <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Scale size={20} className="text-emerald-600" />
          4. Source Reliability & The Syndication Problem
        </h2>
        <p className="text-sm text-slate-700 leading-relaxed">
          Online news often suffers from syndication echo chambers: a single unverified blog post or tweet is republished by twenty secondary aggregation portals. Treating twenty syndicated reprints as twenty independent confirmations leads to false certainty.
        </p>
        <p className="text-sm text-slate-700 leading-relaxed">
          CyberVerify applies cluster fingerprinting to group syndications into a single cluster, decaying redundant weights. It also prioritizes sources according to calibrated baseline weights:
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs pt-1">
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
            <div className="font-bold text-slate-900">Official Company Portals</div>
            <div className="text-blue-600 font-bold font-mono">1.00 Weight</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
            <div className="font-bold text-slate-900">Government Advisories</div>
            <div className="text-blue-600 font-bold font-mono">0.95 Weight</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
            <div className="font-bold text-slate-900">Cybersecurity Press</div>
            <div className="text-blue-600 font-bold font-mono">0.85 Weight</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
            <div className="font-bold text-slate-900">Security Researchers</div>
            <div className="text-blue-600 font-bold font-mono">0.80 Weight</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
            <div className="font-bold text-slate-900">General News Outlets</div>
            <div className="text-blue-600 font-bold font-mono">0.65 Weight</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
            <div className="font-bold text-slate-900">Community Forums</div>
            <div className="text-blue-600 font-bold font-mono">0.35 Weight</div>
          </div>
        </div>
      </section>

      {/* 5. Limitations of Automated Verification */}
      <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs space-y-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <AlertTriangle size={20} className="text-amber-600" />
          5. Limitations of Automated Verification
        </h2>
        <ul className="list-disc pl-5 space-y-2 text-xs sm:text-sm text-slate-700 leading-relaxed">
          <li>
            <strong>Zero-Day & Developing Incidents:</strong> During the initial hours of an active cyber incident, official disclosures may not yet exist. In such cases, CyberVerify correctly issues an <em>UNVERIFIED</em> verdict rather than jumping to conclusions.
          </li>
          <li>
            <strong>Paywalled or Dark Web Sources:</strong> CyberVerify queries the open web and public advisory feeds; claims whose sole corroboration exists inside closed dark web forums require human intelligence validation.
          </li>
          <li>
            <strong>Heuristic Calibration:</strong> While Bayesian likelihood ratios reflect structured empirical principles, they represent mathematical models of public evidence, not absolute proof of non-public facts.
          </li>
        </ul>
      </section>
    </div>
  );
}
