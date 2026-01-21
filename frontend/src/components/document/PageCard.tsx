/**
 * PageCard component for displaying page information with thumbnail and actions.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FileText, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

interface PageCardProps {
    page: {
        id: string;
        page_number: number;
        sheet_number?: string | null;
        title?: string | null;
        classification?: string | null;
        classification_confidence?: number | null;
        concrete_relevance?: string | null;
        scale_calibrated: boolean;
        thumbnail_url?: string | null;
    };
    documentId: string;
    projectId: string;
}

export function PageCard({ page, documentId }: PageCardProps) {
    const queryClient = useQueryClient();
    const [showReclassify, setShowReclassify] = useState(false);

    // Re-classify single page mutation
    const reclassifyMutation = useMutation({
        mutationFn: async () => {
            const response = await axios.post(
                `/api/v1/pages/${page.id}/classify`,
                { use_vision: false }
            );
            return response.data;
        },
        onSuccess: () => {
            // Refetch pages after classification
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['pages', documentId] });
            }, 2000);
        },
    });
    return (
        <Card className="hover:shadow-lg transition-shadow bg-neutral-900 border-neutral-700">
            <CardContent className="p-3">
                {/* Thumbnail */}
                <div className="relative aspect-[8.5/11] bg-neutral-800 mb-2 rounded overflow-hidden">
                    {page.thumbnail_url ? (
                        <img
                            src={page.thumbnail_url}
                            alt={`Page ${page.page_number}`}
                            className="w-full h-full object-contain"
                        />
                    ) : (
                        <div className="flex items-center justify-center h-full">
                            <FileText className="h-12 w-12 text-neutral-600" />
                        </div>
                    )}

                    {/* Sheet Number & Classification Badge Overlay */}
                    <div className="absolute top-2 left-2 right-2">
                        <div className="bg-neutral-900/90 backdrop-blur-sm border border-neutral-700 px-2 py-1 rounded">
                            {/* Sheet Number (from OCR) */}
                            {page.sheet_number && (
                                <div className="text-sm font-bold text-white font-mono mb-1">
                                    {page.sheet_number}
                                </div>
                            )}

                            {/* Classification (Discipline:Type) */}
                            {page.classification && (
                                <div className="text-xs text-neutral-300 font-mono truncate">
                                    {page.classification}
                                </div>
                            )}

                            {/* Confidence Bar */}
                            {page.classification_confidence && (
                                <div className="flex items-center gap-1 mt-1">
                                    <div className="flex-1 h-1 bg-neutral-700 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full ${page.classification_confidence >= 0.8 ? 'bg-green-500' :
                                                page.classification_confidence >= 0.6 ? 'bg-amber-500' :
                                                    'bg-red-500'
                                                }`}
                                            style={{ width: `${page.classification_confidence * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-neutral-400 font-mono">
                                        {(page.classification_confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Concrete Relevance Badge */}
                    {page.concrete_relevance && (
                        <div className="absolute bottom-2 right-2">
                            <span className={`px-2 py-0.5 text-xs font-mono uppercase tracking-wider rounded ${page.concrete_relevance === 'high' ? 'bg-green-500/90 text-white' :
                                page.concrete_relevance === 'medium' ? 'bg-amber-500/90 text-black' :
                                    'bg-neutral-700/90 text-white'
                                }`}>
                                {page.concrete_relevance}
                            </span>
                        </div>
                    )}
                </div>

                {/* Page Info */}
                <div className="space-y-1 mb-3">
                    <div className="text-xs text-neutral-500 font-mono">
                        Page {page.page_number}
                    </div>
                </div>

                {/* Actions */}
                <div className="space-y-2">
                    {/* Open Takeoff Button */}
                    <Link to={`/documents/${documentId}/pages/${page.id}`}>
                        <Button
                            variant="outline"
                            size="sm"
                            className="w-full border-neutral-700 hover:bg-neutral-800 font-mono text-xs uppercase tracking-wider"
                        >
                            Open Takeoff
                        </Button>
                    </Link>

                    {/* Re-classify Button (on hover or when clicked) */}
                    <div
                        className="relative"
                        onMouseEnter={() => setShowReclassify(true)}
                        onMouseLeave={() => !reclassifyMutation.isPending && setShowReclassify(false)}
                    >
                        {(showReclassify || reclassifyMutation.isPending) && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => reclassifyMutation.mutate()}
                                disabled={reclassifyMutation.isPending}
                                className="w-full border border-amber-500/50 hover:bg-amber-500/10 text-amber-400 font-mono text-xs uppercase tracking-wider"
                            >
                                <RefreshCw className={`w-3 h-3 mr-1 ${reclassifyMutation.isPending ? 'animate-spin' : ''}`} />
                                {reclassifyMutation.isPending ? 'Classifying...' : 'Re-classify'}
                            </Button>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
