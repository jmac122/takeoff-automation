import type { Condition } from '@/types';

interface ConditionsPanelProps {
    conditions: Condition[];
    selectedConditionId: string | null;
    onSelectCondition: (id: string) => void;
}

export function ConditionsPanel({
    conditions,
    selectedConditionId,
    onSelectCondition,
}: ConditionsPanelProps) {
    if (conditions.length === 0) return null;

    return (
        <div className="absolute bottom-4 left-4 bg-neutral-900/95 backdrop-blur border border-neutral-700 rounded-lg shadow-xl p-3 max-w-xs max-h-96 overflow-y-auto z-10">
            <h2 className="text-sm font-semibold mb-2 text-white font-mono uppercase tracking-wider">
                Conditions
            </h2>
            <div className="space-y-1">
                {conditions.map((condition) => (
                    <button
                        key={condition.id}
                        onClick={() => onSelectCondition(condition.id)}
                        className={`w-full text-left px-3 py-2 rounded transition-colors border ${selectedConditionId === condition.id
                                ? 'bg-amber-500/20 border-amber-500/50 text-amber-400'
                                : 'text-neutral-300 hover:bg-neutral-800 border-transparent'
                            }`}
                    >
                        <div className="flex items-center gap-2">
                            <div
                                className="w-3 h-3 rounded flex-shrink-0 border border-neutral-600"
                                style={{ backgroundColor: condition.color }}
                            />
                            <div className="flex-1 min-w-0">
                                <p className="text-sm truncate font-mono">{condition.name}</p>
                                <p className="text-xs opacity-75 font-mono">
                                    {condition.total_quantity.toFixed(1)} {condition.unit}
                                </p>
                            </div>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
}
