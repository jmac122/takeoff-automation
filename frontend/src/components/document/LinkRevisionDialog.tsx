/**
 * LinkRevisionDialog — Modal for linking a document as a revision of another.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/api/client';
import { revisionsApi } from '@/api/revisions';
import type { Document } from '@/types';

interface LinkRevisionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  documentId: string;
  projectId: string;
}

export function LinkRevisionDialog({
  open,
  onOpenChange,
  documentId,
  projectId,
}: LinkRevisionDialogProps) {
  const queryClient = useQueryClient();
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [revisionNumber, setRevisionNumber] = useState('');
  const [revisionLabel, setRevisionLabel] = useState('');

  // Fetch other documents in the project
  const { data: docsData } = useQuery({
    queryKey: ['project-documents', projectId],
    queryFn: async () => {
      const response = await apiClient.get<{ documents: Document[] }>(
        `/projects/${projectId}/documents`,
      );
      return response.data.documents;
    },
    enabled: open && !!projectId,
  });

  const otherDocs = (docsData ?? []).filter((d) => d.id !== documentId);

  const linkMutation = useMutation({
    mutationFn: () =>
      revisionsApi.linkRevision(documentId, {
        supersedes_document_id: selectedDocId,
        revision_number: revisionNumber || null,
        revision_label: revisionLabel || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['revision-chain', documentId] });
      queryClient.invalidateQueries({ queryKey: ['document', documentId] });
      queryClient.invalidateQueries({ queryKey: ['project-documents', projectId] });
      onOpenChange(false);
      setSelectedDocId('');
      setRevisionNumber('');
      setRevisionLabel('');
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-neutral-900 border-neutral-700 text-neutral-200">
        <DialogHeader>
          <DialogTitle>Link as Revision</DialogTitle>
          <DialogDescription className="text-neutral-400">
            Mark this document as a newer revision of an existing document.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div>
            <Label className="text-neutral-300">Supersedes Document</Label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="mt-1 w-full rounded bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm text-neutral-200"
            >
              <option value="">Select a document...</option>
              {otherDocs.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.original_filename}
                  {doc.revision_number ? ` (Rev ${doc.revision_number})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <Label className="text-neutral-300">Revision Number</Label>
            <Input
              value={revisionNumber}
              onChange={(e) => setRevisionNumber(e.target.value)}
              placeholder="e.g., A, B1, Rev2"
              className="mt-1 bg-neutral-800 border-neutral-700 text-neutral-200"
            />
          </div>

          <div>
            <Label className="text-neutral-300">Revision Label</Label>
            <Input
              value={revisionLabel}
              onChange={(e) => setRevisionLabel(e.target.value)}
              placeholder="e.g., Issued for Permit"
              className="mt-1 bg-neutral-800 border-neutral-700 text-neutral-200"
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-neutral-700 text-neutral-300"
          >
            Cancel
          </Button>
          <Button
            onClick={() => linkMutation.mutate()}
            disabled={!selectedDocId || linkMutation.isPending}
            className="bg-blue-600 hover:bg-blue-500"
          >
            {linkMutation.isPending ? 'Linking...' : 'Link Revision'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
