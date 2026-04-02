import type { Metadata } from "next";
import AboutHero from "@/components/pages/about/AboutHero";
import MissionSection from "@/components/pages/about/MissionSection";
import FounderSection from "@/components/pages/about/FounderSection";
import VisionSection from "@/components/pages/about/VisionSection";

export const metadata: Metadata = {
  title: "About — Stratus",
  description:
    "Built for the businesses shaping MENA. The story behind Stratus.",
};

export default function AboutPage() {
  return (
    <>
      <AboutHero />
      <MissionSection />
      <FounderSection />
      <VisionSection />
    </>
  );
}
