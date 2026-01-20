/**
 * CreateProjectModal component for creating new projects.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { projectsApi } from '@/api/projects';
import { CreateProjectRequest } from '@/types';

interface CreateProjectModalProps {
    open: boolean;
    onClose: () => void;
}

export function CreateProjectModal({ open, onClose }: CreateProjectModalProps) {
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const [formData, setFormData] = useState<CreateProjectRequest>({
        name: '',
        description: '',
        client_name: '',
        project_address: '',
    });

    const createMutation = useMutation({
        mutationFn: async (data: CreateProjectRequest) => {
            return await projectsApi.create(data);
        },
        onSuccess: (newProject) => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            onClose();
            // Reset form
            setFormData({
                name: '',
                description: '',
                client_name: '',
                project_address: '',
            });
            // Navigate to new project
            navigate(`/projects/${newProject.id}`);
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        createMutation.mutate(formData);
    };

    const handleClose = () => {
        if (!createMutation.isPending) {
            onClose();
            // Reset form on close
            setFormData({
                name: '',
                description: '',
                client_name: '',
                project_address: '',
            });
        }
    };

    return (
        <Dialog open={open} onOpenChange={handleClose}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>Create New Project</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <Label htmlFor="name">Project Name *</Label>
                        <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                            maxLength={200}
                            placeholder="Enter project name"
                        />
                    </div>

                    <div>
                        <Label htmlFor="client_name">Client Name</Label>
                        <Input
                            id="client_name"
                            value={formData.client_name}
                            onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                            maxLength={200}
                            placeholder="Enter client name"
                        />
                    </div>

                    <div>
                        <Label htmlFor="project_address">Project Address</Label>
                        <Input
                            id="project_address"
                            value={formData.project_address}
                            onChange={(e) => setFormData({ ...formData, project_address: e.target.value })}
                            maxLength={500}
                            placeholder="Enter project address"
                        />
                    </div>

                    <div>
                        <Label htmlFor="description">Description</Label>
                        <textarea
                            id="description"
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            rows={3}
                            maxLength={1000}
                            placeholder="Enter project description"
                            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        />
                    </div>

                    <div className="flex justify-end gap-2">
                        <Button type="button" variant="outline" onClick={handleClose} disabled={createMutation.isPending}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={createMutation.isPending}>
                            {createMutation.isPending ? 'Creating...' : 'Create Project'}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
