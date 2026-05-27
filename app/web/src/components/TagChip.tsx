"use client";

import { X } from "lucide-react";
import type { Tag } from "@/lib/api/types";

interface TagChipProps {
  tag: Tag;
  onRemove?: (tagId: string) => void;
  size?: "sm" | "md";
}

/** A coloured pill that displays a single tag. Pass ``onRemove`` to show an ×. */
export function TagChip({ tag, onRemove, size = "sm" }: TagChipProps) {
  const bg = tag.color || "#6366f1";
  const padding = size === "sm" ? "px-2 py-0.5" : "px-2.5 py-1";
  const textSize = size === "sm" ? "text-[11px]" : "text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium text-white ${padding} ${textSize}`}
      style={{ backgroundColor: bg }}
    >
      {tag.name}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove(tag.id);
          }}
          className="rounded-full opacity-70 hover:opacity-100 focus:outline-none"
          aria-label={`Remove tag ${tag.name}`}
        >
          <X className="h-2.5 w-2.5" />
        </button>
      )}
    </span>
  );
}
