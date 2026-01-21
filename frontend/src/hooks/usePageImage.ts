import { useState, useEffect } from 'react';

export function usePageImage(imageUrl: string | null | undefined): HTMLImageElement | null {
    const [image, setImage] = useState<HTMLImageElement | null>(null);

    useEffect(() => {
        if (!imageUrl) {
            setImage(null);
            return;
        }

        const img = new window.Image();
        img.crossOrigin = 'anonymous';
        img.src = imageUrl;
        img.onload = () => setImage(img);
        img.onerror = () => {
            console.error('Failed to load image:', imageUrl);
            setImage(null);
        };

        return () => {
            // Cleanup: abort image loading if component unmounts
            img.src = '';
        };
    }, [imageUrl]);

    return image;
}
