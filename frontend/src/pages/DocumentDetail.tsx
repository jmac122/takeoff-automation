/**
 * DocumentDetail page - displays document information and pages.
 */

import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { PageCard } from '@/components/document/PageCard';
import { apiClient } from '@/api/client';
import { projectsApi } from '@/api/projects';
import { Document, Page } from '@/types';
import { formatDistanceToNow } from 'date-fns';

export default function DocumentDetail() {
    const { projectId, documentId } = useParams<{ projectId: string; documentId: string }>();

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
