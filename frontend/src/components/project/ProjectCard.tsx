/**
 * ProjectCard component for displaying project information in a card format.
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useNavigate } from 'react-router-dom';
import { FileText, Calendar } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface ProjectCardProps {
    project: {
        id: string;
        name: string;
        description?: string | null;
        client_name?: string | null;
        document_count?: number;
        created_at: string;
    };
}

export function ProjectCard({ project }: ProjectCardProps) {
    const navigate = useNavigate();

    return (
        <Card
            className="hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => navigate(`/projects/${project.id}`)}
        >
            <CardHeader>
                <CardTitle className="text-xl truncate">{project.name}</CardTitle>
                {project.client_name && (
                    <CardDescription className="truncate">{project.client_name}</CardDescription>
                )}
            </CardHeader>
            <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        <span>{project.document_count || 0} document{(project.document_count || 0) !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>Created {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}</span>
                    </div>
                </div>
                {project.description && (
                    <p className="text-sm text-gray-500 mt-3 line-clamp-2">{project.description}</p>
                )}
            </CardContent>
        </Card>
    );
}
