import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import { Pencil } from "lucide-react";

interface PageInfoCardProps {
    page: {
        id: string;
        document_id: string;
        page_number: number;
        sheet_number: string | null;
        classification: string | null;
        concrete_relevance?: string | null;
        thumbnail_url: string | null;
        image_url: string | null;
    };
    projectId: string;
    isSelected: boolean;
    onSelect: () => void;
}

function getConcreteVariant(relevance: string | null | undefined): "default" | "secondary" | "destructive" | "outline" {
    switch (relevance) {
        case "high": return "destructive";
        case "medium": return "secondary";
        case "low": return "secondary";
        default: return "outline";
    }
}

export function PageInfoCard({ page, projectId, isSelected, onSelect }: PageInfoCardProps) {
    const navigate = useNavigate();

    const handleOpenTakeoff = (e: React.MouseEvent) => {
        e.stopPropagation();
        navigate(`/projects/${projectId}/workspace`);
    };

    return (
        <div
            onClick={onSelect}
            className={cn(
                "border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md",
                isSelected ? "ring-2 ring-primary border-primary" : "border-border"
            )}
        >
            {/* Thumbnail */}
            <div className="aspect-[8.5/11] bg-muted rounded mb-2 overflow-hidden relative group">
                {page.thumbnail_url ? (
                    <a
                        href={page.image_url || page.thumbnail_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="block w-full h-full"
                        title="Click to open full resolution image"
                    >
                        <img
                            src={page.thumbnail_url}
                            alt={`Page ${page.page_number}`}
                            className="w-full h-full object-contain"
                        />
                    </a>
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                        No thumbnail
                    </div>
                )}
            </div>

            {/* Page Info */}
            <div className="text-xs space-y-2">
                <div>
                    <p className="font-medium text-foreground">
                        Page {page.page_number}
                        {page.sheet_number && (
                            <span className="text-muted-foreground ml-1">({page.sheet_number})</span>
                        )}
                    </p>
                    {page.classification && (
                        <p className="text-primary truncate">{page.classification}</p>
                    )}
                    {page.concrete_relevance && (
                        <Badge variant={getConcreteVariant(page.concrete_relevance)} className="mt-1">
                            Concrete: {page.concrete_relevance}
                        </Badge>
                    )}
                </div>

                {/* Takeoff Button */}
                <Button
                    size="sm"
                    variant="outline"
                    className="w-full text-xs"
                    onClick={handleOpenTakeoff}
                >
                    <Pencil className="w-3 h-3 mr-1" />
                    Open Takeoff
                </Button>
            </div>
        </div>
    );
}
