import { notFound } from "next/navigation";
import type { AgentTemplate } from "@/types";
import AgentHero from "@/components/pages/agent-detail-marketing/AgentHero";
import AgentBenefits from "@/components/pages/agent-detail-marketing/AgentBenefits";
import HowItWorks from "@/components/pages/agent-detail-marketing/HowItWorks";
import AgentPricingCTA from "@/components/pages/agent-detail-marketing/AgentPricingCTA";
import RelatedAgents from "@/components/pages/agent-detail-marketing/RelatedAgents";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface PageProps {
  params: Promise<{ slug: string }>;
}

async function fetchTemplate(slug: string): Promise<AgentTemplate | null> {
  try {
    const res = await fetch(`${API_URL}/marketplace/agents/${slug}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    const json = await res.json();
    return json.data ?? null;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: PageProps) {
  const { slug } = await params;
  const template = await fetchTemplate(slug);
  if (!template) return {};
  return {
    title: `${template.name} — Stratus`,
    description: template.description,
  };
}

export default async function AgentDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const template = await fetchTemplate(slug);

  if (!template) {
    notFound();
  }

  return (
    <>
      <AgentHero template={template} />
      <AgentBenefits template={template} />
      <HowItWorks />
      <AgentPricingCTA template={template} />
      <RelatedAgents currentSlug={slug} />
    </>
  );
}
