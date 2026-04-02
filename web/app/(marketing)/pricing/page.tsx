import type { Metadata } from "next";
import PricingHero from "@/components/pages/pricing/PricingHero";
import PricingCards from "@/components/pages/pricing/PricingCards";
import AgentPricingTable from "@/components/pages/pricing/AgentPricingTable";
import PricingFAQ from "@/components/pages/pricing/PricingFAQ";

export const metadata: Metadata = {
  title: "Pricing — Stratus",
  description:
    "One agent. One price. No surprises. Start at $50/month with no setup fee.",
};

export default function PricingPage() {
  return (
    <>
      <PricingHero />
      <PricingCards />
      <AgentPricingTable />
      <PricingFAQ />
    </>
  );
}
