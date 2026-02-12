import { useState, useEffect, useRef, useMemo } from 'react';

export function usePageImage(imageUrl: string | null | undefined): HTMLImageElement | null {
    const [image, setImage] = useState<HTMLImageElement | null>(null);
    const loadingRef = useRef<boolean>(false);
    const currentUrlRef = useRef<string | null>(null);
    
    // Extract the base URL without query parameters to detect actual URL changes
    // Presigned URLs change timestamps on every API call, but the base path stays the same
    const baseUrl = useMemo(() => {
        if (!imageUrl) return null;
        try {
            const url = new URL(imageUrl);
            return url.origin + url.pathname;
        } catch {
            return imageUrl;
        }
    }, [imageUrl]);

    useEffect(() => {
        if (!imageUrl) {
            setImage(null);
            currentUrlRef.current = null;
            return;
        }

        // If we already have an image loaded for this base URL, don't reload
        if (image && currentUrlRef.current === baseUrl) {
            return;
        }

        // Prevent multiple concurrent loads
        if (loadingRef.current && currentUrlRef.current === baseUrl) {
            return;
        }

        loadingRef.current = true;
        currentUrlRef.current = baseUrl;

        const img = new window.Image();
        img.crossOrigin = 'anonymous';
        img.src = imageUrl;
        img.onload = () => {
            loadingRef.current = false;
            if (img.width === 0 || img.height === 0) {
                setImage(null);
                return;
            }
            setImage(img);
        };
        img.onerror = () => {
            loadingRef.current = false;
            console.debug('Failed to load image:', imageUrl);
            // Don't clear existing image on error - keep showing the old one
        };

        // No cleanup that clears img.src - this was causing the black screen
        // The browser will handle garbage collection
    }, [imageUrl, baseUrl, image]);

    return image;
}
