import type { Measurement } from '@/types';

interface MeasurementsPanelProps {
    measurements: Measurement[];
    selectedMeasurementId: string | null;
    onSelectMeasurement: (id: string) => void;
}

export function MeasurementsPanel({
    measurements,
    selectedMeasurementId,
    onSelectMeasurement,
}: MeasurementsPanelProps) {
    if (measurements.length === 0) return null;

    return (
        <div className="absolute bottom-4 right-4 bg-neutral-900/95 backdrop-blur border border-neutral-700 rounded-lg shadow-xl p-3 max-w-xs max-h-96 overflow-y-auto z-10">
            <h2 className="text-sm font-semibold mb-2 text-white font-mono uppercase tracking-wider">
                Measurements
            </h2>
            <div className="space-y-1">
                {measurements.map((measurement) => (
                    <div
                        key={measurement.id}
                        onClick={() => onSelectMeasurement(measurement.id)}
                        className={`px-3 py-2 rounded cursor-pointer transition-colors border ${selectedMeasurementId === measurement.id
                                ? 'bg-amber-500/20 border-amber-500/50 text-amber-400'
                                : 'text-neutral-300 hover:bg-neutral-800 border-transparent'
                            }`}
                    >
                        <p className="text-xs opacity-75 font-mono uppercase">
                            {measurement.geometry_type}
                        </p>
                        <p className="text-sm font-bold font-mono">
                            {measurement.quantity.toFixed(1)} {measurement.unit}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
}
