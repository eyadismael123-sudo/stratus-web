import Link from "next/link";

const FOOTER_COLS = [
  {
    heading: "Product",
    links: [
      { label: "Agents", href: "/agents/linkedin-post-agent" },
      { label: "Pricing", href: "/pricing" },
      { label: "Dashboard", href: "/dashboard" },
      { label: "Marketplace", href: "/marketplace" },
    ],
  },
  {
    heading: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Blog", href: "/blog" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    heading: "Legal",
    links: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
    ],
  },
];

export function Footer() {
  return (
    <footer style={{ background: "#EFEEEB" }}>
      <div className="max-w-[1440px] mx-auto px-6 md:px-12 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10 mb-16">
          {/* Brand column — spans 2 on desktop */}
          <div className="col-span-2 flex flex-col gap-4">
            <span className="text-[18px] font-black tracking-tight font-display" style={{ color: "#1B4332" }}>
              Stratus
            </span>
            <p className="text-[14px] leading-relaxed max-w-[220px]" style={{ color: "#8A8A8A" }}>
              Hire your first AI employee. Built for MENA businesses.
            </p>
            <p className="text-[12px] font-medium" style={{ color: "#8A8A8A" }}>
              Built in Dubai · Arabic + English
            </p>
          </div>

          {/* Link columns */}
          {FOOTER_COLS.map(({ heading, links }) => (
            <div key={heading} className="flex flex-col gap-4">
              <p className="text-[11px] font-bold uppercase tracking-widest" style={{ color: "#1A1A1A" }}>
                {heading}
              </p>
              <ul className="flex flex-col gap-3 list-none">
                {links.map(({ label, href }) => (
                  <li key={href}>
                    <Link
                      href={href}
                      className="text-[14px] no-underline transition-colors duration-150 hover:opacity-70"
                      style={{ color: "#8A8A8A" }}
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div
          className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-3"
          style={{ borderTop: "1px solid #c1c8c2" }}
        >
          <p className="text-[12px]" style={{ color: "#8A8A8A" }}>
            &copy; {new Date().getFullYear()} Stratus. All rights reserved.
          </p>
          <p className="text-[12px]" style={{ color: "#8A8A8A" }}>
            Your AI workforce. Built for MENA.
          </p>
        </div>
      </div>
    </footer>
  );
}
