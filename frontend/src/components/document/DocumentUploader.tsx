/**
 * Document uploader component with drag-and-drop support.
 */

import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, Check, X, Loader2 } from "lucide-react";
import { uploadDocument, pollDocumentStatus, DocumentStatus } from "../../api/documents";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface UploadingFile {
  file: File;
  progress: number;
  status: "uploading" | "processing" | "ready" | "error";
  documentId?: string;
  error?: string;
}

interface DocumentUploaderProps {
  projectId: string;
  onUploadComplete?: (documentId: string) => void;
}

export default function DocumentUploader({
  projectId,
  onUploadComplete,
}: DocumentUploaderProps) {
  const [uploadingFiles, setUploadingFiles] = useState<Map<string, UploadingFile>>(
    new Map()
  );
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async ({
      file,
      fileKey,
    }: {
      file: File;
      fileKey: string;
    }) => {
      // Upload the file
      const document = await uploadDocument(projectId, file, (progress) => {
        setUploadingFiles((prev) => {
          const updated = new Map(prev);
          const fileData = updated.get(fileKey);
          if (fileData) {
            fileData.progress = progress;
          }
          return updated;
        });
      });

      // Update with document ID and change status to processing
      setUploadingFiles((prev) => {
        const updated = new Map(prev);
        const fileData = updated.get(fileKey);
        if (fileData) {
          fileData.documentId = document.id;
          fileData.status = "processing";
        }
        return updated;
      });

      // Poll for completion
      await pollDocumentStatus(
        document.id,
        (status: DocumentStatus) => {
          setUploadingFiles((prev) => {
            const updated = new Map(prev);
            const fileData = updated.get(fileKey);
            if (fileData) {
              if (status.status === "ready") {
                fileData.status = "ready";
              } else if (status.status === "error") {
                fileData.status = "error";
                fileData.error = status.error || "Processing failed";
              }
            }
            return updated;
          });
        }
      );

      return document;
    },
    onSuccess: (document, { fileKey }) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "documents"] });
      if (onUploadComplete) {
        onUploadComplete(document.id);
      }

      // Remove from uploading list after 2 seconds
      setTimeout(() => {
        setUploadingFiles((prev) => {
          const updated = new Map(prev);
          updated.delete(fileKey);
          return updated;
        });
      }, 2000);
    },
    onError: (error: Error, { fileKey }) => {
      setUploadingFiles((prev) => {
        const updated = new Map(prev);
        const fileData = updated.get(fileKey);
        if (fileData) {
          fileData.status = "error";
          fileData.error = error.message;
        }
        return updated;
      });
    },
  });

  const onDrop = (acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const fileKey = `${file.name}-${Date.now()}`;

      // Add to uploading list
      setUploadingFiles((prev) => {
        const updated = new Map(prev);
        updated.set(fileKey, {
          file,
          progress: 0,
          status: "uploading",
        });
        return updated;
      });

      // Start upload
      uploadMutation.mutate({ file, fileKey });
    });
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/tiff": [".tiff", ".tif"],
    },
    multiple: true,
  });

  return (
    <div className="w-full">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50 bg-background"
        )}
      >
        <input {...getInputProps()} />
        <div className="space-y-2">
          <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
          {isDragActive ? (
            <p className="text-lg text-primary">Drop files here...</p>
          ) : (
            <>
              <p className="text-lg text-foreground">
                Drag and drop PDF or TIFF files here
              </p>
              <p className="text-sm text-muted-foreground">or click to browse</p>
            </>
          )}
          <p className="text-xs text-muted-foreground">
            Supports: PDF, TIFF (multi-page supported)
          </p>
        </div>
      </div>

      {/* Upload progress list */}
      {uploadingFiles.size > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-medium text-foreground">Uploading Files</h3>
          {Array.from(uploadingFiles.entries()).map(([key, fileData]) => (
            <div
              key={key}
              className="bg-card border border-border rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div
                    className={cn(
                      "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                      fileData.status === "ready" && "bg-green-100",
                      fileData.status === "error" && "bg-red-100",
                      (fileData.status === "uploading" || fileData.status === "processing") && "bg-blue-100"
                    )}
                  >
                    {fileData.status === "ready" ? (
                      <Check className="w-5 h-5 text-green-600" />
                    ) : fileData.status === "error" ? (
                      <X className="w-5 h-5 text-red-600" />
                    ) : (
                      <Loader2 className="w-5 h-5 text-primary animate-spin" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {fileData.file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <div className="flex-shrink-0 ml-4">
                  <Badge
                    variant={
                      fileData.status === "ready"
                        ? "default"
                        : fileData.status === "error"
                          ? "destructive"
                          : "secondary"
                    }
                  >
                    {fileData.status === "uploading"
                      ? `Uploading ${fileData.progress}%`
                      : fileData.status === "processing"
                        ? "Processing"
                        : fileData.status === "ready"
                          ? "Complete"
                          : "Error"}
                  </Badge>
                </div>
              </div>

              {/* Progress bar for uploading */}
              {fileData.status === "uploading" && (
                <Progress value={fileData.progress} className="h-2" />
              )}

              {/* Processing indicator */}
              {fileData.status === "processing" && (
                <Progress value={100} className="h-2 animate-pulse" />
              )}

              {/* Error message */}
              {fileData.error && (
                <p className="mt-2 text-sm text-destructive">{fileData.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
