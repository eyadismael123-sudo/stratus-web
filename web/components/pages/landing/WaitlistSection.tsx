"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function WaitlistSection() {
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const email = (e.currentTarget.elements.namedItem("email") as HTMLInputElement).value;
    try {
      const res = await fetch(`${API_URL}/waitlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error("Failed");
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      className="py-20 px-6 text-center"
      style={{ background: "#1B4332" }}
    >
      <div className="max-w-[560px] mx-auto">
        <div
          className="inline-block text-[12px] font-semibold tracking-[0.1em] uppercase px-4 py-1.5 rounded-full mb-6"
          style={{ background: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.8)" }}
        >
          New agents dropping soon
        </div>

        <h2
          className="font-display font-bold tracking-[-0.03em] leading-[1.1] mb-4"
          style={{ fontSize: "clamp(32px, 4vw, 48px)", color: "#FAF9F6" }}
        >
          Be first in line.
        </h2>

        <p className="text-[18px] leading-relaxed mb-10" style={{ color: "rgba(250,249,246,0.7)" }}>
          Flash, Focus, Develop and Shutter are coming soon. Drop your email and we&apos;ll notify you the moment they go live.
        </p>

        {submitted ? (
          <p className="text-[18px] font-semibold" style={{ color: "#FAF9F6" }}>
            You&apos;re on the list. We&apos;ll be in touch.
          </p>
        ) : (
          <>
            <form
              onSubmit={handleSubmit}
              className="flex gap-3 max-w-[440px] mx-auto flex-wrap"
            >
              <input
                type="email"
                name="email"
                placeholder="Your email address"
                required
                disabled={loading}
                className="flex-1 min-w-[220px] px-[18px] py-[14px] rounded-[10px] text-[15px] outline-none disabled:opacity-60"
                style={{
                  background: "#FAF9F6",
                  color: "#1A1A1A",
                  border: "none",
                  fontFamily: "inherit",
                }}
              />
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-[14px] rounded-[10px] text-[15px] font-bold whitespace-nowrap transition-all hover:bg-[#E8E6E1] disabled:opacity-60"
                style={{
                  background: "#FAF9F6",
                  color: "#1B4332",
                  border: "none",
                  fontFamily: "inherit",
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {loading ? "Joining..." : "Join Waitlist"}
              </button>
            </form>
            {error && (
              <p className="text-[13px] mt-3" style={{ color: "rgba(250,100,100,0.9)" }}>
                {error}
              </p>
            )}
          </>
        )}

        <p className="text-[12px] mt-4" style={{ color: "rgba(250,249,246,0.4)" }}>
          No spam. Just a heads-up when your agent is ready.
        </p>
      </div>
    </section>
  );
}
