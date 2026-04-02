"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";

const FAQ_ITEMS = [
  {
    question: "Can I hire multiple agents?",
    answer:
      "Yes, you can hire as many specialized agents as your business needs. Each agent is priced at a flat $50/month and functions as a dedicated member of your digital workforce.",
  },
  {
    question: "What happens if I cancel?",
    answer:
      "Stratus operates on a month-to-month basis. If you cancel, your agent will finish their current billing cycle and will not renew. You retain all content previously generated.",
  },
  {
    question: "Is there a setup fee?",
    answer:
      "Absolutely not. We believe in honest pricing. You pay only for the agents you use, with no hidden implementation or onboarding costs.",
  },
  {
    question: "Do you support Arabic?",
    answer:
      "Yes. Stratus is designed with a MENA-first mindset. Our agents are natively fluent in multiple dialects of Arabic as well as professional English.",
  },
  {
    question: "What markets do you serve?",
    answer:
      "While our platform is global, our agents are specifically tuned for the unique cultural and business landscapes of the GCC, Levant, and North African markets.",
  },
];

export default function PricingFAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  function toggle(i: number) {
    setOpenIndex((prev) => (prev === i ? null : i));
  }

  return (
    <>
      {/* FAQ */}
      <section className="max-w-4xl mx-auto px-8 py-32">
        <h2 className="font-display text-4xl font-bold text-[#012d1d] mb-16 text-center">
          Frequently Asked Questions
        </h2>
        <div className="space-y-4">
          {FAQ_ITEMS.map((item, i) => (
            <div
              key={item.question}
              className="bg-white p-6 rounded-lg hover:border-b hover:border-[#c1c8c2]/20 transition-all"
              style={{ boxShadow: "0 30px 60px -12px rgba(26,28,26,0.05)" }}
            >
              <button
                onClick={() => toggle(i)}
                className="w-full flex justify-between items-center cursor-pointer text-left"
                aria-expanded={openIndex === i}
              >
                <h4 className="font-semibold text-lg text-[#1a1c1a]">
                  {item.question}
                </h4>
                <span className="text-[#012d1d] text-xl transition-transform duration-200 flex-shrink-0 ml-4">
                  {openIndex === i ? "−" : "+"}
                </span>
              </button>
              <AnimatePresence initial={false}>
                {openIndex === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <p className="mt-4 text-[#414844] leading-relaxed">
                      {item.answer}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="bg-[#1b4332] relative overflow-hidden py-24 mx-8 rounded-3xl mb-24">
        <div className="relative z-10 max-w-4xl mx-auto text-center">
          <h2 className="font-display text-4xl md:text-5xl font-extrabold text-white mb-10 px-4">
            Ready to hire your AI workforce?
          </h2>
          <Link
            href="/marketplace"
            className="inline-block bg-[#FAF9F6] text-[#1b4332] px-10 py-4 rounded-lg font-bold text-lg hover:bg-white transition-all"
          >
            Start Now
          </Link>
        </div>
      </section>
    </>
  );
}
