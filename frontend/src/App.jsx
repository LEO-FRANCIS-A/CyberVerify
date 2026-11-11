import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import EventIntelligence from './pages/EventIntelligence';
import NewInvestigation from './pages/NewInvestigation';
import InvestigationResults from './pages/InvestigationResults';
import InvestigationHistory from './pages/InvestigationHistory';
import InvestigationCompare from './pages/InvestigationCompare';
import About from './pages/About';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [currentClaim, setCurrentClaim] = useState('');
  const [activeInvestigationId, setActiveInvestigationId] = useState(null);
  const [activeInvestigationData, setActiveInvestigationData] = useState(null);
  const [compareIds, setCompareIds] = useState({ id1: null, id2: null });

  // Handle URL hash navigation for clean back/forward browser compatibility
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash.startsWith('results/')) {
        const id = hash.replace('results/', '');
        setActiveInvestigationId(id);
        setActivePage('results');
      } else if (['dashboard', 'events', 'new', 'history', 'about'].includes(hash)) {
        setActivePage(hash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigateTo = (page) => {
    setActivePage(page);
    window.location.hash = page;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStartInvestigation = (claimText) => {
    setCurrentClaim(claimText || '');
    navigateTo('new');
  };

  const handleInvestigationComplete = (completedData) => {
    setActiveInvestigationData(completedData);
    setActiveInvestigationId(completedData.investigation_id);
    setActivePage('results');
    window.location.hash = `results/${completedData.investigation_id}`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleOpenReport = (investigationId) => {
    setActiveInvestigationId(investigationId);
    setActiveInvestigationData(null); // Fetch fresh
    setActivePage('results');
    window.location.hash = `results/${investigationId}`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleTriggerCompare = (id1, id2) => {
    setCompareIds({ id1, id2 });
    setActivePage('compare');
    window.location.hash = 'compare';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/70 text-slate-900 selection:bg-blue-600 selection:text-white">
      <Navbar
        activePage={activePage}
        setActivePage={navigateTo}
        onStartNew={() => {
          setCurrentClaim('');
          navigateTo('new');
        }}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-8">
        {activePage === 'dashboard' && (
          <Dashboard
            onInvestigate={handleStartInvestigation}
            onOpenReport={handleOpenReport}
            onOpenEvents={() => navigateTo('events')}
          />
        )}

        {activePage === 'events' && (
          <EventIntelligence />
        )}

        {activePage === 'new' && (
          <NewInvestigation
            initialClaim={currentClaim}
            onInvestigationComplete={handleInvestigationComplete}
          />
        )}

        {activePage === 'results' && (
          <InvestigationResults
            investigationId={activeInvestigationId}
            initialData={activeInvestigationData}
            onBack={() => navigateTo('dashboard')}
            onCompareSelect={(id) => {
              navigateTo('history');
            }}
          />
        )}

        {activePage === 'history' && (
          <InvestigationHistory
            onOpenReport={handleOpenReport}
            onCompare={handleTriggerCompare}
          />
        )}

        {activePage === 'compare' && (
          <InvestigationCompare
            id1={compareIds.id1}
            id2={compareIds.id2}
            onBack={() => navigateTo('history')}
            onOpenReport={handleOpenReport}
          />
        )}

        {activePage === 'about' && <About />}
      </main>

      <Footer setActivePage={navigateTo} />
    </div>
  );
}
