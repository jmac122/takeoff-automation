import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";
import App from "./App.tsx";

const queryClient = new QueryClient();

// #region agent log
fetch('http://127.0.0.1:7244/ingest/c2908297-06df-40fb-a71a-4f158024ffa0',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run1',hypothesisId:'H3',location:'main.tsx:10',message:'app render bootstrap',data:{rootExists:!!document.getElementById("root")},timestamp:Date.now()})}).catch(()=>{});
// #endregion

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
