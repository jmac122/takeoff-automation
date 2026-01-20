import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

interface Provider {
    name: string;
    display_name: string;
    model: string;
    strengths: string;
    cost_tier: string;
    available: boolean;
    is_default: boolean;
}

interface LLMProviderSelectorProps {
    value?: string;
    onChange: (provider: string | undefined) => void;
    showDefault?: boolean;
    label?: string;
}

const getCostBadgeVariant = (costTier: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (costTier) {
        case 'low':
            return 'secondary';
        case 'medium':
            return 'secondary';
        case 'medium-high':
            return 'default';
        case 'high':
            return 'destructive';
        default:
            return 'secondary';
    }
};

export function LLMProviderSelector({
    value,
    onChange,
    showDefault = true,
    label = 'AI Provider',
}: LLMProviderSelectorProps) {
    const { data, isLoading } = useQuery({
        queryKey: ['llm-providers'],
        queryFn: async () => {
            const response = await apiClient.get<{ providers: Record<string, Provider> }>(
                '/settings/llm/providers'
            );
            return response.data;
        },
    });

    const providers = data?.providers || {};
    const availableProviders = Object.values(providers).filter(p => p.available);
    const [showTooltip, setShowTooltip] = useState<string | null>(null);

    if (isLoading) {
        return (
            <div className="flex flex-col gap-2">
                {label && <Skeleton className="h-4 w-20" />}
                <Skeleton className="h-10 w-[220px]" />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-2">
            {label && <Label htmlFor="llm-provider">{label}</Label>}
            <Select
                value={value || 'default'}
                onValueChange={(val) => onChange(val === 'default' ? undefined : val)}
            >
                <SelectTrigger id="llm-provider" className="w-[220px]">
                    <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                    {showDefault && (
                        <SelectItem value="default">🤖 Default (Auto)</SelectItem>
                    )}
                    {availableProviders.map((provider) => (
                        <SelectItem
                            key={provider.name}
                            value={provider.name}
                            onMouseEnter={() => setShowTooltip(provider.name)}
                            onMouseLeave={() => setShowTooltip(null)}
                        >
                            {provider.display_name}
                            {provider.is_default && ' (Default)'}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>

            {/* Provider details tooltip */}
            {showTooltip && availableProviders.find(p => p.name === showTooltip) && (
                <div className="mt-2 p-3 bg-card border border-border rounded-lg shadow-lg">
                    {(() => {
                        const provider = availableProviders.find(p => p.name === showTooltip)!;
                        return (
                            <div className="space-y-2">
                                <p className="font-medium text-sm text-foreground">{provider.model}</p>
                                <p className="text-xs text-muted-foreground">{provider.strengths}</p>
                                <Badge variant={getCostBadgeVariant(provider.cost_tier)}>
                                    💰 {provider.cost_tier}
                                </Badge>
                            </div>
                        );
                    })()}
                </div>
            )}
        </div>
    );
}
