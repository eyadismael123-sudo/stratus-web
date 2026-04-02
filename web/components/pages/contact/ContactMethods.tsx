const METHODS = [
  {
    emoji: "💬",
    bg: "bg-emerald-100",
    title: "Message us on WhatsApp",
    description:
      "Instant response. Best for quick inquiries and immediate support from our MENA team.",
    cta: "Start Chat",
    ctaStyle:
      "bg-[#012d1d] text-white hover:bg-[#1b4332]",
    href: "https://wa.me/97337646913",
    external: true,
  },
  {
    emoji: "✉️",
    bg: "bg-[#c1ecd4]",
    title: "Email us",
    description:
      "Prefer formal communication? Send us a detailed brief of your requirements.",
    cta: "hello@stratus.ai",
    ctaStyle: "text-[#012d1d] font-bold text-xl hover:underline",
    href: "mailto:hello@stratus.ai",
    external: false,
    isLink: true,
  },
  {
    emoji: "📅",
    bg: "bg-[#d5e7db]",
    title: "Book a call",
    description:
      "Schedule a 20-min intro call with our team to discuss your roadmap.",
    cta: "View Calendar",
    ctaStyle:
      "bg-[#e9e8e5] text-[#012d1d] hover:bg-[#c1ecd4]",
    href: "#",
    external: false,
  },
];

export default function ContactMethods() {
  return (
    <>
      {/* Contact Options */}
      <section className="py-24 px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {METHODS.map((method) => (
            <div
              key={method.title}
              className="bg-[#f4f3f1] p-10 rounded-xl flex flex-col items-start gap-6 hover:-translate-y-1 transition-transform"
              style={{ boxShadow: "0 8px 32px -4px rgba(1,45,29,0.04)" }}
            >
              <div
                className={`w-14 h-14 rounded-full ${method.bg} flex items-center justify-center text-2xl`}
              >
                {method.emoji}
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-[#1a1c1a] mb-3">
                  {method.title}
                </h3>
                <p className="text-[#414844] leading-relaxed mb-4">
                  {method.description}
                </p>
                {method.isLink ? (
                  <a href={method.href} className={method.ctaStyle}>
                    {method.cta}
                  </a>
                ) : null}
              </div>
              {!method.isLink && (
                <a
                  href={method.href}
                  className={`${method.ctaStyle} px-8 py-3 rounded-xl font-bold w-full text-center transition-colors`}
                  {...(method.external
                    ? { target: "_blank", rel: "noopener noreferrer" }
                    : {})}
                >
                  {method.cta}
                </a>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Contact Form */}
      <section className="py-32 px-8 max-w-7xl mx-auto">
        <div className="bg-[#f4f3f1] rounded-xl overflow-hidden grid grid-cols-1 lg:grid-cols-2">
          <div className="relative h-64 lg:h-auto min-h-[400px] bg-[#1b4332] flex flex-col justify-end p-12">
            <h2 className="text-4xl font-display font-bold text-white mb-4">
              Direct Message
            </h2>
            <p className="text-lg text-white/90 leading-relaxed">
              Fill out the form and our team will get back to you within 4
              business hours.
            </p>
          </div>
          <div className="p-12 md:p-20 bg-white">
            <form className="space-y-10">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div>
                  <label className="text-xs font-body uppercase tracking-widest text-[#414844] mb-2 block">
                    Name
                  </label>
                  <input
                    type="text"
                    placeholder="Your full name"
                    className="w-full bg-transparent border-0 border-b-2 border-[#c1c8c2] focus:border-[#012d1d] focus:outline-none transition-all py-3 px-0 text-[#1a1c1a] placeholder:text-[#c1c8c2]"
                  />
                </div>
                <div>
                  <label className="text-xs font-body uppercase tracking-widest text-[#414844] mb-2 block">
                    Company
                  </label>
                  <input
                    type="text"
                    placeholder="Company name"
                    className="w-full bg-transparent border-0 border-b-2 border-[#c1c8c2] focus:border-[#012d1d] focus:outline-none transition-all py-3 px-0 text-[#1a1c1a] placeholder:text-[#c1c8c2]"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-body uppercase tracking-widest text-[#414844] mb-2 block">
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="email@company.com"
                  className="w-full bg-transparent border-0 border-b-2 border-[#c1c8c2] focus:border-[#012d1d] focus:outline-none transition-all py-3 px-0 text-[#1a1c1a] placeholder:text-[#c1c8c2]"
                />
              </div>
              <div>
                <label className="text-xs font-body uppercase tracking-widest text-[#414844] mb-2 block">
                  Message
                </label>
                <textarea
                  placeholder="How can we help?"
                  rows={4}
                  className="w-full bg-transparent border-0 border-b-2 border-[#c1c8c2] focus:border-[#012d1d] focus:outline-none transition-all py-3 px-0 text-[#1a1c1a] placeholder:text-[#c1c8c2] resize-none"
                />
              </div>
              <button
                type="submit"
                className="bg-[#012d1d] text-white px-12 py-4 rounded-xl font-bold text-lg hover:bg-[#1b4332] transition-all w-full md:w-auto"
              >
                Send Message
              </button>
            </form>
          </div>
        </div>
      </section>
    </>
  );
}
