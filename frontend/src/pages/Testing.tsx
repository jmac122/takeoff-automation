/**
 * Testing - Classification Testing Interface
 * 
 * Restored from Dashboard with industrial/tactical UI styling
 */

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { DocumentUploader } from "@/components/document/DocumentUploader";
import { HealthStatusBadge } from "@/components/dashboard/HealthStatusBadge";
import { PageInfoCard } from "@/components/dashboard/PageInfoCard";
import { LLMProviderSelector } from "@/components/LLMProviderSelector";
import { PageBrowser } from "@/components/document/PageBrowser";

// Types
interface HealthResponse {
    status: string;
}

interface PageData {
    id: string;
    document_id: string;
    page_number: number;
    sheet_number: string | null;
    classification: string | null;
    classification_confidence?: number | null;
    concrete_relevance?: string | null;
    thumbnail_url: string | null;
    image_url: string | null;
    status: string;
}

// Constants
const DEMO_PROJECT_ID = "fb5df285-615c-40e7-875c-4639c9ea0706";

export default function Testing() {
    const [uploadedDocumentId, setUploadedDocumentId] = useState<string | null>(null);
    const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
    const [classificationProvider, setClassificationProvider] = useState<string | undefined>(undefined);

    // API: Health check
    const { data: healthData, isLoading: healthLoading, error: healthError } = useQuery({
        queryKey: ["health"],
        queryFn: async (): Promise<HealthResponse> => {
            const response = await axios.get("/api/v1/health");
            return response.data;
        },
    });

    // API: Fetch pages for document
    const { data: pagesData, refetch: refetchPages } = useQuery({
        queryKey: ["document-pages", uploadedDocumentId],
        queryFn: async () => {
            if (!uploadedDocumentId) return null;
            const response = await axios.get(`/api/v1/documents/${uploadedDocumentId}/pages`);
            return response.data as { pages: PageData[]; total: number };
        },
        enabled: !!uploadedDocumentId,
        refetchInterval: uploadedDocumentId ? 3000 : false,
    });

    // API: Classify all pages
    const classifyDocumentMutation = useMutation({
        mutationFn: async (documentId: string) => {
            const response = await axios.post(`/api/v1/documents/${documentId}/classify`, {
                provider: classificationProvider,
            });
            return response.data;
        },
        onSuccess: () => {
            setTimeout(() => refetchPages(), 2000);
        },
    });

    // Loading state
    if (healthLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-neutral-950">
                <p className="text-neutral-400 font-mono">LOADING...</p>
            </div>
        );
    }

    // Error state
    if (healthError) {
        return (
            <div className="container mx-auto px-4 py-8 bg-neutral-950">
                <Alert variant="destructive" className="bg-red-900/20 border-red-500/50">
                    <AlertDescription className="text-red-400 font-mono">
                        ERROR LOADING DASHBOARD. PLEASE REFRESH THE PAGE.
                    </AlertDescription>
                </Alert>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-neutral-950">
            <div className="container mx-auto px-4 py-6 space-y-6">
                {/* Header Card */}
                <Card className="bg-neutral-900 border-neutral-700">
                    <CardHeader className="border-b border-neutral-700">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="text-neutral-600 font-mono text-xs">[TESTING]</span>
                            <div className="flex-1 h-px bg-neutral-800" />
                        </div>
                        <CardTitle className="text-2xl text-white uppercase tracking-tight"
                            style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
                            Classification Testing
                        </CardTitle>
                        <CardDescription className="text-neutral-400 font-mono text-sm">
                            Upload plans and test LLM classification accuracy
                        </CardDescription>
                        <div className="flex justify-center mt-4">
                            <HealthStatusBadge status={healthData?.status || "Unknown"} />
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4 pt-6">
                        <div>
                            <h3 className="text-lg font-medium mb-4 text-white uppercase tracking-wide font-mono">
                                Upload Plans
                            </h3>
                            <DocumentUploader
                                projectId={DEMO_PROJECT_ID}
                                onUploadComplete={(documentId) => {
                                    console.log("Document uploaded:", documentId);
                                    setUploadedDocumentId(documentId);
                                }}
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Phase 2A Info */}
                <Alert className="bg-amber-500/10 border-amber-500/50">
                    <AlertDescription className="text-amber-400 font-mono text-sm">
                        <p className="font-semibold uppercase tracking-wider">Phase 2A Testing Mode - Page Classification</p>
                        <p className="text-xs mt-1">
                            Using project: <code className="bg-neutral-800 px-2 py-1 rounded text-amber-500">Test Project</code>
                        </p>
                        <p className="text-xs mt-2 opacity-75">
                            Upload a PDF → Click "Classify All Pages" to test different LLMs!
                        </p>
                    </AlertDescription>
                </Alert>

                {/* LLM Provider Settings */}
                <Card className="bg-neutral-900 border-neutral-700">
                    <CardHeader className="border-b border-neutral-700">
                        <CardTitle className="text-white uppercase tracking-tight font-mono">
                            LLM Provider Settings
                        </CardTitle>
                        <CardDescription className="text-neutral-400 font-mono text-sm">
                            Select which AI provider to use for classification
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                        <LLMProviderSelector
                            value={classificationProvider}
                            onChange={setClassificationProvider}
                            label="Classification Provider"
                        />
                    </CardContent>
                </Card>

                {/* Document Pages */}
                {uploadedDocumentId && (
                    <Card className="bg-neutral-900 border-neutral-700">
                        <CardHeader className="border-b border-neutral-700">
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle className="text-white uppercase tracking-tight font-mono">
                                        Document Pages ({pagesData?.total || 0})
                                    </CardTitle>
                                    <CardDescription className="text-neutral-400 font-mono text-sm">
                                        Click a page to view classification details
                                    </CardDescription>
                                </div>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        onClick={() => refetchPages()}
                                        className="border-neutral-700 text-white hover:bg-neutral-800 font-mono uppercase tracking-wider text-xs"
                                    >
                                        Refresh
                                    </Button>
                                    <Button
                                        onClick={() => classifyDocumentMutation.mutate(uploadedDocumentId)}
                                        disabled={classifyDocumentMutation.isPending}
                                        className="bg-amber-500 hover:bg-amber-400 text-black font-mono uppercase tracking-wider text-xs"
                                    >
                                        {classifyDocumentMutation.isPending ? "Starting..." : "Classify All Pages"}
                                    </Button>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-6">
                            {classifyDocumentMutation.isSuccess && (
                                <Alert className="mb-4 bg-green-500/10 border-green-500/50">
                                    <AlertDescription className="text-green-400 font-mono text-sm">
                                        Classification started! Results will appear as pages are processed.
                                    </AlertDescription>
                                </Alert>
                            )}

                            {/* Pages Grid */}
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                                {pagesData?.pages.map((page) => (
                                    <PageInfoCard
                                        key={page.id}
                                        page={{ ...page, document_id: uploadedDocumentId }}
                                        projectId={DEMO_PROJECT_ID}
                                        isSelected={selectedPageId === page.id}
                                        onSelect={() => setSelectedPageId(page.id)}
                                    />
                                ))}
                            </div>

                            {pagesData?.pages.length === 0 && (
                                <p className="text-center text-neutral-500 font-mono py-8">
                                    No pages found. Document may still be processing.
                                </p>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Selected Page Details */}
                {selectedPageId && uploadedDocumentId && (
                    <Card className="bg-neutral-900 border-neutral-700">
                        <CardHeader className="border-b border-neutral-700">
                            <CardTitle className="text-white uppercase tracking-tight font-mono">
                                Classification Details
                            </CardTitle>
                            <CardDescription className="text-neutral-400 font-mono text-sm">
                                Detailed view for selected page
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <PageBrowser
                                documentId={uploadedDocumentId}
                                onPageSelect={(pageId) => setSelectedPageId(pageId)}
                            />
                        </CardContent>
                    </Card>
                )}

                {/* Instructions */}
                {!uploadedDocumentId && (
                    <Card className="bg-neutral-900 border-neutral-700">
                        <CardHeader className="border-b border-neutral-700">
                            <CardTitle className="text-white uppercase tracking-tight font-mono">
                                How to Test Phase 2A
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <ol className="space-y-2 text-sm font-mono">
                                <li className="flex items-start gap-2 text-neutral-300">
                                    <span className="flex-shrink-0 w-6 h-6 bg-amber-500/20 text-amber-500 rounded-full flex items-center justify-center text-xs font-bold border border-amber-500/50">
                                        1
                                    </span>
                                    <span>Upload a PDF construction plan document above</span>
                                </li>
                                <li className="flex items-start gap-2 text-neutral-300">
                                    <span className="flex-shrink-0 w-6 h-6 bg-amber-500/20 text-amber-500 rounded-full flex items-center justify-center text-xs font-bold border border-amber-500/50">
                                        2
                                    </span>
                                    <span>Wait for document processing to complete</span>
                                </li>
                                <li className="flex items-start gap-2 text-neutral-300">
                                    <span className="flex-shrink-0 w-6 h-6 bg-amber-500/20 text-amber-500 rounded-full flex items-center justify-center text-xs font-bold border border-amber-500/50">
                                        3
                                    </span>
                                    <span>Click "Classify All Pages" to run AI classification</span>
                                </li>
                                <li className="flex items-start gap-2 text-neutral-300">
                                    <span className="flex-shrink-0 w-6 h-6 bg-amber-500/20 text-amber-500 rounded-full flex items-center justify-center text-xs font-bold border border-amber-500/50">
                                        4
                                    </span>
                                    <span>Click on any page to see detailed classification results</span>
                                </li>
                            </ol>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
