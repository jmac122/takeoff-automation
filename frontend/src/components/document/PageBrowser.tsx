import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Filter } from 'lucide-react';
import { apiClient } from '../../api/client';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface Page {
    id: string;
    document_id: string;
    page_number: number;
    width: number;
    height: number;
    classification: string | null;
    classification_confidence: number | null;
    concrete_relevance: string | null;
    title: string | null;
    sheet_number: string | null;
    scale_text: string | null;
    scale_calibrated: boolean;
    status: string;
    thumbnail_url: string | null;
}

interface PageListResponse {
    pages: Page[];
    total: number;
}

interface PageBrowserProps {
    documentId: string;
    onPageSelect?: (pageId: string) => void;
}

const DISCIPLINES = [
    { value: '', label: 'All Disciplines' },
    { value: 'Architectural', label: 'Architectural (A)' },
    { value: 'Structural', label: 'Structural (S)' },
    { value: 'Civil', label: 'Civil/Site (C)' },
    { value: 'Mechanical', label: 'Mechanical (M)' },
    { value: 'Electrical', label: 'Electrical (E)' },
    { value: 'Plumbing', label: 'Plumbing (P)' },
    { value: 'Landscape', label: 'Landscape (L)' },
    { value: 'General', label: 'General/Cover (G)' },
];

const PAGE_TYPES = [
    { value: '', label: 'All Types' },
    { value: 'Plan', label: 'Plan View' },
    { value: 'Elevation', label: 'Elevation' },
    { value: 'Section', label: 'Section' },
    { value: 'Detail', label: 'Detail' },
    { value: 'Schedule', label: 'Schedule' },
    { value: 'Notes', label: 'Notes/Legend' },
    { value: 'Cover', label: 'Cover Sheet' },
    { value: 'Title', label: 'Title Sheet' },
];

const CONCRETE_RELEVANCE = [
    { value: '', label: 'All Relevance' },
    { value: 'high', label: 'High Concrete' },
    { value: 'medium', label: 'Medium Concrete' },
    { value: 'low', label: 'Low Concrete' },
    { value: 'none', label: 'No Concrete' },
];

