"use client";

import { ShieldCheck, Terminal, LogIn } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["auth-methods"],
    queryFn: api.authMethods,
    retry: false,
  });

  const configured = data?.methods.filter((method) => method.configured) ?? [];

  return (
    <section className="grid min-h-screen place-items-center p-6">
      <div className="grid w-full max-w-[980px] gap-5 lg:grid-cols-[1fr_380px]">
        <div className="rounded-2xl border border-[#1e334a] bg-[#07111e] p-8 text-white shadow-hero">
          <Badge tone="info" className="mb-5 bg-cyan-100 text-cyan-800">
            Server mode
          </Badge>
          <h1 className="max-w-[680px] text-4xl font-black leading-[1.04]">
            Sign in to the TrustOps control plane.
          </h1>
          <p className="mt-4 max-w-[620px] text-base leading-7 text-slate-300">
            Browser access uses the same tenant, role, and audit boundary as API
            keys. Unauthenticated console requests are redirected here before
            any protected data loads.
          </p>
          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {["Tenant scoped", "RBAC enforced", "Audit logged"].map((label) => (
              <div
                key={label}
                className="rounded-lg border border-white/15 bg-white/5 p-3 text-sm font-extrabold text-slate-100"
              >
                <ShieldCheck className="mb-2 h-4 w-4 text-cyan-300" />
                {label}
              </div>
            ))}
          </div>
        </div>

        <Card className="self-stretch">
          <CardHeader>
            <CardTitle>Available login methods</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {isLoading && (
              <div className="rounded-lg border border-line bg-slate-50 p-4 text-sm font-bold text-muted">
                Checking identity providers...
              </div>
            )}

            {!isLoading &&
              configured.map((method) => (
                <Button key={method.id} asChild variant="primary" size="lg">
                  <a href={method.login_url}>
                    <LogIn className="h-4 w-4" />
                    Continue with {method.label}
                  </a>
                </Button>
              ))}

            {!isLoading && configured.length === 0 && (
              <div className="rounded-lg border border-line bg-slate-50 p-4">
                <div className="flex items-start gap-3">
                  <Terminal className="mt-0.5 h-5 w-5 text-muted" />
                  <div>
                    <div className="font-black text-ink">
                      No browser SSO provider is configured.
                    </div>
                    <p className="mt-1 text-sm leading-6 text-muted">
                      Configure OIDC or SAML for human login, or use an API key
                      for agent and CI access.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {isError && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-bold text-amber-900">
                Auth discovery is unavailable on this server.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
