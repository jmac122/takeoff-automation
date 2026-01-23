import { ChevronRight, ChevronLeft, Clock, CheckCircle2, XCircle, MapPin, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Page } from '@/types';
import { useQuery } from '@tanstack/react-query';
import { classificationApi, type ClassificationHistoryEntry } from '@/api/classification';
import { useState } from 'react';

interface ClassificationSidebarProps {
    page: Page | undefined;
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

export function ClassificationSidebar({
    page,
    isCollapsed,
    onToggleCollapse,
}: ClassificationSidebarProps) {
    const [showScaleHistory, setShowScaleHistory] = useState(false);

    // Fetch classification history for this page
    const { data: historyData } = useQuery({
        queryKey: ['classification-history', page?.id],
        queryFn: () => classificationApi.getPageHistory(page!.id),
        enabled: !!page?.id,
    });

    if (!page) return null;

    // Use the most recent successful classification from history (has all the data)
    const latestClassification = historyData?.history?.[0];

    // Use classification history data if available, otherwise fall back to page data
    const displayData = latestClassification || page;
    const hasClassification = displayData.discipline || displayData.page_type || displayData.classification;
    const relevanceBadgeColor = getRelevanceBadgeColor(displayData.concrete_relevance);

    // Extract scale detection info
    const scaleDetectionData = page.scale_calibration_data;
    const hasScaleBbox = scaleDetectionData?.best_scale?.bbox;

    return (
        <div className="relative flex-shrink-0">
            {/* Collapsed state - show expand button */}
            {isCollapsed && (
                <div className="w-10 bg-neutral-900 border-l border-neutral-700 h-full flex items-start justify-center pt-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onToggleCollapse}
                        className="w-8 h-8 p-0 text-neutral-400 hover:text-white hover:bg-neutral-700"
                        title="Expand sidebar"
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </Button>
                </div>
            )}

            {/* Expanded state */}
            <div
                className={cn(
                    'bg-neutral-900 border-l border-neutral-700 transition-all duration-300 overflow-y-auto',
                    isCollapsed ? 'w-0 hidden' : 'w-80'
                )}
            >
                <div className="h-full">
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-700 bg-neutral-800">
                        <h2 className="text-xs font-mono tracking-widest text-neutral-400 uppercase">
                            Classification
                        </h2>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onToggleCollapse}
                            className="w-8 h-8 p-0 text-neutral-400 hover:text-white hover:bg-neutral-700"
                            title="Collapse sidebar"
                        >
                            <ChevronRight className="w-4 h-4" />
                        </Button>
                    </div>

                    {/* Content */}
                    <div className="p-4 space-y-6">
                        {!hasClassification ? (
                            <div className="text-sm text-neutral-500 font-mono">
                                No classification data available
                            </div>
                        ) : (
                            <>
                                {/* Classification Summary */}
                                <div>
                                    <div className="text-xl font-bold text-white mb-2">
                                        {displayData.discipline && displayData.page_type
                                            ? `${displayData.discipline}:${displayData.page_type}`
                                            : displayData.classification || 'Unclassified'}
                                    </div>
                                    {displayData.classification_confidence && (
                                        <div className="space-y-1">
                                            <div className="flex items-center justify-between text-xs font-mono">
                                                <span className="text-neutral-500">CONFIDENCE</span>
                                                <span className="text-amber-500">
                                                    {(displayData.classification_confidence * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                            <div className="w-full h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-amber-500 transition-all"
                                                    style={{
                                                        width: `${(displayData.classification_confidence * 100).toFixed(0)}%`,
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Discipline */}
                                {displayData.discipline && (
                                    <div>
                                        <div className="text-xs font-mono tracking-wider text-neutral-500 uppercase mb-1">
                                            Discipline
                                        </div>
                                        <div className="text-sm text-white font-mono">
                                            {displayData.discipline}
                                            {displayData.discipline_confidence && (
                                                <span className="text-neutral-500 ml-2">
                                                    ({(displayData.discipline_confidence * 100).toFixed(0)}%)
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Page Type */}
                                {displayData.page_type && (
                                    <div>
                                        <div className="text-xs font-mono tracking-wider text-neutral-500 uppercase mb-1">
                                            Page Type
                                        </div>
                                        <div className="text-sm text-white font-mono">
                                            {displayData.page_type}
                                            {displayData.page_type_confidence && (
                                                <span className="text-neutral-500 ml-2">
                                                    ({(displayData.page_type_confidence * 100).toFixed(0)}%)
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Concrete Relevance */}
                                {displayData.concrete_relevance && (
                                    <div>
                                        <div className="text-xs font-mono tracking-wider text-neutral-500 uppercase mb-1">
                                            Concrete Relevance
                                        </div>
                                        <div>
                                            <span
                                                className={cn(
                                                    'inline-block px-2 py-0.5 text-xs font-mono tracking-widest uppercase border',
                                                    relevanceBadgeColor
                                                )}
                                            >
                                                {displayData.concrete_relevance}
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* Elements Detected */}
                                {displayData.concrete_elements && displayData.concrete_elements.length > 0 && (
                                    <div>
                                        <div className="text-xs font-mono tracking-wider text-neutral-500 uppercase mb-2">
                                            Elements Detected ({displayData.concrete_elements.length})
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            {displayData.concrete_elements.map((element, index) => (
                                                <span
                                                    key={index}
                                                    className="px-2 py-1 text-xs font-mono bg-green-500/20 text-green-400 border border-green-500/50 rounded"
                                                >
                                                    {element}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Description */}
                                {displayData.description && (
                                    <div>
                                        <div className="text-xs font-mono tracking-wider text-neutral-500 uppercase mb-1">
                                            Description
                                        </div>
                                        <div className="text-sm text-neutral-300 leading-relaxed">
                                            {displayData.description}
                                        </div>
                                    </div>
                                )}

                                {/* Technical Details */}
                                <div className="pt-4 border-t border-neutral-800">
                                    <div className="space-y-2 text-xs font-mono">
                                        {displayData.llm_provider && (
                                            <div className="flex justify-between">
                                                <span className="text-neutral-500">Provider:</span>
                                                <span className="text-neutral-300 uppercase">{displayData.llm_provider}</span>
                                            </div>
                                        )}
                                        {displayData.llm_latency_ms && (
                                            <div className="flex justify-between">
                                                <span className="text-neutral-500">Latency:</span>
                                                <span className="text-neutral-300">{displayData.llm_latency_ms}ms</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Scale Detection Info */}
                                {scaleDetectionData && (
                                    <div className="pt-4 border-t border-neutral-800">
                                        <button
                                            onClick={() => setShowScaleHistory(!showScaleHistory)}
                                            className="w-full flex items-center justify-between text-xs font-mono tracking-wider text-neutral-500 uppercase mb-3 hover:text-neutral-300 transition-colors"
                                        >
                                            <span>Scale Detection {hasScaleBbox ? '(Has Location)' : ''}</span>
                                            {showScaleHistory ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                        </button>
                                        {showScaleHistory && (
                                            <div className="space-y-3 text-sm">
                                                {scaleDetectionData.best_scale && (
                                                    <div>
                                                        <div className="text-xs text-neutral-500 mb-1">Best Scale</div>
                                                        <div className="text-white font-mono">{scaleDetectionData.best_scale.text}</div>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <span className="text-xs text-neutral-400">
                                                                Confidence: {((scaleDetectionData.best_scale.confidence || 0) * 100).toFixed(0)}%
                                                            </span>
                                                            {hasScaleBbox && (
                                                                <span className="flex items-center gap-1 text-xs text-green-400">
                                                                    <MapPin className="w-3 h-3" />
                                                                    Location saved
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="text-xs text-neutral-500 mt-1">
                                                            Method: {scaleDetectionData.best_scale.method?.replace(/_/g, ' ')}
                                                        </div>
                                                    </div>
                                                )}
                                        {scaleDetectionData.parsed_scales && scaleDetectionData.parsed_scales.length > 1 && (
                                                    <div>
                                                        <div className="text-xs text-neutral-500 mb-1">
                                                            Alternative Scales Found ({scaleDetectionData.parsed_scales.length - 1})
                                                        </div>
                                                        <div className="space-y-1">
                                                    {getParsedScales(scaleDetectionData.parsed_scales)
                                                        .slice(0, 3)
                                                        .map((scale, idx) => (
                                                            <div key={idx} className="text-xs text-neutral-400 font-mono">
                                                                • {scale.text} ({(scale.confidence * 100).toFixed(0)}%)
                                                            </div>
                                                        ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Classification History Timeline */}
                                {historyData && historyData.history.length > 0 && (
                                    <div className="pt-4 border-t border-neutral-800">
                                        <div className="text-xs font-mono tracking-wider text-neutral-500 uppercase mb-3">
                                            Classification History ({historyData.total})
                                        </div>
                                        <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                                            {historyData.history.map((entry) => (
                                                <ClassificationHistoryItem key={entry.id} entry={entry} />
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function ClassificationHistoryItem({ entry }: { entry: ClassificationHistoryEntry }) {
    const isSuccess = entry.status === 'completed';
    const isError = entry.status === 'error';
    const date = new Date(entry.created_at);
    const timeAgo = getTimeAgo(date);

    return (
        <div className="border border-neutral-800 rounded-lg p-3 bg-neutral-900/50 hover:bg-neutral-800/50 transition-colors">
            {/* Header: Status & Time */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                    {isSuccess && <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />}
                    {isError && <XCircle className="w-3.5 h-3.5 text-red-500" />}
                    {!isSuccess && !isError && <Clock className="w-3.5 h-3.5 text-amber-500" />}
                    <span className={cn(
                        'text-xs font-mono uppercase tracking-wider',
                        isSuccess && 'text-green-500',
                        isError && 'text-red-500',
                        !isSuccess && !isError && 'text-amber-500'
                    )}>
                        {entry.status}
                    </span>
                </div>
                <span className="text-xs text-neutral-500 font-mono">{timeAgo}</span>
            </div>

            {/* Classification Result */}
            {entry.classification && (
                <div className="mb-2">
                    <div className="text-sm font-bold text-white font-mono">
                        {entry.classification}
                    </div>
                    {entry.classification_confidence && (
                        <div className="flex items-center gap-2 mt-1">
                            <div className="flex-1 h-1 bg-neutral-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-amber-500"
                                    style={{ width: `${(entry.classification_confidence * 100).toFixed(0)}%` }}
                                />
                            </div>
                            <span className="text-xs text-neutral-400 font-mono">
                                {(entry.classification_confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                    )}
                </div>
            )}

            {/* Provider & Model */}
            <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-neutral-500">
                    {entry.llm_provider} • {entry.llm_model}
                </span>
                {entry.llm_latency_ms && (
                    <span className="text-neutral-500">{entry.llm_latency_ms}ms</span>
                )}
            </div>

            {/* Concrete Relevance Badge */}
            {entry.concrete_relevance && (
                <div className="mt-2">
                    <span className={cn(
                        'inline-block px-1.5 py-0.5 text-xs font-mono tracking-wider uppercase border rounded',
                        getRelevanceBadgeColor(entry.concrete_relevance)
                    )}>
                        {entry.concrete_relevance}
                    </span>
                </div>
            )}
        </div>
    );
}

function getTimeAgo(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
}

function getRelevanceBadgeColor(relevance: string | null | undefined): string {
    switch (relevance?.toLowerCase()) {
        case 'high':
            return 'bg-green-500/20 text-green-400 border-green-500/50';
        case 'medium':
            return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
        case 'low':
            return 'bg-neutral-500/20 text-neutral-400 border-neutral-500/50';
        default:
            return 'bg-neutral-500/20 text-neutral-400 border-neutral-500/50';
    }
}

function getParsedScales(values: Array<unknown>): Array<{ text: string; confidence: number }> {
    return values
        .filter(isParsedScale)
        .map((scale) => ({
            text: scale.text,
            confidence: scale.confidence ?? 0,
        }));
}

function isParsedScale(value: unknown): value is { text: string; confidence?: number } {
    return (
        typeof value === 'object' &&
        value !== null &&
        'text' in value &&
        typeof (value as { text?: unknown }).text === 'string'
    );
}
