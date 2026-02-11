/**
 * RevisionChainPanel — Shows the revision chain for a document.
 *
 * Displays a vertical timeline of document revisions with the ability
 * to select two revisions for overlay comparison.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { revisionsApi, type RevisionChainItem } from '@/api/revisions';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GitBranch, Layers } from 'lucide-react';

interface RevisionChainPanelProps {
  documentId: string;
  onCompare?: (oldDocId: string, newDocId: string) => void;
  onLinkRevision?: () => void;
}

export function RevisionChainPanel({
  documentId,
  onCompare,
  onLinkRevision,
}: RevisionChainPanelProps) {
  const [selectedForCompare, setSelectedForCompare] = useState<[string | null, string | null]>([null, null]);

  const { data: chainData, isLoading } = useQuery({
    queryKey: ['revision-chain', documentId],
    queryFn: () => revisionsApi.getRevisionChain(documentId),
    enabled: !!documentId,
  });

  const chain = chainData?.chain ?? [];

  const handleSelect = (docId: string) => {
    setSelectedForCompare((prev) => {
      if (prev[0] === null) return [docId, null];
      if (prev[0] === docId) return [null, null];
      if (prev[1] === docId) return [prev[0], null];
      return [prev[0], docId];
    });
  };

  const canCompare = selectedForCompare[0] !== null && selectedForCompare[1] !== null;

  const handleCompare = () => {
    if (canCompare && onCompare) {
      // Older doc first
      const idx0 = chain.findIndex((c) => c.id === selectedForCompare[0]);
      const idx1 = chain.findIndex((c) => c.id === selectedForCompare[1]);
      const [oldId, newId] = idx0 < idx1
        ? [selectedForCompare[0]!, selectedForCompare[1]!]
        : [selectedForCompare[1]!, selectedForCompare[0]!];
      onCompare(oldId, newId);
    }
  };

  if (isLoading) {
    return <div className="p-4 text-sm text-neutral-500">Loading revisions...</div>;
  }

  if (chain.length <= 1) {
    return (
      <div className="p-4">
        <div className="flex items-center gap-2 text-sm text-neutral-500 mb-3">
          <GitBranch size={14} />
          <span>No revisions linked</span>
        </div>
        {onLinkRevision && (
          <Button
            variant="outline"
            size="sm"
            onClick={onLinkRevision}
            className="w-full border-neutral-700 text-neutral-300"
          >
            Link Revision
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-neutral-300">
          <GitBranch size={14} />
          <span>Revisions ({chain.length})</span>
        </div>
        {onLinkRevision && (
          <Button variant="ghost" size="sm" onClick={onLinkRevision} className="text-xs text-neutral-400">
            + Link
          </Button>
        )}
      </div>

      {/* Revision timeline */}
      <div className="space-y-1">
        {chain.map((item: RevisionChainItem, idx: number) => {
          const isSelected = selectedForCompare.includes(item.id);
          const isCurrent = item.id === documentId;

          return (
            <button
              key={item.id}
              onClick={() => handleSelect(item.id)}
              className={`w-full text-left rounded px-3 py-2 text-xs transition-colors ${
                isSelected
                  ? 'bg-blue-600/20 border border-blue-500'
                  : isCurrent
                    ? 'bg-neutral-800 border border-neutral-600'
                    : 'bg-neutral-900 border border-transparent hover:bg-neutral-800'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-neutral-200 truncate">
                  {item.revision_number
                    ? `Rev ${item.revision_number}`
                    : `v${idx + 1}`}
                </span>
                <div className="flex items-center gap-1">
                  {item.is_latest_revision && (
                    <Badge className="bg-green-600/30 text-green-400 text-[10px] px-1">Latest</Badge>
                  )}
                  {isCurrent && (
                    <Badge className="bg-blue-600/30 text-blue-400 text-[10px] px-1">Current</Badge>
                  )}
                </div>
              </div>
              <div className="text-neutral-500 truncate mt-0.5">
                {item.original_filename}
              </div>
              {item.revision_label && (
                <div className="text-neutral-400 mt-0.5">{item.revision_label}</div>
              )}
            </button>
          );
        })}
      </div>

      {/* Compare button */}
      {canCompare && (
        <Button
          size="sm"
          onClick={handleCompare}
          className="w-full bg-blue-600 hover:bg-blue-500"
        >
          <Layers size={14} className="mr-1" />
          Compare Selected
        </Button>
      )}

      {selectedForCompare[0] && !selectedForCompare[1] && (
        <p className="text-xs text-neutral-500 text-center">
          Select another revision to compare
        </p>
      )}
    </div>
  );
}
