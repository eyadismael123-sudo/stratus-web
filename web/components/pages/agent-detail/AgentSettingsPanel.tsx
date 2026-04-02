"use client";

import { useState } from "react";
import type { UserAgent } from "@/types";

interface ToggleProps {
  checked: boolean;
  onChange: (v: boolean) => void;
}

function Toggle({ checked, onChange }: ToggleProps) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className="w-10 h-6 rounded-full relative flex-shrink-0 transition-colors duration-150 border-none cursor-pointer"
      style={{ background: checked ? "#3A3A3C" : "#D2D2D7" }}
      aria-pressed={checked}
    >
      <span
        className="absolute top-[3px] w-[18px] h-[18px] bg-white rounded-full shadow-[0_1px_3px_rgba(0,0,0,0.2)] transition-transform duration-150"
        style={{ transform: checked ? "translateX(19px)" : "translateX(3px)" }}
      />
    </button>
  );
}

interface AgentSettingsPanelProps {
  agent: UserAgent;
}

export function AgentSettingsPanel({ agent }: AgentSettingsPanelProps) {
  const voiceConfig = agent.config as {
    voice_profile?: string;
    post_time?: string;
    timezone?: string;
    linkedin_profile_url?: string;
    [key: string]: unknown;
  };

  const [notifications, setNotifications] = useState({
    morning_briefing: true,
    post_published: true,
    error_alerts: true,
    weekly_summary: false,
  });

  const [voiceTone, setVoiceTone] = useState(voiceConfig.voice_profile ?? "");
  const [postTime, setPostTime] = useState(voiceConfig.post_time ?? "08:00");
  const [saved, setSaved] = useState(false);

  function handleSave() {
    // In production: PATCH /api/agents/:id with updated config
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function updateNotification(key: keyof typeof notifications, value: boolean) {
    setNotifications((prev) => ({ ...prev, [key]: value }));
  }

  const NOTIFICATION_ITEMS = [
    {
      key: "morning_briefing" as const,
      title: "Morning Briefing",
      desc: "Receive post ideas at scheduled time",
    },
    {
      key: "post_published" as const,
      title: "Post Published",
      desc: "Notify when post goes live",
    },
    {
      key: "error_alerts" as const,
      title: "Error Alerts",
      desc: "Alert if agent fails or encounters errors",
    },
    {
      key: "weekly_summary" as const,
      title: "Weekly Summary",
      desc: "Performance recap every Sunday",
    },
  ];

  return (
    <div className="flex flex-col gap-5">
      {/* Notifications Card */}
      <div className="bg-white rounded-[12px] p-[18px] border border-black/[0.06] shadow-[0_1px_3px_rgba(0,0,0,0.06)]">
        <div className="flex items-center gap-2 text-[13px] font-bold text-[#3A3A3C] mb-3.5">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M7 1.5c-2.76 0-5 2.24-5 5v2.5l-1 1.5h12l-1-1.5V6.5c0-2.76-2.24-5-5-5z"/>
            <path d="M5.5 11.5a1.5 1.5 0 003 0"/>
          </svg>
          Notifications
        </div>
        <div>
          {NOTIFICATION_ITEMS.map(({ key, title, desc }, i) => (
            <div
              key={key}
              className="flex items-center justify-between py-2.5"
              style={{ borderBottom: i < NOTIFICATION_ITEMS.length - 1 ? "1px solid rgba(0,0,0,0.04)" : "none" }}
            >
              <div>
                <div className="text-[13px] font-semibold text-[#3A3A3C]">{title}</div>
                <div className="text-[11px] text-[#8E8E93] mt-0.5">{desc}</div>
              </div>
              <Toggle
                checked={notifications[key]}
                onChange={(v) => updateNotification(key, v)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Voice Profile Card */}
      <div className="bg-white rounded-[12px] p-[18px] border border-black/[0.06] shadow-[0_1px_3px_rgba(0,0,0,0.06)]">
        <div className="flex items-center gap-2 text-[13px] font-bold text-[#3A3A3C] mb-3.5">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M7 1.5a2 2 0 012 2v4a2 2 0 01-4 0v-4a2 2 0 012-2z"/>
            <path d="M3.5 6.5a3.5 3.5 0 007 0M7 10v2.5M5 12.5h4"/>
          </svg>
          Settings
        </div>

        <div className="flex flex-col gap-3 mb-3">
          <div>
            <label className="block text-[11px] font-semibold text-[#8E8E93] mb-1.5 tracking-[0.3px]">
              Voice Profile
            </label>
            <textarea
              value={voiceTone}
              onChange={(e) => setVoiceTone(e.target.value)}
              placeholder="Describe the tone and style..."
              className="w-full h-20 rounded-[8px] border border-[#D2D2D7] bg-white px-3 py-2.5 text-[12px] text-[#3A3A3C] leading-relaxed resize-none outline-none transition-colors focus:border-[#3A3A3C]"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-[#8E8E93] mb-1.5 tracking-[0.3px]">
              Run Time
            </label>
            <input
              type="time"
              value={postTime}
              onChange={(e) => setPostTime(e.target.value)}
              className="w-full h-9 rounded-[8px] border border-[#D2D2D7] bg-white px-3 text-[13px] text-[#3A3A3C] outline-none transition-colors focus:border-[#3A3A3C]"
            />
          </div>
        </div>

        <button
          onClick={handleSave}
          className="w-full h-9 rounded-[8px] text-[13px] font-bold text-white transition-all flex items-center justify-center"
          style={{ background: saved ? "#34C759" : "#3A3A3C" }}
        >
          {saved ? "Saved ✓" : "Save Settings"}
        </button>
      </div>

      {/* Danger Zone */}
      <div className="rounded-[12px] p-3.5 border border-[rgba(255,59,48,0.2)] bg-[rgba(255,59,48,0.02)]">
        <div className="text-[11px] font-bold text-[#FF3B30] uppercase tracking-[0.5px] mb-2.5">
          ⚠ Danger Zone
        </div>
        {[
          { label: "Pause Agent", desc: "Stop all scheduled runs" },
          { label: "Reset Settings", desc: "Clears all custom configuration" },
          { label: "Cancel Subscription", desc: "Removes agent from your team" },
        ].map(({ label, desc }, i, arr) => (
          <div
            key={label}
            className="flex items-center justify-between py-2.5"
            style={{ borderBottom: i < arr.length - 1 ? "1px solid rgba(255,59,48,0.1)" : "none" }}
          >
            <div>
              <div className="text-[12px] font-medium text-[#3A3A3C]">{label}</div>
              <div className="text-[11px] text-[#8E8E93]">{desc}</div>
            </div>
            <button className="px-3 py-1 rounded-[6px] text-[12px] font-semibold text-[#FF3B30] border border-[rgba(255,59,48,0.3)] bg-transparent transition-all hover:bg-[#FFF1F0] hover:border-[#FF3B30] cursor-pointer whitespace-nowrap">
              {label.split(" ")[0]}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
