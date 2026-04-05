import AboutVisual from "./AboutVisual";

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
                Hire once. Show up every day.
              </h3>
              <div className="space-y-6 text-lg text-[#414844] leading-loose">
                <p>
                  We don&apos;t sell software. We hire out people — agents that
                  do real work, on a schedule, without being asked twice. The
                  kind of team member you wish you could afford at the start.
                </p>
                <p>
                  Each agent is built for a specific job in a specific market.
                  Not a general tool you have to configure — something that
                  already knows the context and gets on with it.
                </p>
              </div>
            </div>
          </div>
          <div className="md:col-span-5 -ml-4 md:-ml-20 mt-12 md:mt-0">
            <div className="aspect-[4/5]">
              <AboutVisual />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
