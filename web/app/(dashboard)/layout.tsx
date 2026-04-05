"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layouts/Sidebar";
import { MobileTabBar } from "@/components/layouts/MobileTabBar";
import { Header } from "@/components/layouts/Header";
import { createClient } from "@/lib/supabase";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [email, setEmail] = React.useState<string | undefined>();
  const [avatarUrl, setAvatarUrl] = React.useState<string | null>(null);

  React.useEffect(() => {
    const supabase = createClient();

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.replace("/");
        return;
      }
      setEmail(session.user.email);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (!session) router.replace("/");
      }
    );

    return () => subscription.unsubscribe();
  }, [router]);

  const handleSignOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.replace("/");
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#F5F5F7]">
      {/* Mobile header */}
      <div className="md:hidden">
        <Header
          variant="dashboard"
          userEmail={email}
          userAvatarUrl={avatarUrl}
          onSignOut={handleSignOut}
        />
      </div>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto pb-20 md:pb-0">
          {children}
        </main>
      </div>

      <MobileTabBar />
    </div>
  );
}
