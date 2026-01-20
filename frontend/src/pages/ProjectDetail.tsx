/**
 * ProjectDetail page - displays project information and documents.
 */

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Upload, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Breadcrumbs } from '@/components/layout/Breadcrumbs';
import { DocumentCard } from '@/components/document/DocumentCard';
import { EmptyState } from '@/components/common/EmptyState';
import { projectsApi } from '@/api/projects';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { DocumentUploader } from '@/components/document/DocumentUploader';

export default function ProjectDetail() {
    const { projectId } = useParams<{ projectId: string }>();
    const [showUploadModal, setShowUploadModal] = useState(false);

    // Fetch project details
    const { data: project, isLoading: projectLoading } = useQuery({
        queryKey: ['project', projectId],
        queryFn: async () => {
            if (!projectId) throw new Error('Project ID is required');
            return await projectsApi.get(projectId);
        },
        enabled: !!projectId,
    });

    // Fetch documents for project
    const { data: documentsData, isLoading: documentsLoading } = useQuery({
        queryKey: ['documents', projectId],
        queryFn: async () => {
            if (!projectId) throw new Error('Project ID is required');
            return await projectsApi.getDocuments(projectId);
        },
        enabled: !!projectId,
    });

    const documents = documentsData?.documents || [];

    if (projectLoading) {
        return (
            <div className="container mx-auto px-4 py-6">
                <p className="text-gray-600">Loading project...</p>
            </div>
        );
    }

    if (!project) {
        return (
            <div className="container mx-auto px-4 py-6">
                <p className="text-red-600">Project not found</p>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-6">
            {/* Breadcrumbs */}
            <Breadcrumbs
                items={[
                    { label: 'Projects', href: '/projects' },
                    { label: project.name, href: `/projects/${project.id}` },
                ]}
            />

            {/* Project Header */}
            <div className="flex items-start justify-between mb-6 mt-4">
                <div>
                    <h1 className="text-3xl font-bold mb-2">{project.name}</h1>
                    {project.client_name && (
                        <p className="text-lg text-gray-600">Client: {project.client_name}</p>
                    )}
                    {project.project_address && (
                        <p className="text-sm text-gray-500">{project.project_address}</p>
                    )}
                    {project.description && (
                        <p className="text-sm text-gray-600 mt-2">{project.description}</p>
                    )}
                </div>
                <div className="flex gap-2">
                    <Button onClick={() => setShowUploadModal(true)}>
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Documents
                    </Button>
                </div>
            </div>

            {/* Documents Section */}
            <Card>
                <CardHeader>
                    <CardTitle>Documents ({documents.length})</CardTitle>
                    <CardDescription>Plan sets and drawings for this project</CardDescription>
                </CardHeader>
                <CardContent>
                    {documentsLoading ? (
                        <div className="text-center py-12">
                            <p className="text-gray-600">Loading documents...</p>
                        </div>
                    ) : documents.length === 0 ? (
                        <EmptyState
                            icon={FileText}
                            title="No documents yet"
                            description="Upload your first plan set to get started"
                            action={
                                <Button onClick={() => setShowUploadModal(true)}>
                                    <Upload className="w-4 h-4 mr-2" />
                                    Upload Documents
                                </Button>
                            }
                        />
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                            {documents.map((doc) => (
                                <DocumentCard key={doc.id} document={doc} projectId={projectId!} />
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Upload Modal */}
            <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Upload Documents</DialogTitle>
                    </DialogHeader>
                    <DocumentUploader
                        projectId={projectId!}
                        onUploadComplete={() => {
                            setShowUploadModal(false);
                        }}
                    />
                </DialogContent>
            </Dialog>
        </div>
    );
}
