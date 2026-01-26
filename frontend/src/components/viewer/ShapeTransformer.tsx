import { useEffect, useRef } from 'react';
import { Transformer } from 'react-konva';
import type Konva from 'konva';

interface ShapeTransformerProps {
    node: Konva.Node | null;
    enabled: boolean;
    scale: number;
}

export function ShapeTransformer({ node, enabled, scale }: ShapeTransformerProps) {
    const transformerRef = useRef<Konva.Transformer>(null);

    useEffect(() => {
        if (!enabled || !node || !transformerRef.current) return;
        transformerRef.current.nodes([node]);
        transformerRef.current.getLayer()?.batchDraw();
    }, [enabled, node]);

    if (!enabled) return null;

    return (
        <Transformer
            ref={transformerRef}
            rotateEnabled={false}
            keepRatio={false}
            anchorSize={10 / scale}
            borderDash={[6 / scale, 4 / scale]}
            boundBoxFunc={(oldBox, newBox) => {
                const minSize = 4;
                if (Math.abs(newBox.width) < minSize || Math.abs(newBox.height) < minSize) {
                    return oldBox;
                }
                return newBox;
            }}
        />
    );
}
