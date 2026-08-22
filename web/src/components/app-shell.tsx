"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthService } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useMe } from "@/lib/hooks";

const NAV_ITEMS = [
  { href: "/", label: "This Week" },
  { href: "/inbox", label: "Inbox" },
  { href: "/review", label: "Weekly Review" },
  { href: "/roles", label: "Roles & Goals" },
  { href: "/projects", label: "Projects" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: me } = useMe();
  const isGuest = me?.role === "guest";

  async function handleLogout() {
    await AuthService.logoutApiV1AuthLogoutPost();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-screen flex-1 flex-col">
      <header className="flex items-center justify-between border-b px-4 py-3">
        <span className="flex items-center gap-2 font-semibold">
          Compass
          {isGuest && (
            <span className="demo-rise rounded-full border px-2 py-0.5 text-xs font-normal text-muted-foreground">
              Demo · read-only
            </span>
          )}
        </span>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          {isGuest ? "Exit demo" : "Sign out"}
        </Button>
      </header>
      {isGuest && (
        <div
          className="demo-rise border-b bg-accent/50 px-4 py-2 text-center text-xs text-muted-foreground"
          style={{ animationDelay: "150ms" }}
        >
          You&apos;re exploring a live demo — a sample week of roles, big rocks, and an
          AI weekly review. Everything is browsable, nothing is editable.
        </div>
      )}
      <div className="flex flex-1">
        <nav className="w-48 shrink-0 border-r p-3">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "block rounded-md px-3 py-2 text-sm hover:bg-accent",
                    pathname === item.href && "bg-accent font-medium",
                  )}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <main className="flex-1 overflow-x-auto p-4">{children}</main>
      </div>
    </div>
  );
}
