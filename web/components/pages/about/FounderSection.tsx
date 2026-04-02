export default function FounderSection() {
  return (
    <section className="py-32 px-8 overflow-hidden bg-[#FAF9F6]">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-12 gap-0 items-center">
          <div className="md:col-span-7 z-10">
            <div
              className="bg-white p-12 md:p-24 rounded-xl"
              style={{ boxShadow: "0 12px 32px rgba(27,67,50,0.04)" }}
            >
              <h3 className="text-3xl md:text-4xl font-black font-display mb-8 text-[#1a1c1a]">
                Agents as Colleagues
              </h3>
              <div className="space-y-6 text-lg text-[#414844] leading-loose">
                <p>
                  We are redefining the &ldquo;SaaS&rdquo; model. We don&apos;t
                  sell tools; we provision talent. Our AI agents are designed to
                  behave as integral team members—supporting both Arabic and
                  English markets with cultural nuance and linguistic precision.
                </p>
                <p>
                  Whether it&apos;s managing complex logistics across
                  border-free trade zones or providing localized customer
                  support during Ramadan, Stratus agents understand the context,
                  not just the code.
                </p>
              </div>
            </div>
          </div>
          <div className="md:col-span-5 -ml-4 md:-ml-20 mt-12 md:mt-0">
            <div className="aspect-[4/5] rounded-xl bg-[#1b4332] overflow-hidden" />
          </div>
        </div>
      </div>
    </section>
  );
}
