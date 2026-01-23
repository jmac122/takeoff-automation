import { Layer } from 'react-konva';
import type Konva from 'konva';

import type { Condition, JsonObject, Measurement } from '@/types';
import { MeasurementShape } from './MeasurementShape';

interface MeasurementLayerProps {
    measurements: Measurement[];
    conditions: Map<string, Condition>;
    selectedMeasurementId: string | null;
    onMeasurementSelect: (id: string | null) => void;
    onConditionSelect?: (id: string | null) => void;
    onMeasurementUpdate: (
        id: string,
        geometryData: JsonObject,
        previousGeometryData?: JsonObject
    ) => void;
    onMeasurementContextMenu?: (
        measurement: Measurement,
        event: Konva.KonvaEventObject<PointerEvent | MouseEvent>
    ) => void;
    isEditing: boolean;
    scale: number; // Viewer zoom scale
}

export function MeasurementLayer({
    measurements,
    conditions,
    selectedMeasurementId,
    onMeasurementSelect,
    onConditionSelect,
    onMeasurementUpdate,
    onMeasurementContextMenu,
    isEditing,
    scale,
}: MeasurementLayerProps) {
    return (
        <Layer>
            {measurements.map((measurement) => {
                const condition = conditions.get(measurement.condition_id);
                if (!condition) return null;

                const isSelected = measurement.id === selectedMeasurementId;

                return (
                    <MeasurementShape
                        key={measurement.id}
                        measurement={measurement}
                        condition={condition}
                        isSelected={isSelected}
                        isEditing={isEditing && isSelected}
                        scale={scale}
                        onSelect={() => {
                            onMeasurementSelect(measurement.id);
                            onConditionSelect?.(measurement.condition_id);
                        }}
                        onUpdate={(geometryData, previousGeometryData) =>
                            onMeasurementUpdate(measurement.id, geometryData, previousGeometryData)
                        }
                        onContextMenu={(event) =>
                            onMeasurementContextMenu?.(measurement, event)
                        }
                    />
                );
            })}
        </Layer>
    );
}
