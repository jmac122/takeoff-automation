import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { scaleApi } from '@/api/scale';
import { useNotificationContext } from '@/contexts/NotificationContext';
import type { Page } from '@/types';

interface ScaleHighlightBox {
    x: number;
    y: number;
    width: number;
    height: number;
}

interface DetectionResult {
    best_scale?: {
        text: string;
        confidence: number;
        method: string;
        bbox?: { x: number; y: number; width: number; height: number };
    };
    parsed_scales?: unknown[];
    scale_bars?: unknown[];
}

interface OCRBlock {
    text: string;
    bounding_box?: {
        x: number;
        y: number;
        width: number;
        height: number;
    };
}

// Type assertion helper for pages with OCR blocks
type PageWithOCR = Page & {
    ocr_blocks?: {
        blocks: Array<{
            text: string;
            bounding_box?: {
                x: number;
                y: number;
                width: number;
                height: number;
            };
        }>;
    };
};

export function useScaleDetection(pageId: string | undefined, page: Page | undefined) {
    const queryClient = useQueryClient();
    const { addNotification } = useNotificationContext();
    const [isDetecting, setIsDetecting] = useState(false);
    const [detectionResult, setDetectionResult] = useState<DetectionResult | null>(null);
    const [scaleHighlightBox, setScaleHighlightBox] = useState<ScaleHighlightBox | null>(null);

    const pollForScaleUpdate = useCallback(async () => {
        if (!pageId) return;

        const maxAttempts = 10;
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            await new Promise(resolve => setTimeout(resolve, 500));
            const response = await apiClient.get<Page>(`/pages/${pageId}`);
            const updatedPage = response.data;

            queryClient.setQueryData(['page', pageId], updatedPage);

            if (updatedPage.scale_calibration_data?.best_scale) {
                return;
            }
        }
    }, [pageId, queryClient]);

    const detectScale = useCallback(async () => {
        if (!pageId) return;

        setIsDetecting(true);
        setDetectionResult(null);
        setScaleHighlightBox(null);

        try {
            await scaleApi.detectScale(pageId);

            let attempts = 0;
            const maxAttempts = 10;

            while (attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 500));

                const status = await scaleApi.getDetectionStatus(pageId);

                if (status.status === 'complete') {
                    setIsDetecting(false);
                    setDetectionResult(status.detection);

                    // Show success notification
                    if (status.scale_text) {
                        addNotification(
                            'success',
                            'Scale Detected',
                            `Found scale: ${status.scale_text}. Click "SET SCALE" to review or adjust.`
                        );
                    }

                    // Keep the detection result and highlight visible until user dismisses or refreshes

                    // Find bounding box for highlight
                    if (status.detection?.best_scale) {
                        const detectionMethod = status.detection.best_scale.method;

                        if (detectionMethod === 'vision_llm' && status.detection.best_scale.bbox) {
                            const bbox = status.detection.best_scale.bbox;
                            setScaleHighlightBox({
                                x: bbox.x,
                                y: bbox.y,
                                width: bbox.width,
                                height: bbox.height,
                            });
                        } else if (detectionMethod !== 'vision_llm' && (page as PageWithOCR)?.ocr_blocks?.blocks) {
                            const scaleText = status.detection.best_scale.text;
                            const normalizeText = (text: string) => text.replace(/\s+/g, ' ').trim().toLowerCase();
                            const normalizedScaleText = normalizeText(scaleText);

                            const matchingBlock = (page as PageWithOCR).ocr_blocks!.blocks.find(
                                (block: OCRBlock) => {
                                    if (!block.text) return false;
                                    const normalizedBlockText = normalizeText(block.text);
                                    return normalizedBlockText.includes(normalizedScaleText) ||
                                        normalizedScaleText.includes(normalizedBlockText);
                                }
                            );

                            if (matchingBlock?.bounding_box) {
                                setScaleHighlightBox({
                                    x: matchingBlock.bounding_box.x,
                                    y: matchingBlock.bounding_box.y,
                                    width: matchingBlock.bounding_box.width,
                                    height: matchingBlock.bounding_box.height,
                                });
                            }
                        }
                    }

                    queryClient.invalidateQueries({ queryKey: ['page', pageId] });
                    queryClient.refetchQueries({ queryKey: ['page', pageId] });
                    await pollForScaleUpdate();
                    return;
                }

                attempts++;
            }

            setIsDetecting(false);
            addNotification('error', 'Scale Detection Timeout', 'Scale detection timed out. Please try again.');
        } catch (error) {
            console.error('Scale detection failed:', error);
            setIsDetecting(false);
            addNotification('error', 'Scale Detection Failed', 'Scale detection failed. Please try again.');
        }
    }, [addNotification, pageId, page, pollForScaleUpdate, queryClient]);

    const dismissResult = useCallback(() => {
        setDetectionResult(null);
        setScaleHighlightBox(null);
    }, []);

    return {
        isDetecting,
        detectionResult,
        scaleHighlightBox,
        detectScale,
        dismissResult,
    };
}
