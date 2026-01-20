import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <header className="bg-card shadow border-b">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-foreground">
              ForgeX Takeoffs
            </h1>
          </div>
        </header>
        <main>
          <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
