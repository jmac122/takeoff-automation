# Phase 0 Enhancements - Implementation Plan

**Created:** January 20, 2026  
**Status:** Ready for Implementation  
**Estimated Effort:** 8-12 hours

---

## Overview

This plan details the implementation of four critical enhancements to the Phase 0 Application Interface:

1. **Testing Tab** - Restore the classification testing interface from the old Dashboard
2. **AI Evaluation Tab** - Build a comprehensive LLM comparison and analytics dashboard
3. **DocumentDetail Enhancements** - Add classification controls and confidence display
4. **TakeoffViewer Scale Calibration** - Fix click detection for manual scale setting

All implementations must adhere to:
- **Design System:** `docs/design/DESIGN-SYSTEM.md`
- **Component Library:** `docs/design/COMPONENT_LIBRARY.md`
- **Coding Standards:** SOLID, DRY, KISS principles (`.cursor/rules/coding-standards.mdc`)
- **UI Aesthetic:** Industrial/Tactical UI design (`.cursor/rules/industrial-tactical-ui.mdc`)

---

## Task 1: Testing Tab (Classification Testing Interface)

### Objective
Restore the old Dashboard as a dedicated testing interface accessible via navigation tabs, allowing rapid classification testing with different LLM providers.

### Requirements

#### 1.1 Update Header Navigation
**File:** `frontend/src/components/layout/Header.tsx`

**Changes:**
- Add navigation tabs: `Projects`, `Testing`, `AI Evaluation`
- Use `useLocation()` to highlight active tab
- Apply industrial/tactical styling with uppercase labels and wide letter-spacing

**Implementation:**
```typescript
import { Link, useLocation } from 'react-router-dom';

export function Header() {
    const location = useLocation();
    
    const isActive = (path: string) => location.pathname.startsWith(path);
    
    const navItems = [
        { path: '/projects', label: 'PROJECTS' },
        { path: '/testing', label: 'TESTING' },
        { path: '/ai-evaluation', label: 'AI EVALUATION' },
    ];
    
    return (
        <header className="border-b bg-neutral-900 sticky top-0 z-50 shadow-lg">
            <div className="container mx-auto px-4 py-3">
                <div className="flex items-center justify-between">
                    {/* Logo */}
                    <Link to="/projects" className="flex items-center gap-2">
                        <h1 className="text-xl font-bold text-amber-500 tracking-tight uppercase"
                            style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
                            ForgeX Takeoffs
                        </h1>
                    </Link>
                    
                    {/* Navigation Tabs */}
                    <nav className="flex items-center gap-1">
                        {navItems.map(item => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`px-4 py-2 text-xs font-mono tracking-widest transition-colors ${
                                    isActive(item.path)
                                        ? 'bg-amber-500/20 text-amber-500 border-b-2 border-amber-500'
                                        : 'text-neutral-400 hover:text-white hover:bg-neutral-800'
                                }`}
                            >
                                {item.label}
                            </Link>
                        ))}
                    </nav>
                </div>
            </div>
        </header>
    );
}
```

**Design Notes:**
- Dark background (`bg-neutral-900`) for tactical feel
- Amber accent color for active state
- Monospace font with wide tracking for labels
- Border-bottom indicator for active tab

#### 1.2 Restore Dashboard as Testing Page
**File:** `frontend/src/pages/Testing.tsx` (rename from `Dashboard.tsx.bak`)

**Changes:**
1. Rename `Dashboard.tsx.bak` → `Testing.tsx`
2. Update page title to "Classification Testing"
3. Add tactical styling to match industrial UI aesthetic
4. Keep all existing functionality:
   - Document upload
   - LLM provider selection
   - "Classify All Pages" button
   - Page grid with classification results
   - Page detail viewer

**Styling Updates:**
```typescript
// Update header card styling
<Card className="bg-neutral-900 border-neutral-700">
    <CardHeader className="border-b border-neutral-700">
        <div className="flex items-center gap-3 mb-2">
            <span className="text-neutral-600 font-mono text-xs">[TESTING]</span>
            <div className="flex-1 h-px bg-neutral-800" />
        </div>
        <CardTitle className="text-2xl text-white uppercase tracking-tight"
                   style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
            Classification Testing
        </CardTitle>
        <CardDescription className="text-neutral-400 font-mono text-sm">
            Upload plans and test LLM classification accuracy
        </CardDescription>
    </CardHeader>
    {/* ... content ... */}
</Card>
```

