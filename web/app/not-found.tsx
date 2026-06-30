import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#CCDAD1] flex flex-col items-center justify-center px-6 text-center">
      <img src="/mascot-confused.png" alt="" aria-hidden="true" className="w-44 h-auto mb-8" />

      <h1 className="font-display font-black text-[#2E4057] text-6xl mb-3 tracking-tight">
        404
      </h1>
      <p className="text-[#2E4057] text-xl font-semibold mb-2">
        This page doesn&apos;t exist.
      </p>
      <p className="text-[#2E4057]/60 text-base mb-10 max-w-xs leading-relaxed">
        Even our agents couldn&apos;t find it — and they work 24/7.
      </p>

      <Link
        href="/"
        className="inline-flex items-center gap-2 bg-[#EB0043] text-white font-bold text-sm rounded-xl px-7 py-3.5 transition-all hover:bg-[#4E0110] hover:-translate-y-px"
      >
        Back to home →
      </Link>
    </div>
  );
}
