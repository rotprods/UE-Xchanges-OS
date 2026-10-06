"use client";

import dynamic from "next/dynamic";

const AppShell = dynamic(() => import("../components/layout/AppShell"), { ssr: false });

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
