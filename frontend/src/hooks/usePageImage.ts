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
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/c2908297-06df-40fb-a71a-4f158024ffa0',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run4',hypothesisId:'H1',location:'usePageImage.ts:22',message:'no image url',data:{imageUrl},timestamp:Date.now()})}).catch(()=>{});
            // #endregion
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
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/c2908297-06df-40fb-a71a-4f158024ffa0',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run4',hypothesisId:'H2',location:'usePageImage.ts:44',message:'image loaded',data:{baseUrl,imageUrl,width:img.width,height:img.height,complete:img.complete},timestamp:Date.now()})}).catch(()=>{});
            // #endregion
            loadingRef.current = false;
            if (img.width === 0 || img.height === 0) {
                setImage(null);
                return;
            }
            setImage(img);
        };
        img.onerror = () => {
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/c2908297-06df-40fb-a71a-4f158024ffa0',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run4',hypothesisId:'H3',location:'usePageImage.ts:48',message:'image load error',data:{baseUrl,imageUrl},timestamp:Date.now()})}).catch(()=>{});
            // #endregion
            loadingRef.current = false;
            console.debug('Failed to load image:', imageUrl);
            // Don't clear existing image on error - keep showing the old one
        };

        // No cleanup that clears img.src - this was causing the black screen
        // The browser will handle garbage collection
    }, [imageUrl, baseUrl, image]);

    return image;
}
