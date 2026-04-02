// Landing page — root route, uses root layout only (no marketing Header — dark nav is inside HeroSection)

import { HeroSection } from "@/components/pages/landing/HeroSection";
import { LogoStrip } from "@/components/pages/landing/LogoStrip";
import { StatsStrip } from "@/components/pages/landing/StatsStrip";
import { TickerSection } from "@/components/pages/landing/TickerSection";
import { HireWatchGrowTabs } from "@/components/pages/landing/HireWatchGrowTabs";
import { TeamWorkflowSection } from "@/components/pages/landing/TeamWorkflowSection";
import { BentoGrid } from "@/components/pages/landing/BentoGrid";
import { MemorySection } from "@/components/pages/landing/MemorySection";
import { EditorialBreak } from "@/components/pages/landing/EditorialBreak";
import { PricingSection } from "@/components/pages/landing/PricingSection";
import { FinalCTASection } from "@/components/pages/landing/FinalCTASection";
import { WaitlistSection } from "@/components/pages/landing/WaitlistSection";
import { Footer } from "@/components/layouts/Footer";

export default function LandingPage() {
  return (
    <>
      <HeroSection />
      <LogoStrip />
      <StatsStrip />
      <TickerSection />
      <HireWatchGrowTabs />
      <TeamWorkflowSection />
      <BentoGrid />
      <MemorySection />
      <EditorialBreak />
      <PricingSection />
      <FinalCTASection />
      <WaitlistSection />
      <Footer />
    </>
  );
}
