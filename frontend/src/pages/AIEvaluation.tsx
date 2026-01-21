/**
 * AI Evaluation - LLM Analytics Dashboard
 * 
 * Comprehensive analytics dashboard for comparing LLM performance
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { X } from 'lucide-react';
import { classificationApi, ClassificationHistoryEntry, ProviderStats } from '@/api/classification';
import { apiClient } from '@/api/client';

// Metric Card Component
function MetricCard({ label, value, unit }: { label: string; value: string; unit: string }) {
    return (
        <div className="p-4 bg-neutral-900 border border-neutral-700">
            <div className="text-xs font-mono tracking-wider text-neutral-500 uppercase mb-2">
                {label}
            </div>
            <div className="flex items-baseline gap-2">
                <span className="text-3xl font-mono text-white"
                    style={{ fontFeatureSettings: "'tnum'" }}>
                    {value}
                </span>
                <span className="text-sm text-neutral-500">{unit}</span>
            </div>
        </div>
    );
}

// Stats Overview Component
function StatsOverview({
    stats,
    history
}: {
    stats: { total_classifications: number; by_provider: ProviderStats[] };
    history: ClassificationHistoryEntry[];
}) {
    const totalRuns = stats.total_classifications;
    const providers = stats.by_provider;
    const avgLatency = providers.length > 0
        ? providers.reduce((sum, p) => sum + (p.avg_latency_ms || 0), 0) / providers.length
        : 0;
    const avgConfidence = providers.length > 0
        ? providers.reduce((sum, p) => sum + (p.avg_confidence || 0), 0) / providers.length
        : 0;

    // Calculate concrete relevance distribution
    const concreteStats = history.reduce((acc, entry) => {
        const relevance = entry.concrete_relevance || 'unknown';
        acc[relevance] = (acc[relevance] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const highConcreteCount = concreteStats.high || 0;
    const highConcretePercent = history.length > 0
        ? ((highConcreteCount / history.length) * 100).toFixed(0)
        : '0';

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard
                    label="Total Classifications"
                    value={totalRuns.toString()}
                    unit="runs"
                />
                <MetricCard
                    label="Avg Latency"
                    value={avgLatency > 0 ? avgLatency.toFixed(0) : 'N/A'}
                    unit="ms"
                />
                <MetricCard
                    label="Avg Confidence"
                    value={avgConfidence > 0 ? (avgConfidence * 100).toFixed(1) : 'N/A'}
                    unit="%"
                />
                <MetricCard
                    label="High Concrete Relevance"
                    value={highConcretePercent}
                    unit="%"
                />
            </div>

            {/* Concrete Relevance Breakdown */}
            {history.length > 0 && (
                <Card className="bg-neutral-900 border-neutral-700">
                    <CardHeader className="border-b border-neutral-700">
                        <CardTitle className="text-white uppercase tracking-tight font-mono text-sm">
                            Concrete Relevance Distribution
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {(['high', 'medium', 'low', 'none'] as const).map(relevance => {
                                const count = concreteStats[relevance] || 0;
                                const percent = ((count / history.length) * 100).toFixed(1);
                                const colors = {
                                    high: 'text-green-400',
                                    medium: 'text-amber-400',
                                    low: 'text-neutral-400',
                                    none: 'text-neutral-600',
                                };
                                return (
                                    <div key={relevance} className="text-center">
                                        <div className={`text-2xl font-mono font-bold ${colors[relevance]}`}>
                                            {count}
                                        </div>
                                        <div className="text-xs text-neutral-500 font-mono uppercase mt-1">
                                            {relevance} ({percent}%)
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}

// Confidence Badge Component
function ConfidenceBadge({ confidence }: { confidence: number | null }) {
    if (!confidence) return <span className="text-neutral-500 font-mono">N/A</span>;

    const percentage = (confidence * 100).toFixed(1);
    const color = confidence >= 0.8 ? 'text-green-500' :
        confidence >= 0.6 ? 'text-amber-500' : 'text-red-500';

    return <span className={`${color} font-bold font-mono`}>{percentage}%</span>;
}

// Provider Comparison Table Component
function ProviderComparisonTable({ providers }: { providers: ProviderStats[] }) {
    return (
        <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader className="border-b border-neutral-700">
                <CardTitle className="text-white uppercase tracking-tight font-mono">
                    Provider Performance
                </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
                <Table>
                    <TableHeader>
                        <TableRow className="border-neutral-700 hover:bg-neutral-800/50">
                            <TableHead className="text-neutral-400 font-mono text-xs uppercase tracking-wider">
                                Provider
                            </TableHead>
                            <TableHead className="text-neutral-400 font-mono text-xs uppercase tracking-wider">
                                Model
                            </TableHead>
                            <TableHead className="text-right text-neutral-400 font-mono text-xs uppercase tracking-wider">
                                Runs
                            </TableHead>
                            <TableHead className="text-right text-neutral-400 font-mono text-xs uppercase tracking-wider">
                                Avg Latency
                            </TableHead>
                            <TableHead className="text-right text-neutral-400 font-mono text-xs uppercase tracking-wider">
                                Avg Confidence
                            </TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {providers.map((provider, idx) => (
                            <TableRow key={idx} className="border-neutral-800 hover:bg-neutral-900/50">
                                <TableCell className="font-medium text-white font-mono">
                                    {provider.provider}
                                </TableCell>
                                <TableCell className="text-neutral-300 font-mono text-sm">
                                    {provider.model}
                                </TableCell>
                                <TableCell className="text-right text-white font-mono"
                                    style={{ fontFeatureSettings: "'tnum'" }}>
                                    {provider.total_runs}
                                </TableCell>
                                <TableCell className="text-right text-neutral-300 font-mono"
                                    style={{ fontFeatureSettings: "'tnum'" }}>
                                    {provider.avg_latency_ms?.toFixed(0) || 'N/A'} ms
                                </TableCell>
                                <TableCell className="text-right font-mono">
                                    <ConfidenceBadge confidence={provider.avg_confidence} />
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}

// Classification Detail Modal Component
function ClassificationDetailModal({
    entry,
    isOpen,
    onClose
}: {
    entry: ClassificationHistoryEntry | null;
    isOpen: boolean;
    onClose: () => void;
}) {
    const [imageUrl, setImageUrl] = useState<string | null>(null);

    // Fetch page image when modal opens
    const { data: pageData } = useQuery({
        queryKey: ['page-detail', entry?.page_id],
        queryFn: async () => {
            if (!entry?.page_id) return null;
            const response = await apiClient.get(`/pages/${entry.page_id}`);
            return response.data;
        },
        enabled: isOpen && !!entry?.page_id,
    });

    // Set image URL when page data loads
    useState(() => {
        if (pageData?.image_url) {
            setImageUrl(pageData.image_url);
        }
    });

    if (!entry) return null;

    const getRelevanceBadge = (relevance: string | null) => {
        if (!relevance) return null;
        const colors = {
            high: 'bg-green-500 text-white',
            medium: 'bg-amber-500 text-black',
            low: 'bg-neutral-600 text-white',
            none: 'bg-neutral-700 text-white',
        };
        return (
            <span className={`px-3 py-1 text-sm font-mono uppercase tracking-wider rounded ${colors[relevance as keyof typeof colors] || colors.none}`}>
                {relevance}
            </span>
        );
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-7xl h-[90vh] bg-neutral-900 border-neutral-700 p-0 overflow-hidden">
                {/* Header */}
                <DialogHeader className="px-6 py-4 border-b border-neutral-700">
                    <div className="flex items-center justify-between">
                        <DialogTitle className="text-xl font-mono text-white">
                            {entry.sheet_number || `Page ${entry.page_number}`}
                        </DialogTitle>
                        <button
                            onClick={onClose}
                            className="text-neutral-400 hover:text-white transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </DialogHeader>

                {/* Content: Split View */}
                <div className="flex h-full overflow-hidden">
                    {/* Left: Page Image */}
                    <div className="w-1/2 bg-neutral-950 p-6 overflow-auto">
                        {imageUrl ? (
                            <img
                                src={imageUrl}
                                alt={`Page ${entry.page_number}`}
                                className="w-full h-auto rounded border border-neutral-700"
                            />
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-neutral-500 font-mono">Loading image...</div>
                            </div>
                        )}
                    </div>

                    {/* Right: Classification Details */}
                    <div className="w-1/2 bg-neutral-900 p-6 overflow-auto space-y-6">
                        {/* Model Information */}
                        <div>
                            <h3 className="text-xs font-mono text-neutral-500 uppercase tracking-wider mb-3">
                                Model Information
                            </h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-neutral-400">Provider:</span>
                                    <span className="text-amber-500 font-mono uppercase">{entry.llm_provider}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-neutral-400">Model:</span>
                                    <span className="text-white font-mono">{entry.llm_model}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-neutral-400">Latency:</span>
                                    <span className="text-white font-mono">{entry.llm_latency_ms?.toFixed(0) || 'N/A'} ms</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-neutral-400">Confidence:</span>
                                    <span className="text-white font-mono font-bold">
                                        {((entry.classification_confidence || 0) * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-neutral-400">Status:</span>
                                    <span className={`font-mono ${entry.status === 'success' ? 'text-green-500' : 'text-red-500'}`}>
                                        {entry.status}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-neutral-400">Classified:</span>
                                    <span className="text-neutral-300 text-xs">
                                        {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Classification Output */}
                        <div>
                            <h3 className="text-xs font-mono text-neutral-500 uppercase tracking-wider mb-3">
                                Classification Output
                            </h3>
                            <div className="space-y-3">
                                <div>
                                    <div className="text-xs text-neutral-500 mb-1">Classification</div>
                                    <div className="text-lg text-white font-mono">{entry.classification || 'N/A'}</div>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <div className="text-xs text-neutral-500 mb-1">Discipline</div>
                                        <div className="text-white font-mono">
                                            {entry.discipline || 'N/A'}
                                            {entry.discipline_confidence && (
                                                <span className="text-neutral-500 text-xs ml-2">
                                                    ({(entry.discipline_confidence * 100).toFixed(0)}%)
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-neutral-500 mb-1">Page Type</div>
                                        <div className="text-white font-mono">
                                            {entry.page_type || 'N/A'}
                                            {entry.page_type_confidence && (
                                                <span className="text-neutral-500 text-xs ml-2">
                                                    ({(entry.page_type_confidence * 100).toFixed(0)}%)
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs text-neutral-500 mb-1">Concrete Relevance</div>
                                    <div>{getRelevanceBadge(entry.concrete_relevance)}</div>
                                </div>
                            </div>
                        </div>

                        {/* Concrete Elements */}
                        {entry.concrete_elements && entry.concrete_elements.length > 0 && (
                            <div>
                                <h3 className="text-xs font-mono text-neutral-500 uppercase tracking-wider mb-3">
                                    Concrete Elements Detected ({entry.concrete_elements.length})
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {entry.concrete_elements.map((element: string, idx: number) => (
                                        <span
                                            key={idx}
                                            className="px-3 py-1 text-sm font-mono bg-green-500/20 text-green-400 border border-green-500/30 rounded"
                                        >
                                            {element}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Description */}
                        {entry.description && (
                            <div>
                                <h3 className="text-xs font-mono text-neutral-500 uppercase tracking-wider mb-3">
                                    Description
                                </h3>
                                <div className="text-sm text-neutral-300 leading-relaxed">
                                    {entry.description}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

// Timeline Entry Component
function TimelineEntry({
    entry,
    onClick
}: {
    entry: ClassificationHistoryEntry;
    onClick: () => void;
}) {

    // Get concrete relevance badge color
    const getRelevanceBadge = (relevance: string | null) => {
        if (!relevance) return null;
        const colors = {
            high: 'bg-green-500/20 text-green-400 border-green-500/50',
            medium: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
            low: 'bg-neutral-600/20 text-neutral-400 border-neutral-600/50',
            none: 'bg-neutral-700/20 text-neutral-500 border-neutral-700/50',
        };
        return (
            <span className={`px-2 py-0.5 text-xs font-mono uppercase tracking-wider rounded border ${colors[relevance as keyof typeof colors] || colors.none}`}>
                {relevance}
            </span>
        );
    };

    return (
        <div
            className="bg-neutral-800/50 border border-neutral-700 hover:border-amber-500/50 hover:bg-neutral-800 transition-all cursor-pointer"
            onClick={onClick}
        >
            {/* Main Row */}
            <div className="flex items-start gap-3 p-3">
                {/* Status Indicator */}
                <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${entry.status === 'success' ? 'bg-green-500' : 'bg-red-500'}`} />

                {/* Content */}
                <div className="flex-1 min-w-0">
                    {/* Header Row */}
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-xs font-mono text-amber-500 uppercase tracking-wider">
                            {entry.llm_provider}
                        </span>
                        <span className="text-xs text-neutral-600">•</span>
                        <span className="text-xs text-neutral-500 font-mono">
                            Page {entry.page_number}
                        </span>
                        {entry.sheet_number && (
                            <>
                                <span className="text-xs text-neutral-600">•</span>
                                <span className="text-xs text-neutral-400 font-mono font-bold">
                                    {entry.sheet_number}
                                </span>
                            </>
                        )}
                        {entry.concrete_relevance && getRelevanceBadge(entry.concrete_relevance)}
                    </div>

                    {/* Classification */}
                    <div className="text-sm text-white mb-1 font-mono">
                        {entry.classification || 'No classification'}
                    </div>

                    {/* Description (if available) */}
                    {entry.description && (
                        <div className="text-xs text-neutral-400 mb-2 line-clamp-2">
                            {entry.description}
                        </div>
                    )}

                    {/* Metrics Row */}
                    <div className="flex items-center gap-3 text-xs text-neutral-500 font-mono flex-wrap">
                        <span>Confidence: {((entry.classification_confidence || 0) * 100).toFixed(1)}%</span>
                        <span>•</span>
                        <span>Latency: {entry.llm_latency_ms?.toFixed(0) || 'N/A'} ms</span>
                        <span>•</span>
                        <span>{formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}</span>
                        <span className="ml-auto text-amber-500 text-xs">Click to view details →</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Classification Timeline Component
function ClassificationTimeline({ history }: { history: ClassificationHistoryEntry[] }) {
    const [filterProvider, setFilterProvider] = useState<string | null>(null);
    const [selectedEntry, setSelectedEntry] = useState<ClassificationHistoryEntry | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleEntryClick = (entry: ClassificationHistoryEntry) => {
        setSelectedEntry(entry);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setTimeout(() => setSelectedEntry(null), 300); // Clear after animation
    };

    const filteredHistory = filterProvider
        ? history.filter(h => h.llm_provider === filterProvider)
        : history;

    const providers = Array.from(new Set(history.map(h => h.llm_provider)));

    return (
        <>
            <Card className="bg-neutral-900 border-neutral-700">
                <CardHeader className="border-b border-neutral-700">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-white uppercase tracking-tight font-mono">
                            Classification Timeline
                        </CardTitle>
                        <Select value={filterProvider || 'all'}
                            onValueChange={(v) => setFilterProvider(v === 'all' ? null : v)}>
                            <SelectTrigger className="w-[180px] bg-neutral-800 border-neutral-700 text-white font-mono">
                                <SelectValue placeholder="Filter by provider" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Providers</SelectItem>
                                {providers.map(p => (
                                    <SelectItem key={p} value={p}>{p}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardHeader>
                <CardContent className="p-4">
                    <div className="space-y-2 max-h-[500px] overflow-y-auto">
                        {filteredHistory.length === 0 ? (
                            <p className="text-center text-neutral-500 font-mono py-8">
                                No classification history found.
                            </p>
                        ) : (
                            filteredHistory.map((entry) => (
                                <TimelineEntry
                                    key={entry.id}
                                    entry={entry}
                                    onClick={() => handleEntryClick(entry)}
                                />
                            ))
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Classification Detail Modal */}
            <ClassificationDetailModal
                entry={selectedEntry}
                isOpen={isModalOpen}
                onClose={handleCloseModal}
            />
        </>
    );
}

// Main Component
export default function AIEvaluation() {
    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ['classification-stats'],
        queryFn: classificationApi.getStats,
    });

    const { data: history, isLoading: historyLoading } = useQuery({
        queryKey: ['classification-history'],
        queryFn: () => classificationApi.getHistory(100),
    });

    if (statsLoading || historyLoading) {
        return (
            <div className="min-h-screen bg-neutral-950">
                <div className="container mx-auto px-4 py-6 space-y-6">
                    <Skeleton className="h-32 w-full bg-neutral-900" />
                    <Skeleton className="h-64 w-full bg-neutral-900" />
                </div>
            </div>
        );
    }

    if (!stats || !history) {
        return (
            <div className="min-h-screen bg-neutral-950">
                <div className="container mx-auto px-4 py-6">
                    <Alert variant="destructive" className="bg-red-900/20 border-red-500/50">
                        <AlertDescription className="text-red-400 font-mono">
                            Failed to load AI evaluation data
                        </AlertDescription>
                    </Alert>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-neutral-950">
            <div className="container mx-auto px-4 py-6 space-y-6">
                {/* Header */}
                <div className="mb-6">
                    <div className="flex items-center gap-3 mb-2">
                        <span className="text-neutral-600 font-mono text-xs">[AI-EVAL]</span>
                        <div className="flex-1 h-px bg-neutral-800" />
                    </div>
                    <h1 className="text-3xl font-bold text-white uppercase tracking-tight"
                        style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
                        AI Evaluation Dashboard
                    </h1>
                    <p className="text-neutral-400 font-mono text-sm mt-1">
                        Compare LLM performance across all classification runs
                    </p>
                </div>

                {/* Stats Overview */}
                <StatsOverview stats={stats} history={history.history} />

                {/* Provider Comparison */}
                {stats.by_provider.length > 0 && (
                    <ProviderComparisonTable providers={stats.by_provider} />
                )}

                {/* Classification Timeline */}
                <ClassificationTimeline history={history.history} />
            </div>
        </div>
    );
}
