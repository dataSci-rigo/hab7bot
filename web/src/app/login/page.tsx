"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthService, ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await AuthService.loginApiV1AuthLoginPost({ username, password });
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? "Incorrect username or password." : "Login failed.");
    } finally {
      setLoading(false);
    }
  }


  return (
    <main className="flex flex-1 items-center justify-center p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
        <div className="space-y-1 text-center">
          <h1 className="text-2xl font-semibold">Compass</h1>
          <p className="text-sm text-muted-foreground">Sign in to your planner</p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="username">Username</Label>
          <Input
            id="username"
            autoFocus
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </Button>
        <p className="demo-glow mx-auto w-fit rounded-md px-3 py-1 text-center text-xs text-muted-foreground">
          Just looking? Try the read-only demo —{" "}
          <code className="rounded bg-muted px-1 font-mono">demo</code> /{" "}
          <code className="rounded bg-muted px-1 font-mono">demo</code>
        </p>
      </form>
    </main>
  );
}
