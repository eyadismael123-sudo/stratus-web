"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  {
    label: "Team",
    href: "/dashboard",
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <rect
          x="2.5" y="2.5" width="7" height="7" rx="1.75"
          stroke="currentColor" strokeWidth={active ? 2 : 1.5}
          fill={active ? "currentColor" : "none"}
          fillOpacity={active ? 0.15 : 0}
        />
        <rect
          x="12.5" y="2.5" width="7" height="7" rx="1.75"
          stroke="currentColor" strokeWidth={active ? 2 : 1.5}
          fill={active ? "currentColor" : "none"}
          fillOpacity={active ? 0.15 : 0}
        />
        <rect
          x="2.5" y="12.5" width="7" height="7" rx="1.75"
          stroke="currentColor" strokeWidth={active ? 2 : 1.5}
          fill={active ? "currentColor" : "none"}
          fillOpacity={active ? 0.15 : 0}
        />
        <rect
          x="12.5" y="12.5" width="7" height="7" rx="1.75"
          stroke="currentColor" strokeWidth={active ? 2 : 1.5}
          fill={active ? "currentColor" : "none"}
          fillOpacity={active ? 0.15 : 0}
        />
      </svg>
    ),
  },
  {
    label: "Hire",
    href: "/marketplace",
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path
          d="M3 6h16M3 11h16M3 16h16"
          stroke="currentColor"
          strokeWidth={active ? 2 : 1.5}
          strokeLinecap="round"
        />
        <circle cx="17" cy="6" r="2.5" fill={active ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.5" />
      </svg>
    ),
  },
  {
    label: "Billing",
    href: "/dashboard/billing",
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <rect x="3" y="5" width="16" height="12" rx="2.5" stroke="currentColor" strokeWidth={active ? 2 : 1.5} />
        <path d="M3 9.5h16" stroke="currentColor" strokeWidth={active ? 2 : 1.5} />
        <path d="M7 14h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
  },
];

export function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-[#E5E5EA] safe-area-bottom">
      <div className="flex items-center justify-around px-2 py-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))]">
        {TABS.map(({ label, href, icon }) => {
          const isActive =
            pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-col items-center gap-1 px-4 py-1 rounded-xl transition-colors min-w-0",
                isActive ? "text-[#3A3A3C]" : "text-[#A1A1A6]"
              )}
            >
              {icon(isActive)}
              <span
                className={cn(
                  "text-[10px] font-medium",
                  isActive ? "text-[#3A3A3C]" : "text-[#A1A1A6]"
                )}
              >
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
