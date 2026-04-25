import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import DemandAnalysis from './pages/DemandAnalysis';
import SimulationPanel from './pages/SimulationPanel';
import DecisionInsights from './pages/DecisionInsights';
import AIAssistant from './pages/AIAssistant';
import './App.css';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <Router>
      <div className="app-layout">
        <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
        <main className={`main-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/demand" element={<DemandAnalysis />} />
            <Route path="/simulation" element={<SimulationPanel />} />
            <Route path="/decisions" element={<DecisionInsights />} />
            <Route path="/ai-assistant" element={<AIAssistant />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
