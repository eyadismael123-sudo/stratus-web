"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export interface SidebarProps {
  isAdmin?: boolean;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
}

const DashboardIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <rect x="2" y="2" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
    <rect x="10" y="2" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
    <rect x="2" y="10" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
    <rect x="10" y="10" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
  </svg>
);

const MarketplaceIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M2 5h14M2 9h14M2 13h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    <circle cx="14.5" cy="5" r="2" fill="currentColor" />
  </svg>
);

const BillingIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <rect x="2" y="4" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" />
    <path d="M2 8h14" stroke="currentColor" strokeWidth="1.5" />
    <path d="M6 12h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

const SettingsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.5" />
    <path
      d="M9 2v1.5M9 14.5V16M2 9h1.5M14.5 9H16M3.757 3.757l1.06 1.06M13.183 13.183l1.06 1.06M3.757 14.243l1.06-1.06M13.183 4.817l1.06-1.06"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  </svg>
);

const AdminIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <path d="M9 2L11.5 7H16L12 10.5L13.5 16L9 12.5L4.5 16L6 10.5L2 7H6.5L9 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
  </svg>
);

const NAV_ITEMS: NavItem[] = [
  { label: "Your Team",    href: "/dashboard",           icon: <DashboardIcon /> },
  { label: "Marketplace",  href: "/marketplace",         icon: <MarketplaceIcon /> },
  { label: "Billing",      href: "/dashboard/billing",   icon: <BillingIcon /> },
  { label: "Settings",     href: "/dashboard/settings",  icon: <SettingsIcon /> },
  { label: "Admin",        href: "/admin",               icon: <AdminIcon />, adminOnly: true },
];

export function Sidebar({ isAdmin = false }: SidebarProps) {
  const pathname = usePathname();

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.adminOnly || (item.adminOnly && isAdmin)
  );

  return (
    <aside className="hidden md:flex flex-col w-56 shrink-0 h-full bg-white border-r border-[#E5E5EA] py-6 px-3">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2 px-2 mb-8">
        <div className="w-7 h-7 bg-[#3A3A3C] rounded-lg flex items-center justify-center">
          <span className="text-white text-xs font-black tracking-tight">S</span>
        </div>
        <span className="text-base font-black text-[#3A3A3C] tracking-tight">Stratus</span>
      </Link>

      {/* Nav */}
      <nav className="flex flex-col gap-1 flex-1">
        {visibleItems.map(({ label, href, icon, adminOnly }) => {
          const isActive = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors duration-150",
                isActive
                  ? "bg-[#3A3A3C] text-white"
                  : "text-[#6A6A6E] hover:bg-[#F2F2F4] hover:text-[#3A3A3C]",
                adminOnly && !isActive && "text-[#A1A1A6]"
              )}
            >
              <span className={cn("shrink-0", isActive ? "text-white" : "")}>
                {icon}
              </span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom hint */}
      <div className="px-2 pt-4 border-t border-[#F2F2F4]">
        <p className="text-xs text-[#A1A1A6]">Stratus v1.0</p>
      </div>
    </aside>
  );
}
