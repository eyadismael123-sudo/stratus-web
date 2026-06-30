import Link from "next/link";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-6 text-center">
      {/* Happy octopus — bottom-left sprite */}
      {/* Happy waving octopus */}
      <div
        className="w-32 h-32 mb-6"
        style={{
          backgroundImage: "url('/mascot-poses.png')",
          backgroundSize: "200% auto",
          backgroundPosition: "100% center",
        }}
        aria-hidden="true"
      />

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
