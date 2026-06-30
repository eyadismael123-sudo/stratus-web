import Link from "next/link";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-6 text-center">
      <img src="/mascot-happy.png" alt="" aria-hidden="true" className="w-32 h-auto mb-6" />

      <h3 className="text-[18px] font-black text-[#2E4057] tracking-[-0.02em] mb-2">
        Your team is empty
      </h3>
      <p className="text-[14px] text-[#2E4057]/50 leading-relaxed max-w-[280px] mb-8">
        Hire your first AI agent from the marketplace. They start working tomorrow morning.
      </p>

      <Link
        href="/marketplace"
        className="inline-flex items-center gap-2 bg-[#EB0043] text-white text-[14px] font-bold rounded-[10px] px-6 py-3 no-underline transition-all hover:bg-[#4E0110] hover:-translate-y-px"
      >
        Browse the marketplace →
      </Link>
    </div>
  );
}