**Component Updates:**
- `PageInfoCard`: Add confidence percentage badge
- `LLMProviderSelector`: Style with tactical dropdown
- Status badges: Use industrial color scheme (green=success, amber=processing, red=error)

#### 1.3 Update App Routing
**File:** `frontend/src/App.tsx`

**Changes:**
```typescript
import Testing from "./pages/Testing";

// Add route
<Route path="/testing" element={<Testing />} />
```

#### 1.4 Update DocumentUploader Import
**File:** `frontend/src/pages/Testing.tsx`

**Changes:**
```typescript
// Ensure named import
import { DocumentUploader } from "@/components/document/DocumentUploader";
```

### Acceptance Criteria
- [ ] Header shows three navigation tabs
- [ ] Active tab is visually highlighted
- [ ] `/testing` route loads the classification testing interface
- [ ] All classification functionality works (upload, classify, view results)
- [ ] UI matches industrial/tactical aesthetic
- [ ] No TypeScript errors

---

## Task 2: AI Evaluation Tab (LLM Analytics Dashboard)

### Objective
Build a comprehensive analytics dashboard for comparing LLM performance across all classification runs, using data from the `classification_history` table.

### Requirements

#### 2.1 Create AI Evaluation Page
**File:** `frontend/src/pages/AIEvaluation.tsx`

**Structure:**
1. **Stats Overview Cards** - Aggregate metrics by provider
2. **Classification Timeline** - Recent classification runs
3. **Provider Comparison Table** - Side-by-side performance metrics
4. **Confidence Distribution Charts** - Visual comparison of confidence levels
5. **Relevance Breakdown** - Concrete relevance distribution by provider

**API Endpoints to Use:**
- `GET /api/v1/classification/stats` - Aggregate statistics
- `GET /api/v1/classification/history?limit=100` - Recent history

#### 2.2 API Client Functions
**File:** `frontend/src/api/classification.ts` (new file)

**Implementation:**
```typescript
import { apiClient } from './client';

export interface ClassificationHistoryEntry {
    id: string;
    page_id: string;
    page_number?: number;
    sheet_number?: string;
    document_id?: string;
    classification: string | null;
    classification_confidence: number | null;
    concrete_relevance: string | null;
    llm_provider: string;
    llm_model: string;
    llm_latency_ms: number | null;
    input_tokens: number | null;
    output_tokens: number | null;
    status: string;
    created_at: string;
}

export interface ProviderStats {
    provider: string;
    model: string;
    total_runs: number;
    avg_latency_ms: number | null;
    min_latency_ms: number | null;
    max_latency_ms: number | null;
    avg_confidence: number | null;
    relevance_distribution: Record<string, number>;
}

export interface ClassificationStats {
    by_provider: ProviderStats[];
    total_classifications: number;
}

export interface ClassificationHistory {
    total: number;
    history: ClassificationHistoryEntry[];
}

export const classificationApi = {
    getStats: async (): Promise<ClassificationStats> => {
        const response = await apiClient.get<ClassificationStats>('/classification/stats');
        return response.data;
    },
    
    getHistory: async (limit: number = 100): Promise<ClassificationHistory> => {
        const response = await apiClient.get<ClassificationHistory>(
            `/classification/history?limit=${limit}`
        );
        return response.data;
    },
    
    getPageHistory: async (pageId: string, limit: number = 50): Promise<ClassificationHistory> => {
        const response = await apiClient.get<ClassificationHistory>(
            `/pages/${pageId}/classification/history?limit=${limit}`
        );
        return response.data;
    },
};
```

#### 2.3 Stats Overview Cards
**Component:** Stats cards at top of page

