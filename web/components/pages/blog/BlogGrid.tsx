const FEATURED_POST = {
  category: "Latest Analysis",
  title: "Why MENA businesses need AI employees, not AI tools",
  excerpt:
    "In the rapidly evolving landscape of Riyadh and Dubai, the shift from static software to autonomous agents is no longer optional.",
  date: "JAN 15, 2026",
  read: "5 MIN READ",
};

const POSTS = [
  {
    category: "Product Insights",
    title: "How the LinkedIn Post Agent writes in your voice",
    excerpt: "Mastering the art of authentic digital presence through regional-specific AI training.",
    date: "JAN 12, 2026",
    read: "3 MIN READ",
  },
  {
    category: "Workflow",
    title: "Morning briefings: your AI team starts at 8am",
    excerpt: "Start your day with a comprehensive overview of autonomous tasks completed overnight.",
    date: "JAN 08, 2026",
    read: "4 MIN READ",
  },
  {
    category: "Strategy",
    title: "Hiring your first AI employee: a guide",
    excerpt: "Key considerations for MENA startups when integrating autonomous agents into their core team.",
    date: "JAN 05, 2026",
    read: "6 MIN READ",
  },
  {
    category: "Localization",
    title: "Arabic + English: building agents for both markets",
    excerpt: "How Stratus bridges the linguistic gap to deliver seamless service across the GCC.",
    date: "DEC 28, 2025",
    read: "4 MIN READ",
  },
  {
    category: "Future Outlook",
    title: "The future of work in Dubai and Riyadh",
    excerpt: "Forecasting the economic impact of the autonomous workforce in the region's leading hubs.",
    date: "DEC 20, 2025",
    read: "5 MIN READ",
  },
];

export default function BlogGrid() {
  return (
    <>
      {/* Featured post */}
      <section className="max-w-7xl mx-auto px-8 mb-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 bg-[#f4f3f1] rounded-xl overflow-hidden h-[500px]" />
          <div className="lg:col-span-5">
            <span className="inline-block bg-[#1B43321A] text-[#1b4332] px-3 py-1 rounded text-sm font-bold mb-6">
              {FEATURED_POST.category.toUpperCase()}
            </span>
            <h2 className="text-4xl font-display font-black leading-tight mb-4 text-[#1a1c1a]">
              {FEATURED_POST.title}
            </h2>
            <p className="text-[#414844] mb-8 text-lg">{FEATURED_POST.excerpt}</p>
            <div className="flex items-center gap-4 text-xs font-bold text-[#414844]/60">
              <span>{FEATURED_POST.date}</span>
              <span className="w-1 h-1 bg-[#c1c8c2] rounded-full" />
              <span>{FEATURED_POST.read}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Article grid */}
      <section className="max-w-7xl mx-auto px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-20">
          {POSTS.map((post) => (
            <article key={post.title} className="group">
              <div className="mb-6 bg-[#f4f3f1] rounded-lg overflow-hidden h-80" />
              <span className="text-[#1b4332] text-xs font-black tracking-widest uppercase mb-4 block">
                {post.category}
              </span>
              <h3 className="text-2xl font-display font-bold mb-3 text-[#1a1c1a] group-hover:text-[#1b4332] transition-colors">
                {post.title}
              </h3>
              <p className="text-[#414844] line-clamp-1 mb-4">{post.excerpt}</p>
              <div className="flex items-center gap-4 text-xs font-bold text-[#414844]/60">
                <span>{post.date}</span>
                <span>{post.read}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Newsletter */}
      <section className="max-w-7xl mx-auto px-8 mt-40 mb-24">
        <div className="bg-[#1b4332] rounded-xl p-16 relative overflow-hidden">
          <div className="relative z-10 max-w-xl">
            <h2 className="text-white text-5xl font-display font-black mb-6 leading-tight">
              Stay rooted in the future.
            </h2>
            <p className="text-[#86af99] text-lg mb-10">
              Weekly insights on the autonomous workforce in MENA, delivered with editorial precision.
            </p>
            <div className="flex flex-col md:flex-row gap-4">
              <input
                type="email"
                placeholder="Your email address"
                className="flex-1 bg-white/10 border-none text-white placeholder-white/50 px-6 py-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/20"
              />
              <button className="bg-[#FAF9F6] text-[#1b4332] font-black px-8 py-4 rounded-lg hover:bg-white transition-colors">
                SUBSCRIBE
              </button>
            </div>
          </div>
          <div className="absolute right-0 top-0 h-full w-1/2 bg-gradient-to-l from-[#012D1D] to-transparent opacity-50 pointer-events-none" />
        </div>
      </section>
    </>
  );
}
