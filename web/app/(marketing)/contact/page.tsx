import type { Metadata } from "next";
import ContactHero from "@/components/pages/contact/ContactHero";
import ContactMethods from "@/components/pages/contact/ContactMethods";

export const metadata: Metadata = {
  title: "Contact — Stratus",
  description: "Get in touch with the Stratus team via WhatsApp, email, or book a call.",
};

export default function ContactPage() {
  return (
    <>
      <ContactHero />
      <ContactMethods />
    </>
  );
}
