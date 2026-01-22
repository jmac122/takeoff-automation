import { useState, useCallback } from 'react';
import { apiClient } from '@/api/client';

export interface CalibrationPoint {
    x: number;
    y: number;
}

export interface CalibrationLine {
    start: CalibrationPoint;
    end: CalibrationPoint;
}

export interface CalibrationState {
    isCalibrating: boolean;
    calibrationLine: CalibrationLine | null;
    pixelDistance: number | null;
    isDrawing: boolean;
    startPoint: CalibrationPoint | null;
}

export interface UseScaleCalibrationReturn {
    state: CalibrationState;
    startCalibration: () => void;
    cancelCalibration: () => void;
    startDrawing: (point: CalibrationPoint) => void;
    updateDrawing: (point: CalibrationPoint) => void;
    finishDrawing: (point: CalibrationPoint) => void;
    clearLine: () => void;
    submitCalibration: (pageId: string, realDistance: number, unit: string) => Promise<void>;
}

export function useScaleCalibration(): UseScaleCalibrationReturn {
    const [state, setState] = useState<CalibrationState>({
        isCalibrating: false,
        calibrationLine: null,
        pixelDistance: null,
        isDrawing: false,
        startPoint: null,
    });

    const startCalibration = useCallback(() => {
        setState({
            isCalibrating: true,
            calibrationLine: null,
            pixelDistance: null,
            isDrawing: false,
            startPoint: null,
        });
    }, []);

    const cancelCalibration = useCallback(() => {
        setState({
            isCalibrating: false,
            calibrationLine: null,
            pixelDistance: null,
            isDrawing: false,
            startPoint: null,
        });
    }, []);

    const startDrawing = useCallback((point: CalibrationPoint) => {
        setState(prev => ({
            ...prev,
            isDrawing: true,
            startPoint: point,
            calibrationLine: null,
            pixelDistance: null,
        }));
    }, []);

    const updateDrawing = useCallback((point: CalibrationPoint) => {
        setState(prev => {
            if (!prev.isDrawing || !prev.startPoint) return prev;

            const line: CalibrationLine = {
                start: prev.startPoint,
                end: point,
            };

            const dx = line.end.x - line.start.x;
            const dy = line.end.y - line.start.y;
            const pixelDistance = Math.sqrt(dx * dx + dy * dy);

            return {
                ...prev,
                calibrationLine: line,
                pixelDistance,
            };
        });
    }, []);

    const finishDrawing = useCallback((point: CalibrationPoint) => {
        setState(prev => {
            if (!prev.isDrawing || !prev.startPoint) return prev;

            const line: CalibrationLine = {
                start: prev.startPoint,
                end: point,
            };

            const dx = line.end.x - line.start.x;
            const dy = line.end.y - line.start.y;
            const pixelDistance = Math.sqrt(dx * dx + dy * dy);

            return {
                ...prev,
                isDrawing: false,
                calibrationLine: line,
                pixelDistance,
            };
        });
    }, []);

    const clearLine = useCallback(() => {
        setState(prev => ({
            ...prev,
            calibrationLine: null,
            pixelDistance: null,
            isDrawing: false,
            startPoint: null,
        }));
    }, []);

    const submitCalibration = useCallback(async (
        pageId: string,
        realDistance: number,
        unit: string = 'foot',
        pixelDistanceOverride?: number
    ) => {
        // Calculate pixel distance from line if not provided
        let pixelDist = pixelDistanceOverride;
        if (!pixelDist && state.calibrationLine) {
            const dx = state.calibrationLine.end.x - state.calibrationLine.start.x;
            const dy = state.calibrationLine.end.y - state.calibrationLine.start.y;
            pixelDist = Math.sqrt(dx * dx + dy * dy);
        }
        if (!pixelDist) {
            pixelDist = state.pixelDistance ?? 0;
        }

        if (!pixelDist || pixelDist <= 0) {
            throw new Error('No calibration line drawn');
        }

        if (realDistance <= 0) {
            throw new Error('Real distance must be positive');
        }

        await apiClient.post(`/pages/${pageId}/calibrate`, null, {
            params: {
                pixel_distance: pixelDist,
                real_distance: realDistance,
                real_unit: unit,
            },
        });

        // Reset state after successful calibration
        setState({
            isCalibrating: false,
            calibrationLine: null,
            pixelDistance: null,
            isDrawing: false,
            startPoint: null,
        });
    }, [state.calibrationLine, state.pixelDistance]);

    return {
        state,
        startCalibration,
        cancelCalibration,
        startDrawing,
        updateDrawing,
        finishDrawing,
        clearLine,
        submitCalibration,
    };
}
