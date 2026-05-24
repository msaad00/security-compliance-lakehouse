import type { NextConfig } from "next";

// Static export so `npm run build` emits a fully static bundle into
// src/security_lakehouse/web/dist/ — Python wheel ships it, no Node in prod.
// basePath '/console' matches the Python server route.
const config: NextConfig = {
  output: "export",
  basePath: "/console",
  assetPrefix: "/console",
  trailingSlash: true,
  distDir: "../../src/security_lakehouse/web/dist",
  cleanDistDir: true,
  images: { unoptimized: true },
  reactStrictMode: true,
  typescript: { ignoreBuildErrors: false },
  eslint: { ignoreDuringBuilds: true },
};

export default config;
