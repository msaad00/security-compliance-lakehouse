"use client";

/**
 * Neutral framework labels for the workbench.
 *
 * Do not recreate framework logos, certification seals, regulator marks, or
 * lookalike badges here. If an official public logo is ever used, it must come
 * from the official brand/certification program, carry documented permission,
 * and be tracked as a third-party asset.
 */

import type { CSSProperties } from "react";

interface FrameworkBadgeProps {
  frameworkId: string;
  fallbackLabel?: string;
  size?: number;
  className?: string;
}

const LABELS: Record<string, string> = {
  soc2: "SOC 2",
  "nist-ai-rmf": "NIST AI",
  "iso-27001-2022": "ISO 27001",
  "iso-42001-2023": "ISO 42001",
  "hipaa-security-rule": "HIPAA",
  "pci-dss-v4": "PCI DSS",
  "gdpr-2016-679": "GDPR",
  "eu-ai-act-2024-1689": "EU AI Act",
};

const styleFor = (size: number): CSSProperties => ({
  width: Math.max(size * 2.8, 86),
  minHeight: size,
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  flexShrink: 0,
});

export function FrameworkBadge({
  frameworkId,
  fallbackLabel,
  size = 32,
  className,
}: FrameworkBadgeProps) {
  const label = LABELS[frameworkId] ?? fallbackLabel ?? frameworkId;

  return (
    <span
      style={styleFor(size)}
      className={[
        "rounded-md border border-line bg-panel px-2 text-center text-[11px] font-semibold leading-tight text-ink",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      role="img"
      aria-label={`${label} framework label; not an official logo or certification seal`}
      title={`${label} framework label; not an official logo or certification seal`}
    >
      {label}
    </span>
  );
}
