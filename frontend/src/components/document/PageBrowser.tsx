import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../api/client';

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

    const getConcreteBadgeColor = (relevance: string | null): string => {
        switch (relevance) {
            case 'high':
                return 'bg-red-100 text-red-800 border-red-300';
            case 'medium':
                return 'bg-orange-100 text-orange-800 border-orange-300';
            case 'low':
                return 'bg-yellow-100 text-yellow-800 border-yellow-300';
            case 'none':
                return 'bg-gray-100 text-gray-800 border-gray-300';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-300';
        }
    };

    if (isLoading) {
        return (
            <div className="p-4">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-gray-200 rounded w-1/4"></div>
                    <div className="grid grid-cols-4 gap-4">
                        {[...Array(8)].map((_, i) => (
                            <div key={i} className="h-32 bg-gray-200 rounded"></div>
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
                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Discipline</label>
                    <select
                        value={disciplineFilter}
                        onChange={(e) => setDisciplineFilter(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm min-w-[160px]"
                    >
                        {DISCIPLINES.map((d) => (
                            <option key={d.value} value={d.value}>
                                {d.label}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Page Type</label>
                    <select
                        value={pageTypeFilter}
                        onChange={(e) => setPageTypeFilter(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm min-w-[160px]"
                    >
                        {PAGE_TYPES.map((pt) => (
                            <option key={pt.value} value={pt.value}>
                                {pt.label}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-gray-700">Concrete Relevance</label>
                    <select
                        value={concreteFilter}
                        onChange={(e) => setConcreteFilter(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm min-w-[160px]"
                    >
                        {CONCRETE_RELEVANCE.map((cr) => (
                            <option key={cr.value} value={cr.value}>
                                {cr.label}
                            </option>
                        ))}
                    </select>
                </div>

                {(disciplineFilter || pageTypeFilter || concreteFilter) && (
                    <button
                        onClick={() => {
                            setDisciplineFilter('');
                            setPageTypeFilter('');
                            setConcreteFilter('');
                        }}
                        className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                        Clear Filters
                    </button>
                )}
            </div>

            {/* Results count */}
            <div className="text-sm text-gray-600">
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
                            className={`
                relative border rounded-lg overflow-hidden cursor-pointer transition-all
                ${isHighConcrete ? 'border-red-400 border-2 shadow-md' : 'border-gray-300 hover:border-blue-400'}
                ${onPageSelect ? 'hover:shadow-lg' : ''}
              `}
                        >
                            {/* Thumbnail */}
                            {page.thumbnail_url ? (
                                <img
                                    src={page.thumbnail_url}
                                    alt={`Page ${page.page_number}`}
                                    className="w-full h-32 object-contain bg-gray-50"
                                />
                            ) : (
                                <div className="w-full h-32 bg-gray-100 flex items-center justify-center">
                                    <span className="text-gray-400 text-sm">No thumbnail</span>
                                </div>
                            )}

                            {/* Page info overlay */}
                            <div className="p-2 bg-white">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-medium text-gray-900">
                                        {disciplinePrefix && (
                                            <span className="inline-block px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded text-xs mr-1">
                                                {disciplinePrefix}
                                            </span>
                                        )}
                                        Page {page.page_number}
                                    </span>
                                    {page.classification_confidence !== null && (
                                        <span className="text-xs text-gray-500">
                                            {(page.classification_confidence * 100).toFixed(0)}%
                                        </span>
                                    )}
                                </div>

                                {page.sheet_number && (
                                    <div className="text-xs text-gray-600 mb-1">{page.sheet_number}</div>
                                )}

                                {page.title && (
                                    <div className="text-xs text-gray-700 truncate mb-1" title={page.title}>
                                        {page.title}
                                    </div>
                                )}

                                {page.classification && (
                                    <div className="text-xs text-gray-600 mb-1">{page.classification}</div>
                                )}

                                {/* Concrete relevance badge */}
                                {page.concrete_relevance && (
                                    <div className="mt-1">
                                        <span
                                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getConcreteBadgeColor(
                                                page.concrete_relevance
                                            )}`}
                                        >
                                            {page.concrete_relevance === 'high' && '🔴 '}
                                            {page.concrete_relevance === 'medium' && '🟠 '}
                                            {page.concrete_relevance === 'low' && '🟡 '}
                                            {page.concrete_relevance === 'none' && '⚪ '}
                                            {page.concrete_relevance}
                                        </span>
                                    </div>
                                )}

                                {/* Classification metadata */}
                                {page.classification_confidence !== null && (
                                    <div className="mt-1 text-xs text-gray-500">
                                        Confidence: {(page.classification_confidence * 100).toFixed(0)}%
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {filteredPages.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                    No pages match the selected filters.
                </div>
            )}
        </div>
    );
}