**Implementation:**
```typescript
function StatsOverview({ stats }: { stats: ClassificationStats }) {
    const totalRuns = stats.total_classifications;
    const avgLatency = stats.by_provider.reduce((sum, p) => 
        sum + (p.avg_latency_ms || 0), 0) / stats.by_provider.length;
    const avgConfidence = stats.by_provider.reduce((sum, p) => 
        sum + (p.avg_confidence || 0), 0) / stats.by_provider.length;
    
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
                label="Total Classifications"
                value={totalRuns.toString()}
                unit="runs"
            />
            <MetricCard
                label="Avg Latency"
                value={avgLatency.toFixed(0)}
                unit="ms"
            />
            <MetricCard
                label="Avg Confidence"
                value={(avgConfidence * 100).toFixed(1)}
                unit="%"
            />
        </div>
    );
}

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
```

#### 2.4 Provider Comparison Table
**Component:** Table comparing all providers

**Implementation:**
```typescript
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

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

function ConfidenceBadge({ confidence }: { confidence: number | null }) {
    if (!confidence) return <span className="text-neutral-500">N/A</span>;
    
    const percentage = (confidence * 100).toFixed(1);
    const color = confidence >= 0.8 ? 'text-green-500' : 
                  confidence >= 0.6 ? 'text-amber-500' : 'text-red-500';
    
    return <span className={`${color} font-bold`}>{percentage}%</span>;
}
```

#### 2.5 Classification Timeline
**Component:** Recent classification runs with filtering

