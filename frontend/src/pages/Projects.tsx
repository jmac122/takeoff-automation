/**
 * Projects list page - displays all projects in a grid with search and create functionality.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ProjectCard } from '@/components/project/ProjectCard';
import { EmptyState } from '@/components/common/EmptyState';
import { CreateProjectModal } from '@/components/project/CreateProjectModal';
import { projectsApi } from '@/api/projects';
import { Project } from '@/types';

export default function Projects() {
    const [searchTerm, setSearchTerm] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);

    // Fetch all projects
    const { data, isLoading, error } = useQuery({
        queryKey: ['projects'],
        queryFn: async () => {
            try {
                const response = await projectsApi.list();
                console.log('API Response:', response);
                return response.projects;
            } catch (err) {
                console.error('Error fetching projects:', err);
                throw err;
            }
        },
    });

    const projects = data || [];

    // Filter projects by search term
    const filteredProjects = projects.filter((project: Project) => {
        const searchLower = searchTerm.toLowerCase();
        return (
            project.name.toLowerCase().includes(searchLower) ||
            project.client_name?.toLowerCase().includes(searchLower) ||
            false
        );
    });

    return (
        <div className="container mx-auto px-4 py-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-3xl font-bold">Projects</h1>
                    <p className="text-gray-600">Manage your construction takeoff projects</p>
                </div>
                <Button onClick={() => setShowCreateModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Project
                </Button>
            </div>

            {/* Error State */}
            {error && (
                <div className="text-center py-12">
                    <p className="text-red-600">Error loading projects: {(error as Error).message}</p>
                </div>
            )}

            {/* Search */}
            {projects.length > 0 && (
                <div className="mb-6">
                    <Input
                        placeholder="Search projects by name or client..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="max-w-md"
                    />
                </div>
            )}

            {/* Loading State */}
            {isLoading && (
                <div className="text-center py-12">
                    <p className="text-gray-600">Loading projects...</p>
                </div>
            )}

            {/* Empty State */}
            {!isLoading && projects.length === 0 && (
                <EmptyState
                    icon={FolderOpen}
                    title="No projects yet"
                    description="Create your first project to get started with takeoff management"
                    action={
                        <Button onClick={() => setShowCreateModal(true)}>
                            <Plus className="w-4 h-4 mr-2" />
                            Create Project
                        </Button>
                    }
                />
            )}

            {/* Projects Grid */}
            {!isLoading && filteredProjects.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {filteredProjects.map((project: Project) => (
                        <ProjectCard key={project.id} project={project} />
                    ))}
                </div>
            )}

            {/* No Results */}
            {!isLoading && projects.length > 0 && filteredProjects.length === 0 && (
                <div className="text-center py-12">
                    <p className="text-gray-600">No projects match your search</p>
                </div>
            )}

            {/* Create Project Modal */}
            <CreateProjectModal
                open={showCreateModal}
                onClose={() => setShowCreateModal(false)}
            />
        </div>
    );
}

