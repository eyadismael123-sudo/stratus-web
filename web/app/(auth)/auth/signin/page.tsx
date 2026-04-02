"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    router.push("/dashboard");
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

      {/* Auth card */}
      <div
        className="w-full max-w-[440px] bg-white rounded-[16px] p-10"
        style={{
          boxShadow: "0 20px 60px rgba(0,0,0,0.10), 0 8px 20px rgba(0,0,0,0.06)",
        }}
      >
        <h1
          className="font-black text-[#3A3A3C] tracking-[-0.035em] leading-[1.15] mb-1.5"
          style={{ fontSize: "clamp(22px, 4vw, 26px)" }}
        >
          Welcome back
        </h1>
        <p className="text-[14px] text-[#6A6A6E] mb-7 leading-relaxed">
          Sign in to your Stratus account.
        </p>

        {error && (
          <div className="mb-5 px-4 py-3 rounded-[10px] bg-red-50 border border-red-200 text-[13px] text-red-600 font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Email */}
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

          {/* Password */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-[13px] font-semibold text-[#3A3A3C] tracking-[-0.01em]">
                Password
              </label>
              <Link
                href="/auth/reset"
                className="text-[12px] text-[#6A6A6E] no-underline hover:text-[#3A3A3C] transition-colors"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full h-11 text-[15px] text-[#3A3A3C] bg-[#FAFAFA] border border-[#D2D2D7] rounded-[10px] pl-3.5 pr-10 outline-none transition-all placeholder:text-[#A8A8AD] hover:border-[#AEAEB2] hover:bg-white focus:border-[#3A3A3C] focus:bg-white focus:shadow-[0_0_0_3px_rgba(58,58,60,0.08)]"
                style={{ borderWidth: "1.5px" }}
              />
              <button
                type="button"
                onClick={() => setShowPassword((p) => !p)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6A6A6E] hover:text-[#3A3A3C] transition-colors p-1"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
                    <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full h-11 mt-1 bg-[#3A3A3C] text-white text-[15px] font-bold rounded-[10px] transition-all hover:bg-[#2c2c2e] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(0,0,0,0.2)] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3 my-5">
          <div className="flex-1 h-px bg-[#D2D2D7]" />
          <span className="text-[12px] font-medium text-[#6A6A6E]">or</span>
          <div className="flex-1 h-px bg-[#D2D2D7]" />
        </div>

        {/* Sign up link */}
        <p className="text-center text-[13px] text-[#6A6A6E]">
          Don&apos;t have an account?{" "}
          <Link
            href="/auth/signup"
            className="font-semibold text-[#3A3A3C] no-underline hover:underline"
          >
            Sign up
          </Link>
        </p>
      </div>
    </>
  );
}
