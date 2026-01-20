/**
 * PageCard component for displaying page information with thumbnail and actions.
 */

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { Pencil } from 'lucide-react';

interface PageCardProps {
    page: {
        id: string;
        page_number: number;
        classification?: string | null;
        scale_calibrated: boolean;
        thumbnail_url?: string | null;
    };
    documentId: string;
    projectId: string;
}

export function PageCard({ page, documentId }: PageCardProps) {
    const navigate = useNavigate();

    return (
        <div className="border rounded-lg p-3 hover:shadow-md transition-shadow">
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
                        No preview
                    </div>
                )}
            </div>

            {/* Page Info */}
            <div className="space-y-2">
                <div>
                    <p className="font-medium text-sm">Page {page.page_number}</p>
                    {page.classification && (
                        <p className="text-xs text-gray-600 truncate">{page.classification}</p>
                    )}
                    {page.scale_calibrated && (
                        <Badge variant="secondary" className="mt-1 text-xs">Calibrated</Badge>
                    )}
                </div>

                {/* Open Takeoff Button */}
                <Button
                    size="sm"
                    variant="outline"
                    className="w-full text-xs"
                    onClick={() => navigate(`/documents/${documentId}/pages/${page.id}`)}
                >
                    <Pencil className="w-3 h-3 mr-1" />
                    Open Takeoff
                </Button>
            </div>
        </div>
    );
}
