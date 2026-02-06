import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NotificationProvider } from "./contexts/NotificationContext";
import { Header } from "./components/layout/Header";
import Projects from "./pages/Projects";
import ProjectDetail from "./pages/ProjectDetail";
import DocumentDetail from "./pages/DocumentDetail";
import { TakeoffViewer } from "./pages/TakeoffViewer";
import { TakeoffWorkspace } from "./components/workspace/TakeoffWorkspace";
import Testing from "./pages/Testing";
import AIEvaluation from "./pages/AIEvaluation";
import "./App.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function AppContent() {
  const location = useLocation();

  // Hide main header on TakeoffViewer and TakeoffWorkspace (they have their own headers)
  const isTakeoffViewer = location.pathname.includes('/pages/');
  const isWorkspace = /^\/projects\/[^/]+\/workspace/.test(location.pathname);

  return (
    <div className="min-h-screen bg-neutral-950">
      {!isTakeoffViewer && !isWorkspace && <Header />}
      <main>
        <Routes>
          {/* Redirect root to projects */}
          <Route path="/" element={<Navigate to="/projects" replace />} />

          {/* Projects */}
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:projectId" element={<ProjectDetail />} />

          {/* New Workspace (feature-flagged) */}
          <Route path="/projects/:id/workspace" element={<TakeoffWorkspace />} />

          {/* Documents */}
          <Route path="/projects/:projectId/documents/:documentId" element={<DocumentDetail />} />

          {/* Takeoff Viewer */}
          <Route path="/documents/:documentId/pages/:pageId" element={<TakeoffViewer />} />

          {/* Testing */}
          <Route path="/testing" element={<Testing />} />

          {/* AI Evaluation */}
          <Route path="/ai-evaluation" element={<AIEvaluation />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NotificationProvider>
        <Router>
          <AppContent />
        </Router>
      </NotificationProvider>
    </QueryClientProvider>
  );
}

export default App;
