import { Check } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface HealthStatusBadgeProps {
    status: string;
}

export function HealthStatusBadge({ status }: HealthStatusBadgeProps) {
    return (
        <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
            <Check className="w-4 h-4 mr-2" />
            API Status: {status}
        </Badge>
    );
}
