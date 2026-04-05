"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export interface HeaderProps {
  variant?: "marketing" | "dashboard";
  userEmail?: string;
  userAvatarUrl?: string | null;
  onSignOut?: () => void;
}

const NAV_LINKS = [
  { label: "Marketplace", href: "/marketplace" },
  { label: "Pricing", href: "/pricing" },
  { label: "About", href: "/about" },
  { label: "Blog", href: "/blog" },
];

export function Header({
  variant = "marketing",
  userEmail,
  userAvatarUrl,
  onSignOut,
}: HeaderProps) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = React.useState(false);
  const [userDropOpen, setUserDropOpen] = React.useState(false);

  return (
    <header className="fixed top-0 w-full z-50 bg-[#FAF9F6]/80 backdrop-blur-md shadow-sm">
      <div className="flex justify-between items-center px-8 py-4 max-w-7xl mx-auto">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 no-underline"
        >
          <Image
            src="/logo.png"
            alt="Stratus"
            width={28}
            height={28}
            className="rounded-[6px]"
          />
          <span className="text-2xl font-display font-bold tracking-tighter text-[#012d1d]">
            Stratus
          </span>
        </Link>

        {/* Desktop nav */}
        {variant === "marketing" && (
          <nav className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map(({ label, href }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "font-body text-sm transition-colors duration-300",
                  pathname === href
                    ? "text-[#012d1d] border-b-2 border-[#012d1d] pb-0.5"
                    : "text-[#57534e] font-medium hover:text-[#065f46]"
                )}
              >
                {label}
              </Link>
            ))}
          </nav>
        )}

        {/* Right side */}
        <div className="flex items-center gap-6">
          {variant === "marketing" ? (
            <>
              <Link href="/marketplace">
                <button className="bg-[#1b4332] text-white px-5 py-2.5 rounded font-body text-sm hover:opacity-90 active:scale-[0.99] transition-all">
                  Hire an Agent
                </button>
              </Link>
              {/* Mobile hamburger */}
              <button
                className="md:hidden p-2 text-[#57534e] hover:text-[#012d1d] transition-colors"
                onClick={() => setMenuOpen((v) => !v)}
                aria-label="Toggle menu"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  {menuOpen ? (
                    <path
                      d="M4 4L16 16M16 4L4 16"
                      stroke="currentColor"
                      strokeWidth="1.75"
                      strokeLinecap="round"
                    />
                  ) : (
                    <path
                      d="M3 6H17M3 10H17M3 14H17"
                      stroke="currentColor"
                      strokeWidth="1.75"
                      strokeLinecap="round"
                    />
                  )}
                </svg>
              </button>
            </>
          ) : (
            /* Dashboard user menu */
            <div className="relative">
              <button
                onClick={() => setUserDropOpen((v) => !v)}
                className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-lg hover:bg-[#EFEEEB] transition-colors"
                aria-label="User menu"
              >
                <div className="w-7 h-7 rounded-full bg-[#1b4332] flex items-center justify-center overflow-hidden">
                  {userAvatarUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={userAvatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-white text-xs font-bold">
                      {userEmail?.charAt(0).toUpperCase() ?? "U"}
                    </span>
                  )}
                </div>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-[#414844]">
                  <path d="M2 4L6 8L10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>

              {userDropOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setUserDropOpen(false)} aria-hidden />
                  <div className="absolute right-0 top-full mt-2 z-20 w-52 bg-white rounded-xl border border-[#c1c8c2]/30 shadow-xl py-1 overflow-hidden">
                    {userEmail && (
                      <div className="px-4 py-2.5 border-b border-[#EFEEEB]">
                        <p className="text-xs text-[#414844]">Signed in as</p>
                        <p className="text-sm font-medium text-[#1a1c1a] truncate">{userEmail}</p>
                      </div>
                    )}
                    <Link
                      href="/dashboard/settings"
                      className="flex items-center gap-2 px-4 py-2.5 text-sm text-[#1a1c1a] hover:bg-[#EFEEEB] transition-colors"
                      onClick={() => setUserDropOpen(false)}
                    >
                      Settings
                    </Link>
                    <button
                      onClick={() => { setUserDropOpen(false); onSignOut?.(); }}
                      className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      Sign out
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Mobile menu */}
      {variant === "marketing" && menuOpen && (
        <div className="md:hidden bg-[#FAF9F6] border-t border-[#c1c8c2]/20">
          <nav className="flex flex-col px-8 py-4 gap-1">
            {NAV_LINKS.map(({ label, href }) => (
              <Link
                key={href}
                href={href}
                onClick={() => setMenuOpen(false)}
                className={cn(
                  "px-3 py-2.5 font-body text-sm font-medium transition-colors",
                  pathname === href ? "text-[#012d1d]" : "text-[#57534e] hover:text-[#012d1d]"
                )}
              >
                {label}
              </Link>
            ))}
            <div className="flex flex-col gap-2 mt-3 pt-3 border-t border-[#c1c8c2]/20">
              <Link href="/marketplace" onClick={() => setMenuOpen(false)}>
                <button className="w-full bg-[#1b4332] text-white py-2.5 rounded font-body text-sm hover:opacity-90 transition-all">
                  Hire an Agent
                </button>
              </Link>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
