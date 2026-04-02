"""Seed script — creates 5 agent templates per COFOUNDER-PROPOSAL.md."""

from app.db.connection import get_service_client

AGENT_TEMPLATES = [
    {
        "name": "LinkedIn Post Agent",
        "slug": "linkedin-post-agent",
        "description": "Writes thought leadership in your voice. Daily.",
        "long_description": (
            "Your personal LinkedIn ghostwriter. Captures your voice via Telegram, "
            "researches trending topics in your industry using real-time web intelligence, "
            "and generates 3 post variations every morning. Pick one, tap to post. "
            "Builds your personal brand while you focus on your work."
        ),
        "category": "personal",
        "role": "content_creator",
        "icon_url": "/icons/linkedin-post-agent.svg",
        "is_published": True,
        "is_featured": True,
        "price_usd_cents": 5000,
        "features": [
            "Daily voice-matched post generation",
            "Real-time industry trend research",
            "2 post variations to choose from",
            "One-tap LinkedIn posting via deep link",
            "Morning briefing with 3 topic ideas",
            "Telegram-based workflow",
        ],
        "requirements": [
            "LinkedIn account",
            "Telegram account",
            "5-minute voice onboarding",
        ],
        "industries": ["all"],
        "platforms": ["telegram", "linkedin"],
        "setup_time_minutes": 10,
    },
    {
        "name": "Car Reseller Morning Intel",
        "slug": "car-reseller-morning-intel",
        "description": "Underpriced cars found before your competitors wake up.",
        "long_description": (
            "Scans Dubai's car marketplaces overnight and delivers underpriced "
            "deals to your inbox before 8am. Filters by make, model, year, and "
            "margin potential. Your competitors are still sleeping."
        ),
        "category": "business",
        "role": "researcher",
        "icon_url": "/icons/car-reseller-intel.svg",
        "is_published": False,
        "is_featured": False,
        "price_usd_cents": 5000,
        "features": [
            "Overnight marketplace scanning",
            "Underpriced deal detection",
            "Margin potential calculation",
            "Daily morning briefing",
            "Custom make/model filters",
        ],
        "requirements": ["Telegram account"],
        "industries": ["automotive", "resale"],
        "platforms": ["telegram"],
        "setup_time_minutes": 5,
    },
    {
        "name": "Property Market Briefing",
        "slug": "property-market-briefing",
        "description": "Dubai real estate moves. In your inbox at 8am.",
        "long_description": (
            "Tracks Dubai real estate listings, price changes, and market signals. "
            "Delivers a concise morning briefing with new opportunities, price drops, "
            "and market trends relevant to your portfolio focus areas."
        ),
        "category": "business",
        "role": "researcher",
        "icon_url": "/icons/property-briefing.svg",
        "is_published": False,
        "is_featured": False,
        "price_usd_cents": 5000,
        "features": [
            "Dubai property market monitoring",
            "Price drop alerts",
            "New listing notifications",
            "Area-specific trend analysis",
            "Daily morning briefing",
        ],
        "requirements": ["Telegram account"],
        "industries": ["real_estate"],
        "platforms": ["telegram"],
        "setup_time_minutes": 5,
    },
    {
        "name": "Doctor Morning Briefing",
        "slug": "doctor-morning-briefing",
        "description": "Clinical news + patient context. Before your first appointment.",
        "long_description": (
            "Curates clinical news, research updates, and relevant medical "
            "developments for your specialty. Delivered before your first "
            "appointment so you start every day informed."
        ),
        "category": "health",
        "role": "researcher",
        "icon_url": "/icons/doctor-briefing.svg",
        "is_published": False,
        "is_featured": False,
        "price_usd_cents": 5000,
        "features": [
            "Specialty-specific clinical news",
            "Research paper summaries",
            "Drug approval updates",
            "Conference highlights",
            "Daily morning briefing",
        ],
        "requirements": ["Telegram account", "Medical specialty selection"],
        "industries": ["healthcare"],
        "platforms": ["telegram"],
        "setup_time_minutes": 5,
    },
    {
        "name": "AI Receptionist",
        "slug": "ai-receptionist",
        "description": "Answers, books, follows up. 24/7. Never calls in sick.",
        "long_description": (
            "A 24/7 AI receptionist that handles incoming inquiries, books "
            "appointments, sends follow-ups, and keeps your calendar organized. "
            "Works across WhatsApp and Telegram. Never misses a message."
        ),
        "category": "business",
        "role": "assistant",
        "icon_url": "/icons/ai-receptionist.svg",
        "is_published": False,
        "is_featured": False,
        "price_usd_cents": 5000,
        "features": [
            "24/7 message handling",
            "Appointment booking",
            "Follow-up automation",
            "Calendar integration",
            "WhatsApp + Telegram support",
        ],
        "requirements": ["Telegram or WhatsApp Business account"],
        "industries": ["all"],
        "platforms": ["telegram", "whatsapp"],
        "setup_time_minutes": 15,
    },
]


def seed_templates() -> None:
    """Insert or update the 5 agent templates."""
    db = get_service_client()

    for template in AGENT_TEMPLATES:
        existing = (
            db.table("agent_templates")
            .select("id")
            .eq("slug", template["slug"])
            .execute()
        )

        if existing.data:
            db.table("agent_templates").update(template).eq(
                "slug", template["slug"]
            ).execute()
            print(f"  Updated: {template['name']}")
        else:
            db.table("agent_templates").insert(template).execute()
            print(f"  Created: {template['name']}")


def main() -> None:
    """Run seed script."""
    print("Seeding agent templates...")
    seed_templates()
    print("Done.")


if __name__ == "__main__":
    main()
