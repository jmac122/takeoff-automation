import { FileText } from 'lucide-react';
import type { SheetGroup, SheetInfo } from '@/api/sheets';
import { ScaleBadge } from './ScaleBadge';

interface ThumbnailStripProps {
  groups: SheetGroup[];
  activeSheetId: string | null;
  onSelectSheet: (sheetId: string) => void;
}

export function ThumbnailStrip({ groups, activeSheetId, onSelectSheet }: ThumbnailStripProps) {
  return (
    <div className="grid grid-cols-2 gap-2 p-2" data-testid="thumbnail-strip">
      {groups.flatMap((group) =>
        group.sheets.map((sheet) => (
          <ThumbnailCard
            key={sheet.id}
            sheet={sheet}
            isActive={activeSheetId === sheet.id}
            onClick={() => onSelectSheet(sheet.id)}
          />
        )),
      )}
    </div>
  );
}

function ThumbnailCard({
  sheet,
  isActive,
  onClick,
}: {
  sheet: SheetInfo;
  isActive: boolean;
  onClick: () => void;
}) {
  const displayName =
    sheet.display_name ||
    sheet.title ||
    (sheet.sheet_number ? `Sheet ${sheet.sheet_number}` : `Page ${sheet.page_number}`);

  return (
    <button
      className={`flex flex-col items-center rounded border p-1.5 text-center transition-colors ${
        isActive
          ? 'border-blue-500 bg-blue-600/10'
          : 'border-neutral-700 bg-neutral-800 hover:border-neutral-600'
      }`}
      onClick={onClick}
      title={displayName}
      data-testid={`thumbnail-${sheet.id}`}
    >
      {sheet.thumbnail_url ? (
        <img
          src={sheet.thumbnail_url}
          alt={displayName}
          className="mb-1 h-16 w-full rounded object-cover"
          loading="lazy"
        />
      ) : (
        <div className="mb-1 flex h-16 w-full items-center justify-center rounded bg-neutral-700">
          <FileText size={20} className="text-neutral-500" />
        </div>
      )}
      <span className="w-full truncate text-[10px] text-neutral-300">{displayName}</span>
      <div className="mt-0.5">
        <ScaleBadge sheet={sheet} />
      </div>
    </button>
  );
}
