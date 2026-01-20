/**
 * DocumentCard component for displaying document information in a card format.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useNavigate } from 'react-router-dom';
import { FileText, Calendar } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface DocumentCardProps {
    document: {
        id: string;
        original_filename: string;
        page_count: number | null;
        status: string;
        created_at: string;
    };
    projectId: string;
}

export function DocumentCard({ document, projectId }: DocumentCardProps) {
    const navigate = useNavigate();

    const statusColors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-800',
        processing: 'bg-blue-100 text-blue-800',
        completed: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800',
    };

    return (
        <Card
            className="hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => navigate(`/projects/${projectId}/documents/${document.id}`)}
        >
            <CardHeader>
                <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base truncate flex-1">{document.original_filename}</CardTitle>
                    <Badge className={statusColors[document.status] || 'bg-gray-100 text-gray-800'}>
                        {document.status}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        <span>{document.page_count || 0} pages</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDistanceToNow(new Date(document.created_at), { addSuffix: true })}</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
