import { useEffect, useState, useCallback } from 'react';
import AnimatedBackground from '@/components/primitives/AnimatedBackground';
import CustomCursor from '@/components/primitives/CustomCursor';
import Navbar from '@/components/Navbar';
import Hero from '@/components/Hero';
import ResearchOverview from '@/components/ResearchOverview';
import DatasetSection from '@/components/DatasetSection';
import SignalVisualizer from '@/components/SignalVisualizer';
import ProcessingPipeline from '@/components/ProcessingPipeline';
import ModelSection from '@/components/ModelSection';
import ModelComparison from '@/components/ModelComparison';
import ResultsDashboard from '@/components/ResultsDashboard';
import ArchitectureDiagram from '@/components/ArchitectureDiagram';
import TechnologyStack from '@/components/TechnologyStack';
import Timeline from '@/components/Timeline';
import About from '@/components/About';
import Contact from '@/components/Contact';
import Footer from '@/components/Footer';

export type ResultsContext = {
  dataset: 'deap' | 'custom' | null;
  modelTab: string | null;
};

function App() {
  const [resultsCtx, setResultsCtx] = useState<ResultsContext>({ dataset: null, modelTab: null });

  const openResults = useCallback((dataset: 'deap' | 'custom', modelTab: string) => {
    setResultsCtx({ dataset, modelTab });
    requestAnimationFrame(() => {
      const el = document.getElementById('results');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }, []);

  useEffect(() => {
    const onHash = () => {
      const h = window.location.hash.replace('#', '');
      if (h === 'deap-results') openResults('deap', 'svm');
      if (h === 'custom-results') openResults('custom', 'svm');
    };
    window.addEventListener('hashchange', onHash);
    onHash();
    return () => window.removeEventListener('hashchange', onHash);
  }, [openResults]);

  return (
    <>
      <AnimatedBackground />
      <CustomCursor />
      <Navbar />
      <main>
        <Hero />
        <ResearchOverview />
        <DatasetSection onDatasetClick={openResults} />
        <SignalVisualizer />
        <ProcessingPipeline />
        <ModelSection />
        <ModelComparison />
        <ResultsDashboard context={resultsCtx} onClose={() => setResultsCtx({ dataset: null, modelTab: null })} />
        <ArchitectureDiagram />
        <TechnologyStack />
        <Timeline />
        <About />
        <Contact />
      </main>
      <Footer />
    </>
  );
}

export default App;
