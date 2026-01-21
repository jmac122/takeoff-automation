/**
 * Utility to parse construction scale notations and calculate pixels per foot.
 * Assumes 150 DPI for plan images (standard for scanned construction drawings).
 */

const DEFAULT_DPI = 150;

/**
 * Parse scale text like "3/32" = 1'-0"" or "1/4" = 1'-0"" into pixels per foot.
 * 
 * Supported formats:
 * - "3/32" = 1'-0""
 * - "1/4" = 1'-0""
 * - "1" = 10'-0"" (engineering scale)
 * - "1:48" (ratio format)
 */
export function parseScaleText(scaleText: string): { pixelsPerFoot: number; scaleRatio: number } | null {
    if (!scaleText || !scaleText.trim()) {
        return null;
    }

    const text = scaleText.trim();

    // Try fractional architectural scale: "3/32" = 1'-0""
    const fractionalArchMatch = text.match(/^(\d+)\/(\d+)\s*["']?\s*=\s*1['-]0["']?$/i);
    if (fractionalArchMatch) {
        const numerator = parseInt(fractionalArchMatch[1]);
        const denominator = parseInt(fractionalArchMatch[2]);

        if (denominator === 0) return null;

        // Scale ratio: if n/d inch = 1 foot, ratio = 12 * d / n
        // Example: 3/32" = 1'-0" means 3/32 inch on drawing = 1 foot real
        // Ratio = 12 inches / (3/32 inches) = 12 * 32 / 3 = 128
        const scaleRatio = (12 * denominator) / numerator;
        const pixelsPerFoot = DEFAULT_DPI / scaleRatio;

        return { pixelsPerFoot, scaleRatio };
    }

    // Try simple fractional: "1/4" = 1'-0"" (without quotes)
    const simpleFractionalMatch = text.match(/^(\d+)\/(\d+)\s*=\s*1['-]0/i);
    if (simpleFractionalMatch) {
        const numerator = parseInt(simpleFractionalMatch[1]);
        const denominator = parseInt(simpleFractionalMatch[2]);

        if (denominator === 0) return null;

        const scaleRatio = (12 * denominator) / numerator;
        const pixelsPerFoot = DEFAULT_DPI / scaleRatio;

        return { pixelsPerFoot, scaleRatio };
    }

    // Try engineering scale: "1" = 10'-0"" or "1" = 20'-0""
    const engineeringMatch = text.match(/^(\d+)\s*["']?\s*=\s*(\d+)['-]0["']?$/i);
    if (engineeringMatch) {
        const drawingInches = parseInt(engineeringMatch[1]);
        const realFeet = parseInt(engineeringMatch[2]);

        if (drawingInches === 0 || realFeet === 0) return null;

        // If 1" = 10', then 1 foot real = 1/10 inch on drawing
        // Ratio = 12 inches / (1/10 inches) = 120
        const scaleRatio = (12 * realFeet) / drawingInches;
        const pixelsPerFoot = DEFAULT_DPI / scaleRatio;

        return { pixelsPerFoot, scaleRatio };
    }

    // Try ratio format: "1:48" or "1:100"
    const ratioMatch = text.match(/^(\d+):(\d+)$/);
    if (ratioMatch) {
        const realRatio = parseInt(ratioMatch[2]);

        if (realRatio === 0) return null;

        // For architectural scales, ratio is typically drawing:real in inches
        // If 1:48, that means 1 inch drawing = 48 inches real = 4 feet real
        // So 1 foot real = 1/4 inch drawing = 0.25 inches
        // At 150 DPI: 0.25 * 150 = 37.5 pixels per foot
        // Ratio = 48, so pixels_per_foot = 150 / 48 = 3.125

        // For ratio format, assume it's inches:inches, so convert to feet
        // If 1:48, that's 1 inch = 48 inches = 4 feet
        // So scale ratio = 48 / 12 = 4 (but we need the inverse for pixels_per_foot)
        // Actually: 1 inch drawing = 48 inches real = 4 feet real
        // So 1 foot real = 1/4 inch drawing
        // Scale ratio = 48 (inches to inches) = 4 (feet to inches) = 12*4 = 48
        // pixels_per_foot = DPI / (ratio/12) = 150 / (48/12) = 150 / 4 = 37.5
        const scaleRatio = realRatio / 12; // Convert inches to feet ratio
        const pixelsPerFoot = DEFAULT_DPI / scaleRatio;

        return { pixelsPerFoot, scaleRatio };
    }

    // Try whole number architectural: "1/4" (assumes = 1'-0")
    const wholeNumberMatch = text.match(/^(\d+)\/(\d+)$/);
    if (wholeNumberMatch) {
        const numerator = parseInt(wholeNumberMatch[1]);
        const denominator = parseInt(wholeNumberMatch[2]);

        if (denominator === 0) return null;

        const scaleRatio = (12 * denominator) / numerator;
        const pixelsPerFoot = DEFAULT_DPI / scaleRatio;

        return { pixelsPerFoot, scaleRatio };
    }

    return null;
}

/**
 * Validate scale text format and return error message if invalid.
 */
export function validateScaleText(scaleText: string): string | null {
    if (!scaleText || !scaleText.trim()) {
        return 'Scale text is required';
    }

    const parsed = parseScaleText(scaleText);
    if (!parsed) {
        return 'Invalid scale format. Examples: "3/32" = 1\'-0"", "1/4" = 1\'-0"", "1" = 10\'-0""';
    }

    return null;
}
