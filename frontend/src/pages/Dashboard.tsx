import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import DocumentUploader from "../components/document/DocumentUploader";

interface HealthResponse {
  status: string;
}

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["health"],
    queryFn: async (): Promise<HealthResponse> => {
      const response = await axios.get("/api/v1/health");
      return response.data;
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading dashboard</div>;

  // For Phase 1A testing, we'll use a demo project ID
  // In a real app, you'd select/create a project first
  const demoProjectId = "test-project-123";

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              ForgeX Takeoffs
            </h2>
            <p className="text-gray-600 mb-4">
              Upload construction plans and let AI generate accurate takeoffs
            </p>
            <div className="inline-flex items-center bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              API Status: {data?.status || "Unknown"}
            </div>
          </div>

          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Upload Plans (Phase 1A Test)
            </h3>
            <DocumentUploader
              projectId={demoProjectId}
              onUploadComplete={(documentId) => {
                console.log("Document uploaded:", documentId);
              }}
            />
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
        <p className="font-semibold mb-1">Phase 1A Testing Mode</p>
        <p>Using demo project ID: <code className="bg-blue-100 px-2 py-1 rounded">{demoProjectId}</code></p>
        <p className="mt-2 text-xs text-blue-600">
          Note: This will work once we create the project via API. For now, you can test the UI!
        </p>
      </div>
    </div>
  );
}
