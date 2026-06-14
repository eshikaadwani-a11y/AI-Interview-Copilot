"use client";

import { useCallback, useRef, useState, type DragEvent } from "react";
import { motion } from "framer-motion";
import { FileUp, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatApiError } from "@/lib/auth";
import { useUploadResume } from "@/lib/resumes";
import type { ResumeDetail } from "@/lib/types";

interface UploadDropzoneProps {
  onUploaded?: (resume: ResumeDetail) => void;
}

/** Drag-and-drop (or click) PDF uploader with progress and error states. */
export function UploadDropzone({ onUploaded }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const upload = useUploadResume();

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      if (file.type !== "application/pdf") {
        return;
      }
      upload.mutate(file, { onSuccess: (data) => onUploaded?.(data) });
    },
    [upload, onUploaded],
  );

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  return (
    <div>
      <motion.div
        whileHover={{ scale: 1.005 }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border border-dashed p-10 text-center transition-colors",
          dragging ? "border-primary bg-primary/5" : "border-border bg-surface/40 hover:border-primary/50",
        )}
      >
        <span className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-primary/15 text-primary">
          {upload.isPending ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <FileUp className="h-6 w-6" />
          )}
        </span>
        <div>
          <p className="font-medium">
            {upload.isPending ? "Parsing your resume…" : "Drop your resume PDF here"}
          </p>
          <p className="text-sm text-muted">
            {upload.isPending ? "Extracting skills, experience, and projects" : "or click to browse · PDF only · max 10MB"}
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </motion.div>

      {upload.isError && (
        <p className="mt-3 text-sm text-danger">{formatApiError(upload.error)}</p>
      )}
    </div>
  );
}