export function PageBrowser({ documentId, onPageSelect }: PageBrowserProps) {
    const [disciplineFilter, setDisciplineFilter] = useState('');
    const [pageTypeFilter, setPageTypeFilter] = useState('');
    const [concreteFilter, setConcreteFilter] = useState('');

    const { data, isLoading } = useQuery<PageListResponse>({
        queryKey: ['pages', documentId],
        queryFn: async () => {
            const response = await apiClient.get<PageListResponse>(
                `/documents/${documentId}/pages`
            );
            return response.data;
        },
    });

    const pages = data?.pages || [];

    // Filter pages
    const filteredPages = pages.filter((page) => {
        if (disciplineFilter && page.classification) {
            const discipline = page.classification.split(':')[0];
            if (discipline !== disciplineFilter) {
                return false;
            }
        }

        if (pageTypeFilter && page.classification) {
            const pageType = page.classification.split(':')[1];
            if (pageType !== pageTypeFilter) {
                return false;
            }
        }

        if (concreteFilter && page.concrete_relevance !== concreteFilter) {
            return false;
        }

        return true;
    });

    const getDisciplinePrefix = (classification: string | null): string => {
        if (!classification) return '';
        const discipline = classification.split(':')[0];
        const prefixMap: Record<string, string> = {
            Architectural: 'A',
            Structural: 'S',
            Civil: 'C',
            Mechanical: 'M',
            Electrical: 'E',
            Plumbing: 'P',
            Landscape: 'L',
            General: 'G',
        };
        return prefixMap[discipline] || '';
    };

    const getConcreteBadgeVariant = (relevance: string | null): "default" | "secondary" | "destructive" | "outline" => {
        switch (relevance) {
            case 'high':
                return 'destructive';
            case 'medium':
            case 'low':
                return 'secondary';
            default:
                return 'outline';
        }
    };

    if (isLoading) {
        return (
            <div className="p-4">
                <div className="space-y-4">
                    <Skeleton className="h-8 w-1/4" />
                    <div className="grid grid-cols-4 gap-4">
                        {[...Array(8)].map((_, i) => (
                            <Skeleton key={i} className="h-32" />
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="p-4 space-y-4">
            {/* Filters */}
            <div className="flex flex-wrap gap-4 items-end">
                <div className="flex flex-col gap-2">
                    <Label htmlFor="discipline-filter">Discipline</Label>
                    <Select value={disciplineFilter} onValueChange={setDisciplineFilter}>
                        <SelectTrigger id="discipline-filter" className="w-[160px]">
                            <SelectValue placeholder="All Disciplines" />
                        </SelectTrigger>
                        <SelectContent>
                            {DISCIPLINES.map((d) => (
                                <SelectItem key={d.value} value={d.value}>
                                    {d.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <div className="flex flex-col gap-2">
                    <Label htmlFor="page-type-filter">Page Type</Label>
                    <Select value={pageTypeFilter} onValueChange={setPageTypeFilter}>
                        <SelectTrigger id="page-type-filter" className="w-[160px]">
                            <SelectValue placeholder="All Types" />
                        </SelectTrigger>
                        <SelectContent>
                            {PAGE_TYPES.map((pt) => (
                                <SelectItem key={pt.value} value={pt.value}>
                                    {pt.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <div className="flex flex-col gap-2">
                    <Label htmlFor="concrete-filter">Concrete Relevance</Label>
                    <Select value={concreteFilter} onValueChange={setConcreteFilter}>
                        <SelectTrigger id="concrete-filter" className="w-[160px]">
                            <SelectValue placeholder="All Relevance" />
                        </SelectTrigger>
                        <SelectContent>
                            {CONCRETE_RELEVANCE.map((cr) => (
                                <SelectItem key={cr.value} value={cr.value}>
                                    {cr.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                {(disciplineFilter || pageTypeFilter || concreteFilter) && (
                    <Button
                        variant="outline"
                        onClick={() => {
                            setDisciplineFilter('');
                            setPageTypeFilter('');
                            setConcreteFilter('');
                        }}
                    >
                        <Filter className="mr-2 h-4 w-4" />
                        Clear Filters
                    </Button>
                )}
            </div>

            {/* Results count */}
            <div className="text-sm text-muted-foreground">
                Showing {filteredPages.length} of {pages.length} pages
            </div>

            {/* Page grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {filteredPages.map((page) => {
                    const isHighConcrete = page.concrete_relevance === 'high';
                    const disciplinePrefix = getDisciplinePrefix(page.classification);

                    return (
                        <div
                            key={page.id}
                            onClick={() => onPageSelect?.(page.id)}
                            className={cn(
                                "relative border rounded-lg overflow-hidden cursor-pointer transition-all",
                                isHighConcrete ? "border-destructive border-2 shadow-md" : "border-border hover:border-primary",
                                onPageSelect && "hover:shadow-lg"
                            )}
                        >
                            {/* Thumbnail */}
                            {page.thumbnail_url ? (
                                <img
                                    src={page.thumbnail_url}
                                    alt={`Page ${page.page_number}`}
                                    className="w-full h-32 object-contain bg-muted"
                                />
                            ) : (
                                <div className="w-full h-32 bg-muted flex items-center justify-center">
                                    <span className="text-muted-foreground text-sm">No thumbnail</span>
                                </div>
                            )}

                            {/* Page info overlay */}
                            <div className="p-2 bg-card">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-medium text-foreground">
                                        {disciplinePrefix && (
                                            <Badge variant="secondary" className="mr-1 text-xs">
                                                {disciplinePrefix}
                                            </Badge>
                                        )}
                                        Page {page.page_number}
                                    </span>
                                    {page.classification_confidence !== null && (
                                        <span className="text-xs text-muted-foreground">
                                            {(page.classification_confidence * 100).toFixed(0)}%
                                        </span>
                                    )}
                                </div>

                                {page.sheet_number && (
                                    <div className="text-xs text-muted-foreground mb-1">{page.sheet_number}</div>
                                )}

                                {page.title && (
                                    <div className="text-xs text-foreground truncate mb-1" title={page.title}>
                                        {page.title}
                                    </div>
                                )}

                                {page.classification && (
                                    <div className="text-xs text-muted-foreground mb-1">{page.classification}</div>
                                )}

                                {/* Concrete relevance badge */}
                                {page.concrete_relevance && (
                                    <div className="mt-1">
                                        <Badge variant={getConcreteBadgeVariant(page.concrete_relevance)}>
                                            {page.concrete_relevance === 'high' && '🔴 '}
                                            {page.concrete_relevance === 'medium' && '🟠 '}
                                            {page.concrete_relevance === 'low' && '🟡 '}
                                            {page.concrete_relevance === 'none' && '⚪ '}
                                            {page.concrete_relevance}
                                        </Badge>
                                    </div>
                                )}

                                {/* Classification metadata */}
                                {page.classification_confidence !== null && (
                                    <div className="mt-1 text-xs text-muted-foreground">
                                        Confidence: {(page.classification_confidence * 100).toFixed(0)}%
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {filteredPages.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                    No pages match the selected filters.
                </div>
            )}
        </div>
    );
}
