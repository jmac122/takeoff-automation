import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";
import DocumentUploader from "../components/document/DocumentUploader";

interface HealthResponse {
  status: string;
}

interface PageData {
  id: string;
  document_id: string;
  page_number: number;
  width: number;
  height: number;
  classification: string | null;
  title: string | null;
  sheet_number: string | null;
  scale_text: string | null;
  scale_calibrated: boolean;
  status: string;
  thumbnail_url: string | null;
  concrete_relevance?: string | null;
}

interface PageClassification {
  page_id: string;
  classification: string | null;
  confidence: number | null;
  concrete_relevance: string | null;
  metadata: {
    discipline?: string;
    discipline_confidence?: number;
    page_type?: string;
    page_type_confidence?: number;
    concrete_elements?: string[];
    description?: string;
    llm_provider?: string;
    llm_model?: string;
    llm_latency_ms?: number;
  } | null;
}

export default function Dashboard() {
  const [uploadedDocumentId, setUploadedDocumentId] = useState<string | null>(null);
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);

  const { data: healthData, isLoading: healthLoading, error: healthError } = useQuery({
    queryKey: ["health"],
    queryFn: async (): Promise<HealthResponse> => {
      const response = await axios.get("/api/v1/health");
      return response.data;
    },
  });

  // Fetch pages for uploaded document
  const { data: pagesData, refetch: refetchPages } = useQuery({
    queryKey: ["document-pages", uploadedDocumentId],
    queryFn: async () => {
      if (!uploadedDocumentId) return null;
      const response = await axios.get(`/api/v1/documents/${uploadedDocumentId}/pages`);
      return response.data as { pages: PageData[]; total: number };
    },
    enabled: !!uploadedDocumentId,
    refetchInterval: uploadedDocumentId ? 3000 : false, // Poll while document is processing
  });

  // Fetch classification for selected page
  const { data: classificationData, refetch: refetchClassification } = useQuery({
    queryKey: ["page-classification", selectedPageId],
    queryFn: async () => {
      if (!selectedPageId) return null;
      const response = await axios.get(`/api/v1/pages/${selectedPageId}/classification`);
      return response.data as PageClassification;
    },
    enabled: !!selectedPageId,
  });

  // Classify document mutation
  const classifyDocumentMutation = useMutation({
    mutationFn: async (documentId: string) => {
      const response = await axios.post(`/api/v1/documents/${documentId}/classify`);
      return response.data;
    },
    onSuccess: () => {
      // Start polling for classification results
      setTimeout(() => refetchPages(), 2000);
    },
  });

  // Classify single page mutation
  const classifyPageMutation = useMutation({
    mutationFn: async (pageId: string) => {
      const response = await axios.post(`/api/v1/pages/${pageId}/classify`);
      return response.data;
    },
    onSuccess: () => {
      setTimeout(() => {
        refetchPages();
        refetchClassification();
      }, 3000);
    },
  });

  if (healthLoading) return <div>Loading...</div>;
  if (healthError) return <div>Error loading dashboard</div>;

  // For Phase 2A testing, use the actual project ID we created
  const demoProjectId = "fb5df285-615c-40e7-875c-4639c9ea0706";

  const getConcreteRelevanceColor = (relevance: string | null | undefined) => {
    switch (relevance) {
      case "high":
        return "bg-red-100 text-red-800 border-red-300";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "low":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "none":
        return "bg-gray-100 text-gray-600 border-gray-300";
      default:
        return "bg-gray-50 text-gray-500 border-gray-200";
    }
  };

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
              API Status: {healthData?.status || "Unknown"}
            </div>
          </div>

          <div className="border-t border-gray-200 pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Upload Plans (Phase 2A - Page Classification Test)
            </h3>
            <DocumentUploader
              projectId={demoProjectId}
              onUploadComplete={(documentId) => {
                console.log("Document uploaded:", documentId);
                setUploadedDocumentId(documentId);
              }}
            />
          </div>
        </div>
      </div>

      {/* Phase 2A Info Box */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-sm text-purple-800 mb-6">
        <p className="font-semibold mb-1">Phase 2A Testing Mode - Page Classification</p>
        <p>Using project: <code className="bg-purple-100 px-2 py-1 rounded">Test Project</code></p>
        <p className="mt-2 text-xs text-purple-600">
          Upload a PDF → View pages below → Click "Classify All Pages" to run AI classification!
        </p>
      </div>

      {/* Document Pages Section */}
      {uploadedDocumentId && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Document Pages ({pagesData?.total || 0})
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => refetchPages()}
                className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md"
              >
                Refresh
              </button>
              <button
                onClick={() => classifyDocumentMutation.mutate(uploadedDocumentId)}
                disabled={classifyDocumentMutation.isPending}
                className="px-4 py-1.5 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-md disabled:opacity-50"
              >
                {classifyDocumentMutation.isPending ? "Starting..." : "Classify All Pages"}
              </button>
            </div>
          </div>

          {classifyDocumentMutation.isSuccess && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-800">
              Classification started! Results will appear as pages are processed (refresh to see updates).
            </div>
          )}

          {/* Pages Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {pagesData?.pages.map((page) => (
              <div
                key={page.id}
                onClick={() => setSelectedPageId(page.id)}
                className={`border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md ${selectedPageId === page.id ? "ring-2 ring-purple-500 border-purple-300" : "border-gray-200"
                  }`}
              >
                {/* Thumbnail */}
                <div className="aspect-[8.5/11] bg-gray-100 rounded mb-2 overflow-hidden">
                  {page.thumbnail_url ? (
                    <img
                      src={page.thumbnail_url}
                      alt={`Page ${page.page_number}`}
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                  )}
                </div>

                {/* Page Info */}
                <div className="text-xs">
                  <p className="font-medium text-gray-900">
                    Page {page.page_number}
                    {page.sheet_number && <span className="text-gray-500 ml-1">({page.sheet_number})</span>}
                  </p>
                  {page.classification && (
                    <p className="text-purple-600 truncate">{page.classification}</p>
                  )}
                  {page.concrete_relevance && (
                    <span className={`inline-block mt-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${getConcreteRelevanceColor(page.concrete_relevance)}`}>
                      Concrete: {page.concrete_relevance}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {pagesData?.pages.length === 0 && (
            <p className="text-center text-gray-500 py-8">No pages found. Document may still be processing.</p>
          )}
        </div>
      )}

      {/* Selected Page Classification Details */}
      {selectedPageId && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Classification Details
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => refetchClassification()}
                className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md"
              >
                Refresh
              </button>
              <button
                onClick={() => classifyPageMutation.mutate(selectedPageId)}
                disabled={classifyPageMutation.isPending}
                className="px-4 py-1.5 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-md disabled:opacity-50"
              >
                {classifyPageMutation.isPending ? "Classifying..." : "Re-classify Page"}
              </button>
            </div>
          </div>

          {classificationData ? (
            <div className="space-y-4">
              {/* Main Classification */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Discipline</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {classificationData.metadata?.discipline || "—"}
                  </p>
                  {classificationData.metadata?.discipline_confidence && (
                    <p className="text-xs text-gray-500">
                      {(classificationData.metadata.discipline_confidence * 100).toFixed(0)}% confidence
                    </p>
                  )}
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Page Type</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {classificationData.metadata?.page_type || "—"}
                  </p>
                  {classificationData.metadata?.page_type_confidence && (
                    <p className="text-xs text-gray-500">
                      {(classificationData.metadata.page_type_confidence * 100).toFixed(0)}% confidence
                    </p>
                  )}
                </div>
                <div className={`rounded-lg p-3 ${getConcreteRelevanceColor(classificationData.concrete_relevance)}`}>
                  <p className="text-xs uppercase tracking-wide opacity-75">Concrete Relevance</p>
                  <p className="text-lg font-semibold">
                    {classificationData.concrete_relevance || "—"}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Overall Confidence</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {classificationData.confidence ? `${(classificationData.confidence * 100).toFixed(0)}%` : "—"}
                  </p>
                </div>
              </div>

              {/* Description */}
              {classificationData.metadata?.description && (
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-blue-600 uppercase tracking-wide mb-1">AI Description</p>
                  <p className="text-sm text-blue-900">{classificationData.metadata.description}</p>
                </div>
              )}

              {/* Concrete Elements */}
              {classificationData.metadata?.concrete_elements && classificationData.metadata.concrete_elements.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Detected Concrete Elements</p>
                  <div className="flex flex-wrap gap-2">
                    {classificationData.metadata.concrete_elements.map((element, idx) => (
                      <span key={idx} className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-sm">
                        {element}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* LLM Metadata */}
              {classificationData.metadata?.llm_provider && (
                <div className="border-t pt-4 mt-4">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">LLM Details</p>
                  <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                    <span>Provider: <strong>{classificationData.metadata.llm_provider}</strong></span>
                    <span>Model: <strong>{classificationData.metadata.llm_model}</strong></span>
                    {classificationData.metadata.llm_latency_ms && (
                      <span>Latency: <strong>{classificationData.metadata.llm_latency_ms.toFixed(0)}ms</strong></span>
                    )}
                  </div>
                </div>
              )}

              {/* No classification yet */}
              {!classificationData.classification && !classificationData.metadata && (
                <div className="text-center py-8 text-gray-500">
                  <p>No classification data yet.</p>
                  <p className="text-sm">Click "Re-classify Page" to run AI classification.</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>Loading classification data...</p>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      {!uploadedDocumentId && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
          <h4 className="text-lg font-medium text-gray-900 mb-2">How to Test Phase 2A</h4>
          <ol className="text-left text-sm text-gray-600 space-y-2 max-w-md mx-auto">
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-xs font-bold">1</span>
              <span>Upload a PDF construction plan document above</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <span>Wait for document processing to complete (pages will appear)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-xs font-bold">3</span>
              <span>Click "Classify All Pages" to run AI classification</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="flex-shrink-0 w-6 h-6 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-xs font-bold">4</span>
              <span>Click on any page to see detailed classification results</span>
            </li>
          </ol>
        </div>
      )}
    </div>
  );
}
