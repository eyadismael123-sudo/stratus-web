"""Quote calculator for 3D print orders.

Formula (all rates loaded from env — cousin changes them without touching code):

    filament_grams × FILAMENT_COST_PER_GRAM       (material cost)
  + print_hours    × MACHINE_HOURLY_RATE           (machine time)
  + markup_percent %                               (business margin)
  = raw_total
  → rounded UP to nearest 5 EGP                   (cleaner for customers)
  → minimum MINIMUM_QUOTE_EGP                      (floor price)
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass


FILAMENT_COST_PER_GRAM: float = float(os.getenv("FILAMENT_COST_PER_GRAM", "7"))
MACHINE_HOURLY_RATE: float    = float(os.getenv("MACHINE_HOURLY_RATE", "50.00"))
MARKUP_PERCENT: float         = float(os.getenv("MARKUP_PERCENT", "30"))
MINIMUM_QUOTE_EGP: float      = float(os.getenv("MINIMUM_QUOTE_EGP", "150"))


@dataclass(frozen=True)
class QuoteResult:
    filament_cost_egp: float
    machine_cost_egp: float
    subtotal_egp: float
    markup_egp: float
    total_egp: float
    grams: float
    print_hours: float


def calculate_quote(grams: float, print_hours: float) -> QuoteResult:
    filament_cost = round(grams * FILAMENT_COST_PER_GRAM, 2)
    machine_cost  = round(print_hours * MACHINE_HOURLY_RATE, 2)
    subtotal      = filament_cost + machine_cost
    markup        = round(subtotal * (MARKUP_PERCENT / 100), 2)
    raw_total     = subtotal + markup

    total_egp = max(MINIMUM_QUOTE_EGP, math.ceil(raw_total / 5) * 5)

    return QuoteResult(
        filament_cost_egp=filament_cost,
        machine_cost_egp=machine_cost,
        subtotal_egp=round(subtotal, 2),
        markup_egp=markup,
        total_egp=float(total_egp),
        grams=round(grams, 1),
        print_hours=round(print_hours, 2),
    )
