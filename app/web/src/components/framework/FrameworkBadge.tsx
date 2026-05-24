"use client";

/**
 * Per-framework badge components. These are stylized monograms designed for
 * the workbench — NOT reproductions of trademarked logos, certification seals,
 * or regulator marks. Each badge uses a TrustOps-owned shape language and
 * short identifier so the product has clear framework recognition without
 * implying certification.
 *
 * Add a new framework: extend the `framework_id → component` map at the
 * bottom and `FrameworkBadge` resolves it. Unknown framework_ids fall back
 * to a neutral monogram.
 */

import type { CSSProperties } from "react";

interface BadgeProps {
  size?: number;
  className?: string;
}

const baseStyle = (size: number): CSSProperties => ({
  width: size,
  height: size,
  display: "inline-block",
  flexShrink: 0,
});

// --- Per-framework SVGs -----------------------------------------------------

function Soc2({ size = 32, className }: BadgeProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label="SOC 2"
    >
      <circle cx="24" cy="24" r="22" fill="#0f3a78" />
      <circle cx="24" cy="24" r="22" fill="none" stroke="#3b82f6" strokeWidth="2" />
      <text
        x="24"
        y="22"
        textAnchor="middle"
        fill="#ffffff"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="800"
        fontSize="12"
      >
        SOC
      </text>
      <text
        x="24"
        y="34"
        textAnchor="middle"
        fill="#bfdbfe"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="800"
        fontSize="11"
      >
        2
      </text>
    </svg>
  );
}

function NistAi({ size = 32, className }: BadgeProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label="NIST AI RMF"
    >
      <rect x="2" y="2" width="44" height="44" rx="10" fill="#0b3d91" />
      <rect x="2" y="2" width="44" height="44" rx="10" fill="none" stroke="#fc3d21" strokeWidth="2" />
      <text
        x="24"
        y="22"
        textAnchor="middle"
        fill="#ffffff"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="13"
      >
        NIST
      </text>
      <text
        x="24"
        y="34"
        textAnchor="middle"
        fill="#fbbf24"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="10"
      >
        AI RMF
      </text>
    </svg>
  );
}

function Iso27001({ size = 32, className }: BadgeProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label="ISO 27001:2022"
    >
      <rect x="2" y="2" width="44" height="44" rx="6" fill="#b91c1c" />
      <rect x="2" y="2" width="44" height="44" rx="6" fill="none" stroke="#fecaca" strokeWidth="1.5" />
      <text
        x="24"
        y="22"
        textAnchor="middle"
        fill="#ffffff"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="13"
      >
        ISO
      </text>
      <text
        x="24"
        y="34"
        textAnchor="middle"
        fill="#fecaca"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="800"
        fontSize="9.5"
      >
        27001
      </text>
    </svg>
  );
}

function Iso42001({ size = 32, className }: BadgeProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label="ISO/IEC 42001:2023"
    >
      <rect x="2" y="2" width="44" height="44" rx="6" fill="#7c2d12" />
      <rect x="2" y="2" width="44" height="44" rx="6" fill="none" stroke="#fed7aa" strokeWidth="1.5" />
      <text
        x="24"
        y="22"
        textAnchor="middle"
        fill="#ffffff"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="13"
      >
        ISO
      </text>
      <text
        x="24"
        y="34"
        textAnchor="middle"
        fill="#fed7aa"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="800"
        fontSize="9.5"
      >
        42001
      </text>
    </svg>
  );
}

function Hipaa({ size = 32, className }: BadgeProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label="HIPAA Security Rule"
    >
      <path
        d="M24 4 L42 10 L42 24 C42 36 33 43 24 44 C15 43 6 36 6 24 L6 10 Z"
        fill="#047857"
        stroke="#a7f3d0"
        strokeWidth="1.5"
      />
      <text
        x="24"
        y="28"
        textAnchor="middle"
        fill="#ffffff"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="11"
      >
        HIPAA
      </text>
    </svg>
  );
}

