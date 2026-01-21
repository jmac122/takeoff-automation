import { Button } from '@/components/ui/button';

interface DetectionResult {
    best_scale?: {
        text: string;
        confidence: number;
        method: string;
    };
    parsed_scales?: any[];
    scale_bars?: any[];
}

interface ScaleDetectionBannerProps {
    result: DetectionResult | null;
    onDismiss: () => void;
}

export function ScaleDetectionBanner({ result, onDismiss }: ScaleDetectionBannerProps) {
    if (!result) return null;

    return (
        <div className="px-4 py-3 bg-green-900/20 border-b border-green-700/50">
            <div className="flex items-center gap-3">
                {result.best_scale ? (
                    <>
                        <div className="text-xs font-mono text-green-400 uppercase tracking-wider font-bold">
                            ✓ Scale Updated:
                        </div>
                        <div className="text-sm font-mono text-white font-bold">
                            {result.best_scale.text}
                        </div>
                        <div className="text-xs font-mono text-neutral-400">
                            ({(result.best_scale.confidence * 100).toFixed(0)}% confidence)
                        </div>
                        {result.best_scale.method && (
                            <div className="text-xs font-mono text-neutral-500">
                                via {result.best_scale.method === 'vision_llm' ? 'AI Vision' : result.best_scale.method.replace(/_/g, ' ')}
                            </div>
                        )}
                        <div className="text-xs text-neutral-500">
                            • Ready for measurements
                        </div>
                    </>
                ) : (
                    <>
                        <div className="text-xs font-mono text-amber-500 uppercase tracking-wider">
                            Detection Result:
                        </div>
                        <div className="text-sm font-mono text-neutral-400">
                            No scale found
                            {result.parsed_scales?.length === 0 && result.scale_bars && result.scale_bars.length > 0 && (
                                <span className="ml-2 text-xs">
                                    (Found {result.scale_bars.length} graphical scale bar{result.scale_bars.length > 1 ? 's' : ''}, but unable to parse)
                                </span>
                            )}
                        </div>
                        <div className="text-xs text-neutral-500">
                            • Use "Set Scale" to calibrate manually
                        </div>
                    </>
                )}
                <div className="flex-1" />
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onDismiss}
                    className="text-neutral-500 hover:text-white h-6 w-6 p-0"
                >
                    ✕
                </Button>
            </div>
        </div>
    );
}
