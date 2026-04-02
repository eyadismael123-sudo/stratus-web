"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";

function PasswordStrength({ password }: { password: string }) {
  const score =
    (password.length >= 8 ? 1 : 0) +
    (/[A-Z]/.test(password) ? 1 : 0) +
    (/[0-9]/.test(password) ? 1 : 0) +
    (/[^A-Za-z0-9]/.test(password) ? 1 : 0);

  const colors = ["#D2D2D7", "#FF3B30", "#FF9F0A", "#34C759", "#34C759"];

  return (
    <div className="flex gap-1 mt-2">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="flex-1 h-[3px] rounded-full transition-colors duration-300"
          style={{ background: i <= score ? colors[score] : "#D2D2D7" }}
        />
      ))}
    </div>
  );
}

export default function SignUpPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: name },
      },
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    setSuccess(true);
    setLoading(false);
  }

  if (success) {
    return (
      <>
        <Link
          href="/"
          className="fixed top-6 left-8 text-[20px] font-black tracking-[-0.04em] text-[#3A3A3C] no-underline z-10"
        >
          Stratus
        </Link>
        <div
          className="w-full max-w-[440px] bg-white rounded-[16px] p-10 text-center"
          style={{
            boxShadow: "0 20px 60px rgba(0,0,0,0.10), 0 8px 20px rgba(0,0,0,0.06)",
          }}
        >
          <div className="w-14 h-14 rounded-full bg-[#34C759]/10 flex items-center justify-center mx-auto mb-5">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#34C759" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h2 className="text-[22px] font-black text-[#3A3A3C] tracking-[-0.03em] mb-2">
            Check your email
          </h2>
          <p className="text-[14px] text-[#6A6A6E] leading-relaxed">
            We sent a confirmation link to <strong className="text-[#3A3A3C]">{email}</strong>.
            Click it to activate your account.
          </p>
          <Link
            href="/auth/signin"
            className="inline-block mt-6 text-[13px] font-semibold text-[#3A3A3C] no-underline hover:underline"
          >
            Back to sign in
          </Link>
        </div>
      </>
    );
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
          Hire your first agent
        </h1>
        <p className="text-[14px] text-[#6A6A6E] mb-7 leading-relaxed">
          Create your Stratus account. Free to start.
        </p>

        {error && (
          <div className="mb-5 px-4 py-3 rounded-[10px] bg-red-50 border border-red-200 text-[13px] text-red-600 font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Full name */}
          <div>
            <label className="block text-[13px] font-semibold text-[#3A3A3C] mb-1.5 tracking-[-0.01em]">
              Full name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Rashid Al Mansoori"
              className="w-full h-11 text-[15px] text-[#3A3A3C] bg-[#FAFAFA] border border-[#D2D2D7] rounded-[10px] px-3.5 outline-none transition-all placeholder:text-[#A8A8AD] hover:border-[#AEAEB2] hover:bg-white focus:border-[#3A3A3C] focus:bg-white focus:shadow-[0_0_0_3px_rgba(58,58,60,0.08)]"
              style={{ borderWidth: "1.5px" }}
            />
          </div>

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
            <label className="block text-[13px] font-semibold text-[#3A3A3C] mb-1.5 tracking-[-0.01em]">
              Password{" "}
              <span className="font-normal text-[12px] text-[#6A6A6E]">min. 8 characters</span>
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                minLength={8}
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
            {password && <PasswordStrength password={password} />}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full h-11 mt-1 bg-[#3A3A3C] text-white text-[15px] font-bold rounded-[10px] transition-all hover:bg-[#2c2c2e] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(0,0,0,0.2)] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        {/* Sign in link */}
        <p className="mt-5 text-center text-[13px] text-[#6A6A6E]">
          Already have an account?{" "}
          <Link
            href="/auth/signin"
            className="font-semibold text-[#3A3A3C] no-underline hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </>
  );
}
