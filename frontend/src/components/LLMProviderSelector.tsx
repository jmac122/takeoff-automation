import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

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

const COST_COLORS = {
    low: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    'medium-high': 'bg-orange-100 text-orange-700',
    high: 'bg-red-100 text-red-700',
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
        return <div className="h-10 w-48 bg-gray-100 animate-pulse rounded-md" />;
    }

    return (
        <div className="flex flex-col gap-1">
            {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
            <div className="relative">
                <select
                    value={value || 'default'}
                    onChange={(e) => onChange(e.target.value === 'default' ? undefined : e.target.value)}
                    className="w-[220px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
                >
                    {showDefault && (
                        <option value="default">🤖 Default (Auto)</option>
                    )}
                    {availableProviders.map((provider) => (
                        <option key={provider.name} value={provider.name}>
                            {provider.display_name}
                            {provider.is_default && ' (Default)'}
                        </option>
                    ))}
                </select>
            </div>

            {/* Provider details tooltips */}
            {availableProviders.map((provider) => (
                <div
                    key={provider.name}
                    className="relative"
                    onMouseEnter={() => setShowTooltip(provider.name)}
                    onMouseLeave={() => setShowTooltip(null)}
                >
                    {showTooltip === provider.name && (
                        <div className="absolute z-50 left-0 mt-2 w-64 p-3 bg-white border border-gray-200 rounded-lg shadow-lg">
                            <div className="space-y-2">
                                <p className="font-medium text-sm">{provider.model}</p>
                                <p className="text-xs text-gray-600">{provider.strengths}</p>
                                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${COST_COLORS[provider.cost_tier as keyof typeof COST_COLORS] || COST_COLORS.medium}`}>
                                    💰 {provider.cost_tier}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
