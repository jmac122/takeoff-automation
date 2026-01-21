/**
 * PageCard component for displaying page information with thumbnail and actions.
 */

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { FileText } from 'lucide-react';
import { Link } from 'react-router-dom';

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
    isSelectMode?: boolean;
    isSelected?: boolean;
    onToggleSelect?: (pageId: string) => void;
}

export function PageCard({
    page,
    documentId,
    isSelectMode = false,
    isSelected = false,
    onToggleSelect
}: PageCardProps) {
    return (
        <Card className={`hover:shadow-lg transition-all bg-neutral-900 border-neutral-700 ${isSelectMode && isSelected ? 'ring-2 ring-amber-500' : ''
            }`}>
            <CardContent className="p-3">
                {/* Checkbox in Select Mode */}
                {isSelectMode && (
                    <div className="absolute top-2 left-2 z-10">
                        <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => onToggleSelect?.(page.id)}
                            className="w-6 h-6 bg-neutral-900 border-2 border-amber-500 data-[state=checked]:bg-amber-500 data-[state=checked]:border-amber-500"
                        />
                    </div>
                )}

                {/* Thumbnail */}
                <div
                    className="relative aspect-[8.5/11] bg-neutral-800 mb-2 rounded overflow-hidden cursor-pointer"
                    onClick={() => isSelectMode && onToggleSelect?.(page.id)}
                >
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

                    {/* Sheet Number & Title - Edge to Edge */}
                    {page.sheet_number && (
                        <div className="absolute top-0 left-0 right-0 bg-neutral-900/95 backdrop-blur-sm border-b border-neutral-700 px-3 py-2">
                            <div className="text-sm font-bold text-white font-mono">
                                {page.sheet_number}
                                {page.title && (
                                    <span className="text-xs font-normal text-neutral-400 ml-1">
                                        - {page.title}
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Classification (Discipline:Type) - Edge to Edge, Below Sheet Title */}
                    {page.classification && (
                        <div
                            className="absolute left-0 right-0 bg-neutral-900/95 backdrop-blur-sm border-b border-neutral-700 px-3 py-2"
                            style={{ top: page.sheet_number ? '42px' : '0' }}
                        >
                            <div className="text-xs text-neutral-300 font-mono truncate">
                                {page.classification}
                            </div>
                        </div>
                    )}

                    {/* Confidence Bar - Edge to Edge, Below Classification */}
                    {page.classification_confidence && (
                        <div
                            className="absolute left-0 right-0 bg-neutral-900/95 backdrop-blur-sm px-3 py-2"
                            style={{
                                top: page.sheet_number && page.classification ? '84px' :
                                    page.sheet_number ? '42px' :
                                        page.classification ? '42px' : '0'
                            }}
                        >
                            <div className="flex items-center gap-2">
                                <div className="flex-1 h-1.5 bg-neutral-700 rounded-full overflow-hidden">
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
                        </div>
                    )}

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
                {!isSelectMode && (
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
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
