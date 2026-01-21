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
import { classificationApi, ClassificationHistoryEntry, ProviderStats } from '@/api/classification';

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
function StatsOverview({ stats }: { stats: { total_classifications: number; by_provider: ProviderStats[] } }) {
    const totalRuns = stats.total_classifications;
    const providers = stats.by_provider;
    const avgLatency = providers.length > 0
        ? providers.reduce((sum, p) => sum + (p.avg_latency_ms || 0), 0) / providers.length
        : 0;
    const avgConfidence = providers.length > 0
        ? providers.reduce((sum, p) => sum + (p.avg_confidence || 0), 0) / providers.length
        : 0;

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

// Timeline Entry Component
function TimelineEntry({ entry }: { entry: ClassificationHistoryEntry }) {
    return (
        <div className="flex items-start gap-3 p-3 bg-neutral-800/50 border border-neutral-700 hover:border-neutral-600 transition-colors">
            {/* Status Indicator */}
            <div className={`w-2 h-2 rounded-full mt-2 ${entry.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                }`} />

            {/* Content */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
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
                            <span className="text-xs text-neutral-500 font-mono">
                                {entry.sheet_number}
                            </span>
                        </>
                    )}
                </div>

                <div className="text-sm text-white mb-1">
                    {entry.classification || 'No classification'}
                </div>

                <div className="flex items-center gap-3 text-xs text-neutral-500 font-mono">
                    <span>Confidence: {((entry.classification_confidence || 0) * 100).toFixed(1)}%</span>
                    <span>•</span>
                    <span>Latency: {entry.llm_latency_ms?.toFixed(0) || 'N/A'} ms</span>
                    <span>•</span>
                    <span>{formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}</span>
                </div>
            </div>
        </div>
    );
}

// Classification Timeline Component
function ClassificationTimeline({ history }: { history: ClassificationHistoryEntry[] }) {
    const [filterProvider, setFilterProvider] = useState<string | null>(null);

    const filteredHistory = filterProvider
        ? history.filter(h => h.llm_provider === filterProvider)
        : history;

    const providers = Array.from(new Set(history.map(h => h.llm_provider)));

    return (
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
                            <TimelineEntry key={entry.id} entry={entry} />
                        ))
                    )}
                </div>
            </CardContent>
        </Card>
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
                <StatsOverview stats={stats} />

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
