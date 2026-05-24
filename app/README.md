# TrustOps Console (React workbench)

The assessment console ships as a Next.js 15 application (App Router, TypeScript)
in `app/web/`. It is built to a static export that lands inside the Python
package so `pip install trustops-security-data-lake` ships the UI — no Node
runtime is required in production.

```
app/web/                                     ← source (TypeScript / React)
src/security_lakehouse/web/dist/             ← static export (ships in the wheel)
```

## Stack

- **Next.js 15** App Router, TypeScript, static export (`output: "export"`).
- **Tailwind CSS** for styling.
- **Radix UI** primitives + locally-vendored shadcn-style components in
  `src/components/ui/`.
- **TanStack Query** for `/api/*` fetch + cache + invalidation.
- **TanStack Table** for control / evidence / violation tables.
- **Recharts** for KPI / framework / posture-trend charts.
- **Visx** for bespoke visualizations (Sankey, force graphs, heatmaps).
- **framer-motion** for transitions.
- **Lucide** for icons.

## Develop locally

```bash
# one-time: bring up the assessment lake + API
make pipeline
PYTHONPATH=src python -m security_lakehouse.cli serve --lake build/lakehouse

# in another terminal: Next.js dev server on http://127.0.0.1:5173/console
# (dev server proxies /api to the Python server on :8787)
make web-install
make web-dev
```

## Build for ship

```bash
make web-build                # populates src/security_lakehouse/web/dist/
make web-typecheck            # tsc --noEmit
```

After `web-build`, `pip install -e .` and `security-lakehouse serve` will
serve the React workbench from the wheel; without the build, the legacy
single-file dashboard (`dashboard.py`) renders as a graceful fallback so the
existing `dashboard render` CI gate stays green.

## Offline / audit handoff

The legacy CLI still emits a single self-contained HTML for offline
distribution:

```bash
security-lakehouse dashboard --lake build/lakehouse --out build/dashboard/index.html
```

PR 4 replaces the legacy template with a single-file export of the React
build (data injected via `<script id="app-data">`).
