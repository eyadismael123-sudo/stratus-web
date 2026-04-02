import { notFound } from "next/navigation";
import { MOCK_AGENT_TEMPLATES } from "@/constants/mock-data";
import AgentHero from "@/components/pages/agent-detail-marketing/AgentHero";
import AgentBenefits from "@/components/pages/agent-detail-marketing/AgentBenefits";
import HowItWorks from "@/components/pages/agent-detail-marketing/HowItWorks";
import AgentPricingCTA from "@/components/pages/agent-detail-marketing/AgentPricingCTA";
import RelatedAgents from "@/components/pages/agent-detail-marketing/RelatedAgents";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return MOCK_AGENT_TEMPLATES.map((t) => ({ slug: t.slug }));
}

export async function generateMetadata({ params }: PageProps) {
  const { slug } = await params;
  const template = MOCK_AGENT_TEMPLATES.find((t) => t.slug === slug);
  if (!template) return {};
  return {
    title: `${template.name} — Stratus`,
    description: template.description,
  };
}

export default async function AgentDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const template = MOCK_AGENT_TEMPLATES.find((t) => t.slug === slug);

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
