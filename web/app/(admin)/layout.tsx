"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layouts/Sidebar";
import { MobileTabBar } from "@/components/layouts/MobileTabBar";
import { createClient } from "@/lib/supabase";
import { get } from "@/lib/api";
import type { Profile } from "@/types";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [checked, setChecked] = React.useState(false);

  React.useEffect(() => {
    const supabase = createClient();

    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        router.replace("/auth/signin");
        return;
      }

      try {
        const profile = await get<Profile>("/auth/profile");
        if (!profile.is_admin) {
          router.replace("/dashboard");
          return;
        }
        setChecked(true);
      } catch {
        router.replace("/dashboard");
      }
    });
  }, [router]);

  if (!checked) return null;

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#F5F5F7]">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isAdmin />
        <main className="flex-1 overflow-y-auto pb-20 md:pb-0">
          {children}
        </main>
      </div>
      <MobileTabBar />
    </div>
  );
}
