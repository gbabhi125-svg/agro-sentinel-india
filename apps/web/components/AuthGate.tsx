"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";
import BottomNav from "@/components/BottomNav";

const PUBLIC_ROUTES = ["/login", "/register"];

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = PUBLIC_ROUTES.includes(pathname);

  useEffect(() => {
    if (!loading && !user && !isPublic) {
      router.replace("/login");
    }
  }, [loading, user, isPublic, router, pathname]);

  if (isPublic) {
    return <>{children}</>;
  }

  if (loading || !user) {
    return (
      <main>
        <div className="card center" style={{ marginTop: 40 }}>
          <div className="spinner" />
        </div>
      </main>
    );
  }

  return (
    <>
      <BottomNav />
      {children}
    </>
  );
}
