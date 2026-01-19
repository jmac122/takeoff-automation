/**
 * Document uploader component with drag-and-drop support.
 */

import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadDocument, pollDocumentStatus, DocumentStatus } from "../../api/documents";

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
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200
          ${
            isDragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-gray-400 bg-white"
          }
        `}
      >
        <input {...getInputProps()} />
        <div className="space-y-2">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {isDragActive ? (
            <p className="text-lg text-blue-600">Drop files here...</p>
          ) : (
            <>
              <p className="text-lg text-gray-700">
                Drag and drop PDF or TIFF files here
              </p>
              <p className="text-sm text-gray-500">or click to browse</p>
            </>
          )}
          <p className="text-xs text-gray-400">
            Supports: PDF, TIFF (multi-page supported)
          </p>
        </div>
      </div>

      {/* Upload progress list */}
      {uploadingFiles.size > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-medium text-gray-900">Uploading Files</h3>
          {Array.from(uploadingFiles.entries()).map(([key, fileData]) => (
            <div
              key={key}
              className="bg-white border border-gray-200 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <div
                    className={`
                    flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                    ${
                      fileData.status === "ready"
                        ? "bg-green-100"
                        : fileData.status === "error"
                        ? "bg-red-100"
                        : "bg-blue-100"
                    }
                  `}
                  >
                    {fileData.status === "ready" ? (
                      <svg
                        className="w-5 h-5 text-green-600"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : fileData.status === "error" ? (
                      <svg
                        className="w-5 h-5 text-red-600"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-5 h-5 text-blue-600 animate-spin"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {fileData.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <div className="flex-shrink-0 ml-4">
                  <span
                    className={`
                    inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    ${
                      fileData.status === "ready"
                        ? "bg-green-100 text-green-800"
                        : fileData.status === "error"
                        ? "bg-red-100 text-red-800"
                        : fileData.status === "processing"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-blue-100 text-blue-800"
                    }
                  `}
                  >
                    {fileData.status === "uploading"
                      ? `Uploading ${fileData.progress}%`
                      : fileData.status === "processing"
                      ? "Processing"
                      : fileData.status === "ready"
                      ? "Complete"
                      : "Error"}
                  </span>
                </div>
              </div>

              {/* Progress bar for uploading */}
              {fileData.status === "uploading" && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${fileData.progress}%` }}
                  />
                </div>
              )}

              {/* Processing indicator */}
              {fileData.status === "processing" && (
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div className="bg-yellow-500 h-2 rounded-full animate-pulse w-full" />
                </div>
              )}

              {/* Error message */}
              {fileData.error && (
                <p className="mt-2 text-sm text-red-600">{fileData.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
