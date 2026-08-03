"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AuthService } from "@/lib/api-client";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { data, isError, isPending } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => AuthService.meApiV1AuthMeGet(),
  });

  useEffect(() => {
    if (isError) router.replace("/login");
  }, [isError, router]);

  if (isPending || isError || !data) return null;

  return <>{children}</>;
}
