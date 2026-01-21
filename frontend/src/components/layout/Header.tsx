/**
 * Header component with app title and navigation.
 */

import { Link, useLocation } from 'react-router-dom';

export function Header() {
    const location = useLocation();

    const isActive = (path: string) => location.pathname.startsWith(path);

    const navItems = [
        { path: '/projects', label: 'PROJECTS' },
        { path: '/testing', label: 'TESTING' },
        { path: '/ai-evaluation', label: 'AI EVALUATION' },
    ];

    return (
        <header className="border-b bg-neutral-900 sticky top-0 z-50 shadow-lg">
            <div className="container mx-auto px-4 py-3">
                <div className="flex items-center justify-between">
                    {/* Logo */}
                    <Link to="/projects" className="flex items-center gap-2">
                        <h1 className="text-xl font-bold text-amber-500 tracking-tight uppercase"
                            style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
                            ForgeX Takeoffs
                        </h1>
                    </Link>

                    {/* Navigation Tabs */}
                    <nav className="flex items-center gap-1">
                        {navItems.map(item => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`px-4 py-2 text-xs font-mono tracking-widest transition-colors ${isActive(item.path)
                                    ? 'bg-amber-500/20 text-amber-500 border-b-2 border-amber-500'
                                    : 'text-neutral-400 hover:text-white hover:bg-neutral-800'
                                    }`}
                            >
                                {item.label}
                            </Link>
                        ))}
                    </nav>
                </div>
            </div>
        </header>
    );
}
