const orgName =
  process.env.NEXT_PUBLIC_TRUSTOPS_ORG_NAME?.trim() || "Workspace";
const environmentName =
  process.env.NEXT_PUBLIC_TRUSTOPS_ENVIRONMENT?.trim() || "Production";
const secondaryEnvironmentName =
  process.env.NEXT_PUBLIC_TRUSTOPS_SECONDARY_ENVIRONMENT?.trim() || "Staging";

export const workspaceIdentity = {
  orgName,
  environmentName,
  secondaryEnvironmentName,
  avatar: (orgName[0] || "W").toUpperCase(),
  primaryLabel: `${orgName} · ${environmentName}`,
  secondaryLabel: `${orgName} — ${secondaryEnvironmentName}`,
};