function PciDss({ size = 32, className }: BadgeProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label="PCI DSS v4.0"
    >
      <rect x="2" y="6" width="44" height="36" rx="4" fill="#b45309" />
      <rect x="2" y="6" width="44" height="36" rx="4" fill="none" stroke="#fde68a" strokeWidth="1.5" />
      <rect x="2" y="12" width="44" height="6" fill="#92400e" />
      <text
        x="24"
        y="30"
        textAnchor="middle"
        fill="#ffffff"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="13"
      >
        PCI
      </text>
      <text
        x="24"
        y="40"
        textAnchor="middle"
        fill="#fde68a"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="800"
        fontSize="8"
      >
        DSS v4
      </text>
    </svg>
  );
}

function Gdpr({ size = 32, className }: BadgeProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label="GDPR (EU Regulation 2016/679)"
    >
      <rect x="2" y="2" width="44" height="44" rx="22" fill="#003399" />
      {/* Abstract readiness dots; not the official EU flag rendering. */}
      {Array.from({ length: 12 }).map((_, i) => {
        const angle = (i / 12) * Math.PI * 2 - Math.PI / 2;
        const cx = 24 + Math.cos(angle) * 16;
        const cy = 24 + Math.sin(angle) * 16;
        return <circle key={i} cx={cx} cy={cy} r="1.6" fill="#ffcc00" />;
      })}
      <text
        x="24"
        y="28"
        textAnchor="middle"
        fill="#ffffff"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="12"
      >
        GDPR
      </text>
    </svg>
  );
}

function EuAiAct({ size = 32, className }: BadgeProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label="EU AI Act (Regulation 2024/1689)"
    >
      <rect x="2" y="2" width="44" height="44" rx="8" fill="#1e3a8a" />
      <rect x="2" y="2" width="44" height="44" rx="8" fill="none" stroke="#ffcc00" strokeWidth="2" />
      <text
        x="24"
        y="20"
        textAnchor="middle"
        fill="#ffcc00"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="11"
      >
        EU
      </text>
      <text
        x="24"
        y="34"
        textAnchor="middle"
        fill="#ffffff"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="11"
      >
        AI ACT
      </text>
    </svg>
  );
}

function Fallback({ size = 32, className, label }: BadgeProps & { label: string }) {
  const initials = label.slice(0, 2).toUpperCase();
  return (
    <svg
      viewBox="0 0 48 48"
      style={baseStyle(size)}
      className={className}
      role="img"
      aria-label={label}
    >
      <rect x="2" y="2" width="44" height="44" rx="8" fill="#475569" />
      <text
        x="24"
        y="30"
        textAnchor="middle"
        fill="#e2e8f0"
        fontFamily="ui-sans-serif, system-ui, sans-serif"
        fontWeight="900"
        fontSize="16"
      >
        {initials}
      </text>
    </svg>
  );
}

// --- Resolver ---------------------------------------------------------------

const BADGES: Record<string, (props: BadgeProps) => React.JSX.Element> = {
  soc2: Soc2,
  "nist-ai-rmf": NistAi,
  "iso-27001-2022": Iso27001,
  "iso-42001-2023": Iso42001,
  "hipaa-security-rule": Hipaa,
  "pci-dss-v4": PciDss,
  "gdpr-2016-679": Gdpr,
  "eu-ai-act-2024-1689": EuAiAct,
};

interface FrameworkBadgeProps extends BadgeProps {
  frameworkId: string;
  fallbackLabel?: string;
}

export function FrameworkBadge({
  frameworkId,
  fallbackLabel,
  size,
  className,
}: FrameworkBadgeProps) {
  const Badge = BADGES[frameworkId];
  if (Badge) return <Badge size={size} className={className} />;
  return <Fallback size={size} className={className} label={fallbackLabel ?? frameworkId} />;
}
