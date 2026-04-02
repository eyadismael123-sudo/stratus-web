import Link from "next/link";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-6 text-center">
      {/* Icon */}
      <div className="w-16 h-16 rounded-[20px] bg-white flex items-center justify-center mb-5 shadow-sm">
        <svg
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#AEAEB2"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="8" r="4"/>
          <path d="M6 20v-2a6 6 0 0112 0v2"/>
          <line x1="12" y1="14" x2="12" y2="18"/>
          <line x1="9" y1="17" x2="15" y2="17"/>
        </svg>
      </div>

      <h3 className="text-[18px] font-black text-[#3A3A3C] tracking-[-0.02em] mb-2">
        Your team is empty
      </h3>
      <p className="text-[14px] text-[#8E8E93] leading-relaxed max-w-[320px] mb-8">
        Hire your first AI agent from the marketplace. They start working tomorrow morning.
      </p>

      <Link
        href="/marketplace"
        className="inline-flex items-center gap-2 bg-[#3A3A3C] text-white text-[14px] font-bold rounded-[10px] px-6 py-3 no-underline transition-all hover:bg-[#2c2c2e] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(0,0,0,0.2)]"
      >
        Browse the marketplace →
      </Link>
    </div>
  );
}