**Implementation:**
```typescript
import { formatDistanceToNow } from 'date-fns';

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
                        <SelectTrigger className="w-[180px] bg-neutral-800 border-neutral-700">
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
                    {filteredHistory.map((entry) => (
                        <TimelineEntry key={entry.id} entry={entry} />
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

function TimelineEntry({ entry }: { entry: ClassificationHistoryEntry }) {
    return (
        <div className="flex items-start gap-3 p-3 bg-neutral-800/50 border border-neutral-700 hover:border-neutral-600 transition-colors">
            {/* Status Indicator */}
            <div className={`w-2 h-2 rounded-full mt-2 ${
                entry.status === 'success' ? 'bg-green-500' : 'bg-red-500'
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
```

#### 2.6 Page Layout
**File:** `frontend/src/pages/AIEvaluation.tsx` (complete structure)

**Implementation:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { classificationApi } from '@/api/classification';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';

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
            <div className="container mx-auto px-4 py-6 space-y-6">
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }
    
    if (!stats || !history) {
        return (
            <div className="container mx-auto px-4 py-6">
                <Alert variant="destructive">
                    <AlertDescription>Failed to load AI evaluation data</AlertDescription>
                </Alert>
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
                <ProviderComparisonTable providers={stats.by_provider} />
                
                {/* Classification Timeline */}
                <ClassificationTimeline history={history.history} />
            </div>
        </div>
    );
}
```

#### 2.7 Update App Routing
**File:** `frontend/src/App.tsx`

**Changes:**
```typescript
import AIEvaluation from "./pages/AIEvaluation";

// Add route
<Route path="/ai-evaluation" element={<AIEvaluation />} />
```

### Acceptance Criteria
- [ ] `/ai-evaluation` route loads the analytics dashboard
- [ ] Stats cards display aggregate metrics
- [ ] Provider comparison table shows all providers with metrics
- [ ] Timeline displays recent classifications with filtering
- [ ] All data loads from backend API endpoints
- [ ] UI matches industrial/tactical aesthetic
- [ ] No TypeScript errors

---

## Task 3: DocumentDetail Enhancements

### Objective
Add classification testing controls to the DocumentDetail page, allowing users to classify pages and view confidence levels directly from the document view.

### Requirements

#### 3.1 Add Classification Controls
**File:** `frontend/src/pages/DocumentDetail.tsx`

**Changes:**
1. Add "Classify All Pages" button to document header
2. Add LLM provider selector
3. Show classification status for each page
4. Display confidence badges on page cards

**Implementation:**
```typescript
import { useMutation } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import axios from 'axios';

export default function DocumentDetail() {
    const [classificationProvider, setClassificationProvider] = useState<string | undefined>(undefined);
    
    // ... existing queries ...
    
    // Classify document mutation
    const classifyMutation = useMutation({
        mutationFn: async () => {
            if (!documentId) throw new Error('Document ID required');
            const response = await axios.post(
                `/api/v1/documents/${documentId}/classify`,
                { provider: classificationProvider }
            );
            return response.data;
        },
        onSuccess: () => {
            // Refetch pages after classification starts
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['pages', documentId] });
            }, 2000);
        },
    });
    
    return (
        <div className="container mx-auto px-4 py-6">
            {/* ... breadcrumbs ... */}
            
            {/* Document Header with Classification Controls */}
            <div className="flex items-start justify-between mb-6 mt-4">
                <div>
                    <h1 className="text-3xl font-bold mb-2">{document.original_filename}</h1>
                    {/* ... existing metadata ... */}
                </div>
                
                {/* Classification Controls */}
                <div className="flex flex-col gap-3 min-w-[250px]">
                    <div className="space-y-2">
                        <Label className="text-xs font-mono text-neutral-500 uppercase tracking-wider">
                            LLM Provider
                        </Label>
                        <Select 
                            value={classificationProvider} 
                            onValueChange={setClassificationProvider}
                        >
                            <SelectTrigger className="bg-neutral-900 border-neutral-700">
                                <SelectValue placeholder="Auto (default)" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="auto">Auto (default)</SelectItem>
                                <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                                <SelectItem value="openai">OpenAI (GPT-4)</SelectItem>
                                <SelectItem value="google">Google (Gemini)</SelectItem>
                                <SelectItem value="xai">xAI (Grok)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    
                    <Button 
                        onClick={() => classifyMutation.mutate()}
                        disabled={classifyMutation.isPending}
                        className="bg-amber-500 hover:bg-amber-400 text-black font-mono uppercase tracking-wider"
                    >
                        {classifyMutation.isPending ? 'Starting...' : 'Classify All Pages'}
                    </Button>
                    
                    {classifyMutation.isSuccess && (
                        <Alert className="bg-green-500/10 border-green-500/50">
                            <AlertDescription className="text-green-400 text-xs font-mono">
                                Classification started! Results will appear shortly.
                            </AlertDescription>
                        </Alert>
                    )}
                </div>
            </div>
            
            {/* ... rest of page ... */}
        </div>
    );
}
```

#### 3.2 Enhance PageCard with Confidence Display
**File:** `frontend/src/components/document/PageCard.tsx`

**Changes:**
```typescript
export function PageCard({ page, documentId, projectId }: PageCardProps) {
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
                    
                    {/* Classification Badge Overlay */}
                    {page.classification && (
                        <div className="absolute top-2 left-2 right-2">
                            <div className="bg-neutral-900/90 backdrop-blur-sm border border-neutral-700 px-2 py-1 rounded">
                                <div className="text-xs text-white font-mono truncate">
                                    {page.classification}
                                </div>
                                {page.classification_confidence && (
                                    <div className="flex items-center gap-1 mt-1">
                                        <div className="flex-1 h-1 bg-neutral-700 rounded-full overflow-hidden">
                                            <div 
                                                className={`h-full ${
                                                    page.classification_confidence >= 0.8 ? 'bg-green-500' :
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
                    )}
                    
                    {/* Concrete Relevance Badge */}
                    {page.concrete_relevance && (
                        <div className="absolute bottom-2 right-2">
                            <span className={`px-2 py-0.5 text-xs font-mono uppercase tracking-wider rounded ${
                                page.concrete_relevance === 'high' ? 'bg-green-500/90 text-white' :
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
                    <div className="text-sm font-mono text-white">
                        Page {page.page_number}
                    </div>
                    {page.sheet_number && (
                        <div className="text-xs text-neutral-500 font-mono">
                            {page.sheet_number}
                        </div>
                    )}
                </div>
                
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
            </CardContent>
        </Card>
    );
}
```

#### 3.3 Update Page Type Definition
**File:** `frontend/src/types/index.ts`

**Changes:**
```typescript
export interface PageSummary {
    id: string;
    document_id: string;
    page_number: number;
    width: number | null;
    height: number | null;
    classification: string | null;
    classification_confidence?: number | null; // Add this field
    concrete_relevance: string | null;
    title: string | null;
    sheet_number: string | null;
    scale_text: string | null;
    scale_calibrated: boolean;
    status: string;
    image_url: string;
    thumbnail_url: string | null;
}
```

### Acceptance Criteria
- [ ] DocumentDetail page shows "Classify All Pages" button
- [ ] LLM provider selector allows choosing classification provider
- [ ] Classification starts when button is clicked
- [ ] Page cards display classification results with confidence bars
- [ ] Concrete relevance badges show on page thumbnails
- [ ] UI matches industrial/tactical aesthetic
- [ ] No TypeScript errors

---

## Task 4: TakeoffViewer Scale Calibration Fix

### Objective
Fix the click detection for manual scale calibration in the TakeoffViewer. Currently, clicks are not being detected when the user tries to set scale by clicking two points.

### Problem Analysis
The issue is likely caused by:
1. Event handlers not properly attached to the Konva Stage
2. Z-index conflicts with overlay panels
3. Drawing mode interfering with calibration mode

### Requirements

#### 4.1 Add Scale Calibration Mode
**File:** `frontend/src/pages/TakeoffViewer.tsx`

**Changes:**

1. **Add calibration state:**
```typescript
const [calibrationMode, setCalibrationMode] = useState(false);
const [calibrationPoints, setCalibrationPoints] = useState<{ x: number; y: number }[]>([]);
const [showCalibrationDialog, setShowCalibrationDialog] = useState(false);
const [calibrationDistance, setCalibrationDistance] = useState<string>('');
const [calibrationUnit, setCalibrationUnit] = useState<'foot' | 'inch'>('foot');
```

2. **Add calibration button to toolbar:**
```typescript
<div className="absolute top-4 left-1/2 -translate-x-1/2 z-20">
    <div className="flex items-center gap-2 bg-neutral-800 border border-neutral-700 rounded-lg p-2">
        {/* Existing drawing tools */}
        <DrawingToolbar {...props} />
        
        {/* Calibration Button */}
        <div className="h-6 w-px bg-neutral-700" /> {/* Divider */}
        <Button
            variant={calibrationMode ? "default" : "ghost"}
            size="sm"
            onClick={() => {
                setCalibrationMode(!calibrationMode);
                setCalibrationPoints([]);
                setDrawingMode(null); // Disable drawing when calibrating
            }}
            className={calibrationMode ? 
                "bg-amber-500 hover:bg-amber-400 text-black" : 
                "text-white hover:bg-neutral-700"
            }
        >
            <Ruler className="h-4 w-4 mr-2" />
            {calibrationMode ? 'Cancel Calibration' : 'Set Scale'}
        </Button>
    </div>
</div>
```

3. **Update Stage click handler:**
```typescript
const handleStageClick = (e: Konva.KonvaEventObject<MouseEvent>) => {
    // Ignore clicks on shapes
    if (e.target !== e.target.getStage()) return;
    
    const stage = e.target.getStage();
    if (!stage) return;
    
    const pointerPosition = stage.getPointerPosition();
    if (!pointerPosition) return;
    
    // Handle calibration mode
    if (calibrationMode) {
        const newPoints = [...calibrationPoints, pointerPosition];
        setCalibrationPoints(newPoints);
        
        // If we have 2 points, open calibration dialog
        if (newPoints.length === 2) {
            setShowCalibrationDialog(true);
        }
        
        return; // Don't process other click handlers
    }
    
    // ... existing click handling for drawing mode ...
};
```

4. **Add calibration line rendering:**
```typescript
{/* Calibration Layer */}
<Layer>
    {calibrationPoints.length > 0 && (
        <>
            {/* First point */}
            <Circle
                x={calibrationPoints[0].x}
                y={calibrationPoints[0].y}
                radius={5}
                fill="#f59e0b"
                stroke="#ffffff"
                strokeWidth={2}
            />
            
            {/* Line between points */}
            {calibrationPoints.length === 2 && (
                <>
                    <Line
                        points={[
                            calibrationPoints[0].x,
                            calibrationPoints[0].y,
                            calibrationPoints[1].x,
                            calibrationPoints[1].y,
                        ]}
                        stroke="#f59e0b"
                        strokeWidth={3}
                        dash={[10, 5]}
                    />
                    <Circle
                        x={calibrationPoints[1].x}
                        y={calibrationPoints[1].y}
                        radius={5}
                        fill="#f59e0b"
                        stroke="#ffffff"
                        strokeWidth={2}
                    />
                </>
            )}
        </>
    )}
</Layer>
```

5. **Add calibration dialog:**
```typescript
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

{/* Calibration Dialog */}
<Dialog open={showCalibrationDialog} onOpenChange={setShowCalibrationDialog}>
    <DialogContent className="bg-neutral-900 border-neutral-700">
        <DialogHeader>
            <DialogTitle className="text-white uppercase tracking-tight font-mono">
                Set Scale
            </DialogTitle>
            <DialogDescription className="text-neutral-400 font-mono text-sm">
                Enter the real-world distance between the two points you clicked.
            </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
            <div className="space-y-2">
                <Label htmlFor="distance" className="text-neutral-400 font-mono text-xs uppercase">
                    Distance
                </Label>
                <Input
                    id="distance"
                    type="number"
                    step="0.1"
                    value={calibrationDistance}
                    onChange={(e) => setCalibrationDistance(e.target.value)}
                    placeholder="e.g., 50"
                    className="bg-neutral-800 border-neutral-700 text-white font-mono"
                />
            </div>
            
            <div className="space-y-2">
                <Label className="text-neutral-400 font-mono text-xs uppercase">
                    Unit
                </Label>
                <Select value={calibrationUnit} onValueChange={(v) => setCalibrationUnit(v as 'foot' | 'inch')}>
                    <SelectTrigger className="bg-neutral-800 border-neutral-700 text-white">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="foot">Feet</SelectItem>
                        <SelectItem value="inch">Inches</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            
            {calibrationPoints.length === 2 && (
                <div className="text-xs text-neutral-500 font-mono">
                    Pixel distance: {Math.sqrt(
                        Math.pow(calibrationPoints[1].x - calibrationPoints[0].x, 2) +
                        Math.pow(calibrationPoints[1].y - calibrationPoints[0].y, 2)
                    ).toFixed(2)} px
                </div>
            )}
        </div>
        
        <DialogFooter>
            <Button
                variant="outline"
                onClick={() => {
                    setShowCalibrationDialog(false);
                    setCalibrationPoints([]);
                    setCalibrationMode(false);
                    setCalibrationDistance('');
                }}
                className="border-neutral-700 text-white hover:bg-neutral-800"
            >
                Cancel
            </Button>
            <Button
                onClick={handleCalibrationSubmit}
                disabled={!calibrationDistance || parseFloat(calibrationDistance) <= 0}
                className="bg-amber-500 hover:bg-amber-400 text-black font-mono uppercase"
            >
                Set Scale
            </Button>
        </DialogFooter>
    </DialogContent>
</Dialog>
```

6. **Add calibration submit handler:**
```typescript
const handleCalibrationSubmit = async () => {
    if (calibrationPoints.length !== 2 || !calibrationDistance) return;
    
    const pixelDistance = Math.sqrt(
        Math.pow(calibrationPoints[1].x - calibrationPoints[0].x, 2) +
        Math.pow(calibrationPoints[1].y - calibrationPoints[0].y, 2)
    );
    
    try {
        await axios.post(`/api/v1/pages/${pageId}/calibrate`, {
            pixel_distance: pixelDistance,
            real_distance: parseFloat(calibrationDistance),
            real_unit: calibrationUnit,
        });
        
        // Refetch page data
        queryClient.invalidateQueries({ queryKey: ['page', pageId] });
        
        // Reset calibration state
        setCalibrationMode(false);
        setCalibrationPoints([]);
        setShowCalibrationDialog(false);
        setCalibrationDistance('');
        
        // Show success message
        toast({
            title: "Scale Calibrated",
            description: "Page scale has been successfully set.",
        });
    } catch (error) {
        toast({
            variant: "destructive",
            title: "Calibration Failed",
            description: "Failed to set scale. Please try again.",
        });
    }
};
```

#### 4.2 Fix Event Propagation
**File:** `frontend/src/pages/TakeoffViewer.tsx`

**Changes:**

1. **Ensure Stage has proper event handlers:**
```typescript
<Stage
    width={stageSize.width}
    height={stageSize.height}
    scaleX={zoom}
    scaleY={zoom}
    x={stagePosition.x}
    y={stagePosition.y}
    draggable={!drawingMode && !calibrationMode} // Disable drag during calibration
    onClick={handleStageClick}
    onMouseDown={handleMouseDown}
    onMouseMove={handleMouseMove}
    onMouseUp={handleMouseUp}
    onWheel={handleWheel}
    style={{ cursor: calibrationMode ? 'crosshair' : drawingMode ? 'crosshair' : 'grab' }}
>
    {/* ... layers ... */}
</Stage>
```

2. **Update overlay panels z-index:**
```typescript
{/* Left Overlay Panel - Conditions */}
<div className="absolute bottom-4 left-4 w-64 bg-gray-800 p-4 rounded-lg shadow-lg z-10 max-h-[calc(100vh-100px)] overflow-y-auto pointer-events-auto">
    {/* ... content ... */}
</div>

{/* Right Overlay Panel - Measurements */}
<div className="absolute bottom-4 right-4 w-64 bg-gray-800 p-4 rounded-lg shadow-lg z-10 max-h-[calc(100vh-100px)] overflow-y-auto pointer-events-auto">
    {/* ... content ... */}
</div>
```

3. **Add pointer-events to canvas container:**
```typescript
<div id="canvas-container" 
     className="w-full h-full flex items-center justify-center relative"
     style={{ pointerEvents: 'auto' }}>
    <Stage {...props}>
        {/* ... */}
    </Stage>
</div>
```

### Acceptance Criteria
- [ ] "Set Scale" button appears in toolbar
- [ ] Clicking "Set Scale" enables calibration mode (crosshair cursor)
- [ ] First click places a point on the canvas
- [ ] Second click places another point and draws a line
- [ ] Dialog opens asking for real-world distance
- [ ] Submitting calibration updates the page scale
- [ ] Scale warning disappears after successful calibration
- [ ] Calibration mode can be cancelled
- [ ] No TypeScript errors

---

## Task 5: Additional Improvements

### 5.1 Update Global Styles for Industrial Theme
**File:** `frontend/src/index.css`

**Changes:**
```css
/* Add industrial/tactical theme overrides */
@layer base {
  :root {
    --background: 220 13% 5%;      /* Near black */
    --foreground: 0 0% 100%;       /* White */
    --primary: 38 92% 50%;         /* Amber */
    --primary-foreground: 0 0% 0%; /* Black */
    /* ... other tokens ... */
  }
  
  body {
    @apply bg-neutral-950 text-white;
  }
}

/* Add scanline effect (optional) */
@layer utilities {
  .scanlines::after {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.05) 2px,
      rgba(0,0,0,0.05) 4px
    );
    pointer-events: none;
  }
}
```

### 5.2 Add Toast Notifications
**File:** `frontend/src/App.tsx`

**Changes:**
```typescript
import { Toaster } from "@/components/ui/toaster";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-neutral-950">
        <Header />
        <main>
          <Routes>
            {/* ... routes ... */}
          </Routes>
        </main>
        <Toaster /> {/* Add toast container */}
      </div>
    </Router>
  );
}
```

### 5.3 Add Loading States
Create a reusable loading component:

**File:** `frontend/src/components/ui/loading-spinner.tsx`

```typescript
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  size?: "sm" | "default" | "lg";
  className?: string;
  message?: string;
}

const sizes = {
  sm: "h-4 w-4",
  default: "h-6 w-6",
  lg: "h-8 w-8",
};

export function LoadingSpinner({ 
  size = "default", 
  className,
  message 
}: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <Loader2 className={cn("animate-spin text-amber-500", sizes[size], className)} />
      {message && (
        <p className="text-sm font-mono text-neutral-500 uppercase tracking-wider animate-pulse">
          {message}
        </p>
      )}
    </div>
  );
}
```

---

## Implementation Sequence

### Phase 1: Navigation & Testing Tab (2-3 hours)
1. Update Header component with navigation tabs
2. Rename Dashboard.tsx.bak to Testing.tsx
3. Apply industrial styling to Testing page
4. Update App.tsx routing
5. Test navigation and classification functionality

### Phase 2: AI Evaluation Tab (3-4 hours)
1. Create classification API client
2. Build stats overview cards
3. Build provider comparison table
4. Build classification timeline
5. Create AIEvaluation page layout
6. Update App.tsx routing
7. Test data loading and display

### Phase 3: DocumentDetail Enhancements (2-3 hours)
1. Add classification controls to DocumentDetail
2. Update PageCard with confidence display
3. Update type definitions
4. Test classification from document view

### Phase 4: TakeoffViewer Scale Fix (2-3 hours)
1. Add calibration mode state
2. Add calibration button to toolbar
3. Implement click handlers
4. Add calibration line rendering
5. Create calibration dialog
6. Fix event propagation
7. Test calibration workflow

### Phase 5: Polish & Testing (1 hour)
1. Update global styles
2. Add toast notifications
3. Add loading states
4. End-to-end testing
5. Fix any remaining issues

---

## Testing Checklist

### Navigation
- [ ] All three tabs appear in header
- [ ] Active tab is highlighted correctly
- [ ] Clicking tabs navigates to correct routes
- [ ] Back/forward browser buttons work

### Testing Tab
- [ ] Document upload works
- [ ] LLM provider selection works
- [ ] "Classify All Pages" triggers classification
- [ ] Page grid displays results
- [ ] Confidence levels are visible
- [ ] Page detail viewer works

### AI Evaluation Tab
- [ ] Stats cards display correct data
- [ ] Provider comparison table loads
- [ ] Timeline shows recent classifications
- [ ] Provider filter works
- [ ] Data refreshes when new classifications run

### DocumentDetail Enhancements
- [ ] "Classify All Pages" button works
- [ ] LLM provider selector works
- [ ] Classification starts successfully
- [ ] Page cards show confidence bars
- [ ] Concrete relevance badges display

### TakeoffViewer Scale Calibration
- [ ] "Set Scale" button enables calibration mode
- [ ] First click places point
- [ ] Second click places point and shows dialog
- [ ] Distance input accepts numbers
- [ ] Unit selector works
- [ ] Submitting calibration updates scale
- [ ] Scale warning disappears after calibration
- [ ] Cancel button resets state

### Industrial UI Theme
- [ ] Dark backgrounds throughout
- [ ] Amber accent colors
- [ ] Monospace fonts for data
- [ ] Uppercase labels with wide tracking
- [ ] Consistent border styling
- [ ] Tactical aesthetic maintained

---

## Files to Create/Modify

### New Files
- `frontend/src/pages/Testing.tsx` (rename from Dashboard.tsx.bak)
- `frontend/src/pages/AIEvaluation.tsx`
- `frontend/src/api/classification.ts`
- `frontend/src/components/ui/loading-spinner.tsx`

### Modified Files
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/pages/DocumentDetail.tsx`
- `frontend/src/components/document/PageCard.tsx`
- `frontend/src/pages/TakeoffViewer.tsx`
- `frontend/src/types/index.ts`
- `frontend/src/App.tsx`
- `frontend/src/index.css`

---

## Dependencies

All required dependencies are already installed:
- `@tanstack/react-query` - Data fetching
- `react-router-dom` - Routing
- `axios` - HTTP client
- `date-fns` - Date formatting
- `lucide-react` - Icons
- `konva` / `react-konva` - Canvas rendering
- `shadcn/ui` components - UI library

---

## Notes

1. **Industrial/Tactical Theme**: All new UI should use dark backgrounds (`bg-neutral-900`, `bg-neutral-950`), amber accents (`text-amber-500`, `bg-amber-500`), monospace fonts for data, and uppercase labels with wide tracking.

2. **API Endpoints**: All backend endpoints for classification history already exist in `backend/app/api/routes/pages.py`.

3. **Type Safety**: Ensure all API responses are properly typed with TypeScript interfaces.

4. **Error Handling**: Add proper error handling with toast notifications for all API calls.

5. **Loading States**: Use skeleton loaders or loading spinners for all async operations.

6. **Accessibility**: Maintain keyboard navigation and screen reader support throughout.

7. **Performance**: Use React Query's caching and refetching strategies to minimize API calls.

---

## Success Criteria

This implementation is complete when:
1. All three navigation tabs are functional
2. Testing tab provides full classification testing capabilities
3. AI Evaluation tab displays comprehensive LLM analytics
4. DocumentDetail page has classification controls with confidence display
5. TakeoffViewer scale calibration works via click detection
6. All UI follows industrial/tactical design aesthetic
7. No TypeScript compilation errors
8. All acceptance criteria are met
9. End-to-end testing passes

---

**Ready for Implementation** ✓
