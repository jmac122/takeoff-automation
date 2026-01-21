/**
 * DocumentDetail page - displays document information and pages.
 */

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { PageCard } from '@/components/document/PageCard';
import { apiClient } from '@/api/client';
import { projectsApi } from '@/api/projects';
import { Document, Page } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import axios from 'axios';

export default function DocumentDetail() {
    const { projectId, documentId } = useParams<{ projectId: string; documentId: string }>();
    const queryClient = useQueryClient();
    const [classificationProvider, setClassificationProvider] = useState<string | undefined>(undefined);

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
        refetchInterval: document?.status === 'processing' ? 3000 : false,
    });

    // Classify document mutation
    const classifyMutation = useMutation({
        mutationFn: async () => {
            if (!documentId) throw new Error('Document ID required');
            const response = await axios.post(
                `/api/v1/documents/${documentId}/classify`,
                { provider: classificationProvider }
            );
            return response.data;
        },
        onSuccess: () => {
            // Refetch pages after classification starts
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['pages', documentId] });
            }, 2000);
        },
    });

    const pages = pagesData?.pages || [];

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
                <div className="flex flex-col gap-3 min-w-[250px]">
                    <div className="space-y-2">
                        <Label className="text-xs font-mono text-neutral-500 uppercase tracking-wider">
                            LLM Provider
                        </Label>
                        <Select
                            value={classificationProvider}
                            onValueChange={setClassificationProvider}
                        >
                            <SelectTrigger className="bg-neutral-900 border-neutral-700 text-white">
                                <SelectValue placeholder="Auto (default)" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="auto">Auto (default)</SelectItem>
                                <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                                <SelectItem value="openai">OpenAI (GPT-4)</SelectItem>
                                <SelectItem value="google">Google (Gemini)</SelectItem>
                                <SelectItem value="xai">xAI (Grok)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <Button
                        onClick={() => classifyMutation.mutate()}
                        disabled={classifyMutation.isPending}
                        className="bg-amber-500 hover:bg-amber-400 text-black font-mono uppercase tracking-wider"
                    >
                        {classifyMutation.isPending ? 'Starting...' : 'Classify All Pages'}
                    </Button>

                    {classifyMutation.isSuccess && (
                        <Alert className="bg-green-500/10 border-green-500/50">
                            <AlertDescription className="text-green-400 text-xs font-mono">
                                Classification started! Results will appear shortly.
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
                                />
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
