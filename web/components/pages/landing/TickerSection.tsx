const TICKER_ITEMS = [
  "Frame → Drafted \"AI trends in Gulf pharma\" for Ahmad",
  "Flash → Found 3 underpriced listings in JVC",
  "Frame → Morning briefing sent to 1 client",
  "Focus → Pulled 5 clinical updates from PubMed",
  "Flash → Price drop alert: 2015 Camry, Al Quoz — AED 28k",
  "Frame → Post reached 847 impressions on LinkedIn",
];

export function TickerSection() {
  const items = [...TICKER_ITEMS, ...TICKER_ITEMS];

  return (
    <div
      className="overflow-hidden py-3"
      style={{
        background: "#1B4332",
        borderTop: "1px solid rgba(255,255,255,0.08)",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <style>{`
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .ticker-track {
          display: flex;
          width: max-content;
          animation: ticker 40s linear infinite;
        }
      `}</style>
      <div className="ticker-track">
        {items.map((item, i) => (
          <div
            key={i}
            className="flex items-center gap-10 px-10 text-[12px] font-bold whitespace-nowrap"
            style={{ color: "rgba(161,210,185,0.7)" }}
          >
            <span>
              <span style={{ color: "#10b981" }}>●</span>{" "}
              {item}
            </span>
            <span style={{ color: "rgba(161,210,185,0.3)" }}>·</span>
          </div>
        ))}
      </div>
    </div>
  );
}
