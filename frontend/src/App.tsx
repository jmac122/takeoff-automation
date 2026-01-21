import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { NotificationProvider } from "./contexts/NotificationContext";
import { Header } from "./components/layout/Header";
import Projects from "./pages/Projects";
import ProjectDetail from "./pages/ProjectDetail";
import DocumentDetail from "./pages/DocumentDetail";
import { TakeoffViewer } from "./pages/TakeoffViewer";
import Testing from "./pages/Testing";
import AIEvaluation from "./pages/AIEvaluation";
import "./App.css";

function App() {
  return (
    <NotificationProvider>
      <Router>
        <div className="min-h-screen bg-neutral-950">
          <Header />
          <main>
            <Routes>
              {/* Redirect root to projects */}
              <Route path="/" element={<Navigate to="/projects" replace />} />

              {/* Projects */}
              <Route path="/projects" element={<Projects />} />
              <Route path="/projects/:projectId" element={<ProjectDetail />} />

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
      </Router>
    </NotificationProvider>
  );
}

export default App;
