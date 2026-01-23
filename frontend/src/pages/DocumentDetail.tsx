/**
 * DocumentDetail page - displays document information and pages.
 */

import { useMemo, useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { PageCard } from '@/components/document/PageCard';
import { LLMProviderSelector } from '@/components/LLMProviderSelector';
import { apiClient } from '@/api/client';
import { projectsApi } from '@/api/projects';
import { Document, Page } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import axios from 'axios';

export default function DocumentDetail() {
    const { projectId, documentId } = useParams<{ projectId: string; documentId: string }>();
    const queryClient = useQueryClient();
    const [isClassifying, setIsClassifying] = useState(false);
    const [isSelectMode, setIsSelectMode] = useState(false);
    const [selectedPageIds, setSelectedPageIds] = useState<Set<string>>(new Set());
    const [selectedProvider, setSelectedProvider] = useState<string | undefined>(undefined);

    // Fetch project details for breadcrumb
    const { data: project } = useQuery({
        queryKey: ['project', projectId],
        queryFn: async () => {
            if (!projectId) throw new Error('Project ID is required');
            return await projectsApi.get(projectId);
        },
        enabled: !!projectId,
    });

    // Fetch document details
    const { data: document, isLoading: documentLoading } = useQuery({
        queryKey: ['document', documentId],
        queryFn: async () => {
            if (!documentId) throw new Error('Document ID is required');
            const response = await apiClient.get<Document>(`/documents/${documentId}`);
            return response.data;
        },
        enabled: !!documentId,
    });

    // Fetch pages for document
    const { data: pagesData, isLoading: pagesLoading } = useQuery({
        queryKey: ['pages', documentId],
        queryFn: async () => {
            if (!documentId) throw new Error('Document ID is required');
            const response = await apiClient.get<{ pages: Page[] }>(`/documents/${documentId}/pages`);
            return response.data;
        },
        enabled: !!documentId,
        // Poll while document is processing OR while classifications are running OR any page is processing
        refetchInterval: (query) => {
            // Use the latest query data
            const data = query.state.data as { pages: Page[] } | undefined;
            const hasProcessingPages = data?.pages?.some(page => {
                const status = page.status?.toLowerCase();
                return status === 'processing' || status === 'pending';
            }) ?? false;

            const shouldPoll = document?.status === 'processing' || isClassifying || hasProcessingPages;
            return shouldPoll ? 2000 : false;
        },
        // Refetch on window focus to catch updates
        refetchOnWindowFocus: true,
    });

    // Classify selected pages mutation
    const classifyMutation = useMutation({
        mutationFn: async ({ pageIds, provider }: { pageIds: string[]; provider?: string }) => {
            if (pageIds.length === 0) throw new Error('No pages selected');

            // If provider is selected, use vision models. Otherwise, use fast OCR-based classification
            const requestBody: { provider?: string; use_vision: boolean } = {
                use_vision: !!provider, // Use vision if provider is specified
            };
            if (provider) {
                requestBody.provider = provider;
            }

            // If all pages selected, use document endpoint
            if (pageIds.length === pages.length) {
                const response = await axios.post(
                    `/api/v1/documents/${documentId}/classify`,
                    requestBody
                );
                return response.data;
            }

            // Otherwise, classify individual pages
            const promises = pageIds.map(pageId =>
                axios.post(`/api/v1/pages/${pageId}/classify`, requestBody)
            );
            await Promise.all(promises);
            return { success: true };
        },
        onSuccess: () => {
            // Start polling for updates
            setIsClassifying(true);
            setIsSelectMode(false);
            setSelectedPageIds(new Set());

            // Immediately refetch to get updated status
            queryClient.refetchQueries({ queryKey: ['pages', documentId] });

            // Fallback: Stop polling after 60 seconds max
            setTimeout(() => {
                setIsClassifying(false);
                queryClient.invalidateQueries({ queryKey: ['pages', documentId] });
            }, 60000);
        },
    });

    const handleToggleSelectMode = () => {
        setIsSelectMode(!isSelectMode);
        setSelectedPageIds(new Set());
        setSelectedProvider(undefined); // Reset provider when exiting select mode
    };

    const handleTogglePage = (pageId: string) => {
        const newSelected = new Set(selectedPageIds);
        if (newSelected.has(pageId)) {
            newSelected.delete(pageId);
        } else {
            newSelected.add(pageId);
        }
        setSelectedPageIds(newSelected);
    };

    const handleSelectAll = () => {
        if (selectedPageIds.size === pages.length) {
            setSelectedPageIds(new Set());
        } else {
            setSelectedPageIds(new Set(pages.map(p => p.id)));
        }
    };

    const handleClassify = () => {
        if (selectedPageIds.size > 0) {
            classifyMutation.mutate({
                pageIds: Array.from(selectedPageIds),
                provider: selectedProvider,
            });
        }
    };

    // Re-run OCR for selected pages mutation
    const reprocessOCRMutation = useMutation({
        mutationFn: async (pageIds: string[]) => {
            if (pageIds.length === 0) throw new Error('No pages selected');

            // Reprocess OCR for each selected page
            const promises = pageIds.map(pageId =>
                axios.post(`/api/v1/pages/${pageId}/reprocess-ocr`)
            );
            await Promise.all(promises);
            return { success: true };
        },
        onSuccess: () => {
            // Start polling for updates
            setIsClassifying(true);
            setIsSelectMode(false);
            setSelectedPageIds(new Set());

            // Immediately refetch to get updated status
            queryClient.refetchQueries({ queryKey: ['pages', documentId] });

            // Fallback: Stop polling after 60 seconds max (OCR should complete by then)
            setTimeout(() => {
                setIsClassifying(false);
                queryClient.invalidateQueries({ queryKey: ['pages', documentId] });
            }, 60000);
        },
    });

    const handleReprocessOCR = () => {
        if (selectedPageIds.size > 0) {
            reprocessOCRMutation.mutate(Array.from(selectedPageIds));
        }
    };

    const pages = useMemo(() => pagesData?.pages || [], [pagesData?.pages]);

    // Check if any pages are still processing
    const hasProcessingPages = pages.some(page => {
        const status = page.status?.toLowerCase();
        return status === 'processing' || status === 'pending';
    });

    // Auto-clear isClassifying when all pages are done processing
    useEffect(() => {
        if (isClassifying && pages.length > 0) {

            // If no pages are processing anymore, clear the classifying state and reset mutations
            if (!hasProcessingPages) {
                console.log('All pages completed, clearing isClassifying state', {
                    pages: pages.map(p => ({ id: p.id, status: p.status }))
                });
                setIsClassifying(false);
                // Reset mutation states so alerts don't persist
                classifyMutation.reset();
                reprocessOCRMutation.reset();
                // Force refetch to get latest data
                queryClient.invalidateQueries({ queryKey: ['pages', documentId] });
                queryClient.refetchQueries({ queryKey: ['pages', documentId] });
            }
        }
    }, [
        pages,
        isClassifying,
        hasProcessingPages,
        documentId,
        queryClient,
        classifyMutation,
        reprocessOCRMutation,
    ]);

    const statusColors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-800',
        processing: 'bg-blue-100 text-blue-800',
        completed: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800',
    };

    if (documentLoading) {
        return (
            <div className="container mx-auto px-4 py-6">
                <p className="text-gray-600">Loading document...</p>
            </div>
        );
    }

    if (!document) {
        return (
            <div className="container mx-auto px-4 py-6">
                <p className="text-red-600">Document not found</p>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-6">
            {/* Breadcrumbs */}
            <Breadcrumbs
                items={[
                    { label: 'Projects', href: '/projects' },
                    { label: project?.name || 'Project', href: `/projects/${projectId}` },
                    { label: document.original_filename, href: `/projects/${projectId}/documents/${documentId}` },
                ]}
            />

            {/* Document Header */}
            <div className="flex items-start justify-between mb-6 mt-4">
                <div>
                    <h1 className="text-3xl font-bold mb-2">{document.original_filename}</h1>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span>{document.page_count || 0} pages</span>
                        <span>•</span>
                        <Badge className={statusColors[document.status] || 'bg-gray-100 text-gray-800'}>
                            {document.status}
                        </Badge>
                        <span>•</span>
                        <span>Uploaded {formatDistanceToNow(new Date(document.created_at), { addSuffix: true })}</span>
                    </div>
                </div>

                {/* Classification Controls */}
                <div className="flex flex-col gap-3 min-w-[320px]">
                    {/* Auto-classification indicator */}
                    <Alert className="bg-green-500/10 border-green-500/50">
                        <AlertDescription className="text-green-400 text-xs font-mono">
                            <span className="font-bold">✓ Auto-classified</span> from OCR data
                        </AlertDescription>
                    </Alert>

                    {/* Re-classification section */}
                    <div className="space-y-2">
                        <Label className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
                            Not happy with results?
                        </Label>
                        <div className="text-xs text-neutral-500 mb-2">
                            {isSelectMode
                                ? 'Select pages to re-classify or re-run OCR'
                                : 'Re-classify pages or re-run OCR for selected pages'
                            }
                        </div>
                    </div>

                    {!isSelectMode ? (
                        <Button
                            onClick={handleToggleSelectMode}
                            disabled={classifyMutation.isPending || isClassifying}
                            variant="outline"
                            className="border-amber-500/50 hover:bg-amber-500/10 text-amber-400 font-mono uppercase tracking-wider"
                        >
                            Re-Classify Pages
                        </Button>
                    ) : (
                        <div className="space-y-3">
                            <div className="flex gap-2">
                                <Button
                                    onClick={handleSelectAll}
                                    variant="outline"
                                    size="sm"
                                    className="flex-1 border-neutral-700 hover:bg-neutral-800 text-white font-mono uppercase tracking-wider text-xs"
                                >
                                    {selectedPageIds.size === pages.length ? 'Deselect All' : 'Select All'}
                                </Button>
                                <Button
                                    onClick={handleToggleSelectMode}
                                    variant="outline"
                                    size="sm"
                                    className="flex-1 border-neutral-700 hover:bg-neutral-800 text-neutral-400 font-mono uppercase tracking-wider text-xs"
                                >
                                    Cancel
                                </Button>
                            </div>

                            {/* Action Buttons */}
                            <div className="space-y-2 pt-2 border-t border-neutral-700">
                                {/* LLM Provider Selector - only show for classification */}
                                <div>
                                    <LLMProviderSelector
                                        value={selectedProvider}
                                        onChange={setSelectedProvider}
                                        label="AI Provider (Optional)"
                                        showDefault={true}
                                    />
                                </div>

                                {/* Re-classify Button */}
                                <Button
                                    onClick={handleClassify}
                                    disabled={selectedPageIds.size === 0 || classifyMutation.isPending || reprocessOCRMutation.isPending}
                                    className="w-full bg-amber-500 hover:bg-amber-400 text-black font-mono uppercase tracking-wider"
                                >
                                    {classifyMutation.isPending
                                        ? 'Classifying...'
                                        : `Re-Classify Selected (${selectedPageIds.size})`
                                    }
                                </Button>

                                {/* Re-run OCR Button */}
                                <Button
                                    onClick={handleReprocessOCR}
                                    disabled={selectedPageIds.size === 0 || reprocessOCRMutation.isPending || classifyMutation.isPending}
                                    variant="outline"
                                    className="w-full border-blue-500/50 hover:bg-blue-500/10 text-blue-400 font-mono uppercase tracking-wider"
                                >
                                    {reprocessOCRMutation.isPending
                                        ? 'Re-running OCR...'
                                        : `Re-Run OCR (${selectedPageIds.size})`
                                    }
                                </Button>
                            </div>
                        </div>
                    )}

                    {(reprocessOCRMutation.isPending || classifyMutation.isPending || hasProcessingPages) && (
                        <Alert className="bg-blue-500/10 border-blue-500/50">
                            <AlertDescription className="text-blue-400 text-xs font-mono">
                                {reprocessOCRMutation.isPending
                                    ? 'OCR re-processing in progress...'
                                    : classifyMutation.isPending
                                        ? 'Re-classification in progress...'
                                        : 'Processing in progress...'}
                            </AlertDescription>
                        </Alert>
                    )}
                </div>
            </div>

            {/* Pages Grid */}
            <Card>
                <CardHeader>
                    <CardTitle>Pages</CardTitle>
                    <CardDescription>Click "Open Takeoff" on a page to view and create measurements</CardDescription>
                </CardHeader>
                <CardContent>
                    {document.status === 'processing' ? (
                        <Alert>
                            <AlertDescription>
                                Document is being processed. Pages will appear shortly...
                            </AlertDescription>
                        </Alert>
                    ) : pagesLoading ? (
                        <div className="text-center py-12">
                            <p className="text-gray-600">Loading pages...</p>
                        </div>
                    ) : pages.length === 0 ? (
                        <div className="text-center py-12">
                            <p className="text-gray-600">No pages found</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                            {pages.map((page) => (
                                <PageCard
                                    key={page.id}
                                    page={page}
                                    documentId={documentId!}
                                    projectId={projectId!}
                                    isSelectMode={isSelectMode}
                                    isSelected={selectedPageIds.has(page.id)}
                                    onToggleSelect={handleTogglePage}
                                />
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
