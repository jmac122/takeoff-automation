/**
 * ExportDropdown — format selector with export options.
 *
 * Renders a dropdown button in the toolbar. Selecting a format
 * triggers an export job with the configured options.
 */

import { useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu';
import { Download, Loader2, FileSpreadsheet, FileText, FileCode, FileType } from 'lucide-react';
import { useExport } from '@/hooks/useExport';
import type { ExportFormat, ExportOptions } from '@/api/exports';

interface ExportDropdownProps {
  projectId: string;
}

const FORMAT_OPTIONS: { format: ExportFormat; label: string; icon: React.ReactNode; desc: string }[] = [
  { format: 'excel', label: 'Excel (.xlsx)', icon: <FileSpreadsheet size={14} />, desc: 'Full workbook with cost summary' },
  { format: 'pdf', label: 'PDF Report', icon: <FileText size={14} />, desc: 'Printable project report' },
  { format: 'csv', label: 'CSV', icon: <FileType size={14} />, desc: 'Flat data for import' },
  { format: 'ost', label: 'OST XML', icon: <FileCode size={14} />, desc: 'On Screen Takeoff format' },
];

export function ExportDropdown({ projectId }: ExportDropdownProps) {
  const [includeUnverified, setIncludeUnverified] = useState(true);
  const [includeCosts, setIncludeCosts] = useState(true);

  const { startExport, isExporting, progress } = useExport({
    projectId,
    onError: (err) => console.error('Export error:', err),
  });

  const handleExport = (format: ExportFormat) => {
    const options: ExportOptions = {
      include_unverified: includeUnverified,
      include_costs: includeCosts,
    };
    startExport(format, options);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="flex items-center gap-1 rounded px-2 py-1.5 text-xs text-neutral-400 hover:bg-neutral-800 hover:text-white disabled:opacity-50"
          disabled={isExporting}
          title="Export project data"
        >
          {isExporting ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Download size={16} />
          )}
          <span className="hidden lg:inline">
            {isExporting
              ? `${Math.round(progress.percent)}%`
              : 'Export'}
          </span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 bg-neutral-900 border-neutral-700">
        <DropdownMenuLabel className="text-neutral-300">Export Format</DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-neutral-700" />

        {FORMAT_OPTIONS.map(({ format, label, icon, desc }) => (
          <DropdownMenuItem
            key={format}
            onClick={() => handleExport(format)}
            className="flex items-center gap-2 text-neutral-200 focus:bg-neutral-800 focus:text-white cursor-pointer"
          >
            {icon}
            <div>
              <div className="text-sm">{label}</div>
              <div className="text-xs text-neutral-500">{desc}</div>
            </div>
          </DropdownMenuItem>
        ))}

        <DropdownMenuSeparator className="bg-neutral-700" />
        <DropdownMenuLabel className="text-neutral-300">Options</DropdownMenuLabel>

        <DropdownMenuCheckboxItem
          checked={includeUnverified}
          onCheckedChange={(v) => setIncludeUnverified(!!v)}
          onSelect={(e) => e.preventDefault()}
          className="text-neutral-300 focus:bg-neutral-800 focus:text-white"
        >
          Include unverified measurements
        </DropdownMenuCheckboxItem>

        <DropdownMenuCheckboxItem
          checked={includeCosts}
          onCheckedChange={(v) => setIncludeCosts(!!v)}
          onSelect={(e) => e.preventDefault()}
          className="text-neutral-300 focus:bg-neutral-800 focus:text-white"
        >
          Include cost data
        </DropdownMenuCheckboxItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
