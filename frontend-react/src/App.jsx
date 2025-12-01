import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import Dashboard from './pages/Dashboard';
import UploadPage from './pages/Upload';
import CandidatesPage from './pages/Candidates';
import CandidateDetailPage from './pages/CandidateDetailPage';
import ComparisonPage from './pages/Comparison';
import HistoryPage from './pages/History';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/candidates" element={<CandidatesPage />} />
        <Route path="/candidates/view" element={<CandidateDetailPage />} />
        <Route path="/compare" element={<ComparisonPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
