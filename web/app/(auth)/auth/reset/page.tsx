"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase";

export default function ResetPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error: authError } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/update-password`,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    setSent(true);
    setLoading(false);
  }

  return (
    <>
      {/* Fixed logo */}
      <Link
        href="/"
        className="fixed top-6 left-8 text-[20px] font-black tracking-[-0.04em] text-[#3A3A3C] no-underline z-10"
      >
        Stratus
      </Link>

      <div
        className="w-full max-w-[440px] bg-white rounded-[16px] p-10"
        style={{
          boxShadow: "0 20px 60px rgba(0,0,0,0.10), 0 8px 20px rgba(0,0,0,0.06)",
        }}
      >
        {sent ? (
          <div className="text-center">
            <div className="w-14 h-14 rounded-full bg-[#3A3A3C]/08 flex items-center justify-center mx-auto mb-5">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3A3A3C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </div>
            <h2 className="text-[22px] font-black text-[#3A3A3C] tracking-[-0.03em] mb-2">
              Check your email
            </h2>
            <p className="text-[14px] text-[#6A6A6E] leading-relaxed">
              We sent a reset link to <strong className="text-[#3A3A3C]">{email}</strong>.
              It expires in 1 hour.
            </p>
            <Link
              href="/auth/signin"
              className="inline-block mt-6 text-[13px] font-semibold text-[#3A3A3C] no-underline hover:underline"
            >
              Back to sign in
            </Link>
          </div>
        ) : (
          <>
            <Link
              href="/auth/signin"
              className="flex items-center gap-1.5 text-[13px] text-[#6A6A6E] no-underline hover:text-[#3A3A3C] transition-colors mb-6"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6"/>
              </svg>
              Back to sign in
            </Link>

            <h1
              className="font-black text-[#3A3A3C] tracking-[-0.035em] leading-[1.15] mb-1.5"
              style={{ fontSize: "clamp(22px, 4vw, 26px)" }}
            >
              Reset your password
            </h1>
            <p className="text-[14px] text-[#6A6A6E] mb-7 leading-relaxed">
              Enter your email and we&apos;ll send you a reset link.
            </p>

            {error && (
              <div className="mb-5 px-4 py-3 rounded-[10px] bg-red-50 border border-red-200 text-[13px] text-red-600 font-medium">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div>
                <label className="block text-[13px] font-semibold text-[#3A3A3C] mb-1.5 tracking-[-0.01em]">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full h-11 text-[15px] text-[#3A3A3C] bg-[#FAFAFA] border border-[#D2D2D7] rounded-[10px] px-3.5 outline-none transition-all placeholder:text-[#A8A8AD] hover:border-[#AEAEB2] hover:bg-white focus:border-[#3A3A3C] focus:bg-white focus:shadow-[0_0_0_3px_rgba(58,58,60,0.08)]"
                  style={{ borderWidth: "1.5px" }}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full h-11 mt-1 bg-[#3A3A3C] text-white text-[15px] font-bold rounded-[10px] transition-all hover:bg-[#2c2c2e] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(0,0,0,0.2)] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {loading ? "Sending…" : "Send reset link"}
              </button>
            </form>
          </>
        )}
      </div>
    </>
  );
}
