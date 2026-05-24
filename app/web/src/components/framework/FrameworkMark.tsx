"use client";

import { ShieldCheck } from "lucide-react";

type MarkTone = {
  label: string;
  short: string;
  accent: string;
  ink: string;
  wash: string;
};

const MARKS: Record<string, MarkTone> = {
  soc2: {
    label: "SOC 2",
    short: "SOC2",
    accent: "#7c3aed",
    ink: "#2e1065",
    wash: "#ede9fe",
  },
  "nist-ai-rmf": {
    label: "NIST AI RMF",
    short: "NIST",
    accent: "#2563eb",
    ink: "#1e3a8a",
    wash: "#dbeafe",
  },
  "iso-27001-2022": {
    label: "ISO 27001",
    short: "ISO",
    accent: "#0f766e",
    ink: "#134e4a",
    wash: "#ccfbf1",
  },
  "hipaa-security-rule": {
    label: "HIPAA",
    short: "HIP",
    accent: "#16a34a",
    ink: "#14532d",
    wash: "#dcfce7",
  },
  "pci-dss-v4": {
    label: "PCI DSS",
    short: "PCI",
    accent: "#ea580c",
    ink: "#7c2d12",
    wash: "#ffedd5",
  },
  "gdpr-2016-679": {
    label: "GDPR",
    short: "GDPR",
    accent: "#1d4ed8",
    ink: "#172554",
    wash: "#bfdbfe",
  },
  "eu-ai-act-2024-1689": {
    label: "EU AI Act",
    short: "AI",
    accent: "#db2777",
    ink: "#831843",
    wash: "#fce7f3",
  },
  "iso-42001-2023": {
    label: "ISO 42001",
    short: "42001",
    accent: "#0891b2",
    ink: "#164e63",
    wash: "#cffafe",
  },
};

const FALLBACK: MarkTone = {
  label: "Framework",
  short: "FW",
  accent: "#475569",
  ink: "#0f172a",
  wash: "#e2e8f0",
};

const SIZE: Record<"sm" | "md" | "lg", { box: number; text: number; icon: number }> = {
  sm: { box: 28, text: 8, icon: 7 },
  md: { box: 42, text: 10, icon: 9 },
  lg: { box: 56, text: 12, icon: 12 },
};

export function frameworkMark(frameworkId: string): MarkTone {
  return MARKS[frameworkId] ?? FALLBACK;
}

export function frameworkLabel(frameworkId: string): string {
  return frameworkMark(frameworkId).label;
}

export function FrameworkMark({
  frameworkId,
  size = "md",
  showLabel = false,
  className = "",
}: {
  frameworkId: string;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}) {
  const mark = frameworkMark(frameworkId);
  const dimensions = SIZE[size];
  const radius = size === "lg" ? 10 : 8;

  return (
    <span className={["inline-flex min-w-0 items-center gap-2", className].join(" ")}>
      <svg
        width={dimensions.box}
        height={dimensions.box}
        viewBox="0 0 56 56"
        role="img"
        aria-label={`${mark.label} framework badge`}
        className="shrink-0 drop-shadow-sm"
      >
        <rect
          x="1"
          y="1"
          width="54"
          height="54"
          rx={radius}
          fill={mark.wash}
          stroke={mark.accent}
          strokeWidth="2"
        />
        <path
          d="M28 7.5 44 14.4v12.2c0 10-6.6 18.8-16 21.9-9.4-3.1-16-11.9-16-21.9V14.4L28 7.5Z"
          fill="#ffffff"
          opacity=".82"
        />
        <path
          d="M20.2 28.1 25.2 33 36.5 21.7"
          fill="none"
          stroke={mark.accent}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="4"
        />
        <text
          x="28"
          y="48"
          textAnchor="middle"
          fill={mark.ink}
          fontFamily="Inter, Arial, sans-serif"
          fontSize={dimensions.text}
          fontWeight="900"
        >
          {mark.short}
        </text>
      </svg>
      {showLabel && (
        <span className="truncate text-sm font-black text-ink">
          <ShieldCheck className="mr-1 inline h-3.5 w-3.5 text-brand" />
          {mark.label}
        </span>
      )}
    </span>
  );
}
