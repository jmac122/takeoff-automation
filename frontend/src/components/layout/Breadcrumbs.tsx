/**
 * Breadcrumbs component for navigation hierarchy.
 */

import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

export interface BreadcrumbItem {
    label: string;
    href: string;
}

interface BreadcrumbsProps {
    items: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
    return (
        <nav className="flex items-center gap-2 text-sm text-gray-600">
            {items.map((item, index) => (
                <div key={item.href} className="flex items-center gap-2">
                    {index > 0 && <ChevronRight className="w-4 h-4" />}
                    {index === items.length - 1 ? (
                        <span className="font-medium text-gray-900">{item.label}</span>
                    ) : (
                        <Link to={item.href} className="hover:text-primary transition-colors">
                            {item.label}
                        </Link>
                    )}
                </div>
            ))}
        </nav>
    );
}
