"use client";

import { useState } from "react";
import type { Subscription, UserAgent } from "@/types";
import { Modal, ModalFooter } from "@/components/common/Modal";

const CATEGORY_EMOJI: Record<string, string> = {
  Personal: "👤",
  Business: "🏢",
  Health: "🩺",
};

function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(0)}`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-AE", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

interface SubscriptionsTableProps {
  subscriptions: Subscription[];
  agents: UserAgent[];
}

export function SubscriptionsTable({ subscriptions, agents }: SubscriptionsTableProps) {
  const [cancelTarget, setCancelTarget] = useState<string | null>(null);

  const agentMap = new Map<string, UserAgent>(agents.map((a) => [a.id, a]));
  const active = subscriptions.filter((s) => s.status === "active");

  function handleCancelConfirm() {
    // In production: call API to cancel subscription
    setCancelTarget(null);
  }

  const cancelSub = cancelTarget ? subscriptions.find((s) => s.id === cancelTarget) : null;
  const cancelAgent = cancelSub ? agentMap.get(cancelSub.user_agent_id) : null;

  return (
    <>
      <div className="bg-white rounded-[12px] border border-black/[0.06] overflow-hidden"
        style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)" }}
      >
        {/* Table header */}
        <div className="px-6 py-4 border-b border-black/[0.06] flex items-center justify-between">
          <span className="text-[15px] font-bold text-[#3A3A3C]">Active Subscriptions</span>
          <span
            className="text-[11px] font-bold tracking-[0.5px] uppercase px-2.5 py-1 rounded-full"
            style={{ background: "rgba(52,199,89,0.1)", color: "#1a7d39" }}
          >
            {active.length} Active
          </span>
        </div>

        {/* Subscription rows */}
        {active.length === 0 ? (
          <div className="px-6 py-10 text-center text-[14px] text-[#8E8E93]">
            No active subscriptions.
          </div>
        ) : (
          <div className="divide-y divide-black/[0.04]">
            {active.map((sub) => {
              const agent = agentMap.get(sub.user_agent_id);
              const emoji = CATEGORY_EMOJI[agent?.agent_template?.category ?? ""] ?? "🤖";
              const isCancelling = sub.cancel_at_period_end;

              return (
                <div key={sub.id} className="px-6 py-4 flex items-center gap-4">
                  {/* Emoji */}
                  <span className="text-2xl flex-shrink-0">{emoji}</span>

                  {/* Agent info */}
                  <div className="flex-1 min-w-0">
                    <div className="text-[14px] font-semibold text-[#3A3A3C] truncate">
                      {agent?.name ?? "Unknown Agent"}
                    </div>
                    <div className="text-[12px] text-[#6A6A6E] mt-0.5">
                      Renews {formatDate(sub.current_period_end)}
                      {isCancelling && (
                        <span className="ml-2 text-[11px] font-medium text-[#FF3B30]">
                          · Cancels at period end
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Status badge */}
                  <span
                    className="text-[10px] font-bold tracking-[0.5px] uppercase px-2 py-0.5 rounded-full flex-shrink-0 hidden sm:block"
                    style={
                      isCancelling
                        ? { background: "rgba(255,59,48,0.08)", color: "#FF3B30" }
                        : { background: "rgba(52,199,89,0.1)", color: "#1a7d39" }
                    }
                  >
                    {isCancelling ? "Cancelling" : "Active"}
                  </span>

                  {/* Price */}
                  <div className="text-[14px] font-bold text-[#3A3A3C] flex-shrink-0 hidden sm:block">
                    {formatPrice(sub.amount_usd_cents)}
                    <span className="text-[12px] font-normal text-[#6A6A6E]">/mo</span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button className="h-[32px] px-3.5 rounded-[8px] text-[12px] font-semibold text-[#3A3A3C] bg-transparent border border-[#D2D2D7] transition-all hover:border-[#3A3A3C] cursor-pointer">
                      Manage
                    </button>
                    {!isCancelling && (
                      <button
                        onClick={() => setCancelTarget(sub.id)}
                        className="h-[32px] px-3.5 rounded-[8px] text-[12px] font-semibold text-[#FF3B30] bg-transparent border border-transparent transition-all hover:border-[#FF3B30]/30 hover:bg-[#FF3B30]/[0.04] cursor-pointer"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Add agent banner */}
        <div className="px-6 py-4 border-t border-black/[0.06] bg-[#F5F5F7] flex items-center justify-between">
          <span className="text-[13px] text-[#6A6A6E]">
            Need another agent for your business?
          </span>
          <a
            href="/marketplace"
            className="h-[32px] px-4 rounded-[8px] text-[12px] font-bold text-white bg-[#3A3A3C] flex items-center gap-1.5 transition-all hover:bg-[#2a2a2c] no-underline"
          >
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M8 3v10M3 8h10" />
            </svg>
            Browse Marketplace
          </a>
        </div>
      </div>

      {/* Cancel confirmation modal */}
      <Modal
        open={!!cancelTarget}
        onClose={() => setCancelTarget(null)}
        title="Cancel Subscription"
        description={`Are you sure you want to cancel ${cancelAgent?.name ?? "this agent"}? It will remain active until the end of your billing period.`}
      >
        <ModalFooter>
          <button
            onClick={() => setCancelTarget(null)}
            className="h-[38px] px-5 rounded-[8px] text-[13px] font-semibold text-[#6A6A6E] border border-[#D2D2D7] bg-white hover:border-[#3A3A3C] hover:text-[#3A3A3C] transition-all cursor-pointer"
          >
            Keep Subscription
          </button>
          <button
            onClick={handleCancelConfirm}
            className="h-[38px] px-5 rounded-[8px] text-[13px] font-bold text-white bg-[#FF3B30] hover:bg-[#e0352a] transition-all cursor-pointer border-none"
          >
            Yes, Cancel
          </button>
        </ModalFooter>
      </Modal>
    </>
  );
}
