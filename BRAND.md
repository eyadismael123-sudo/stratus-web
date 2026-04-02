# Stratus Brand System

## 1. Colour System

### Primary Palette
```
Background:       #FAF9F6  (Cream — warm, premium canvas)
Charcoal:         #1A1A1A  (near-black — text, nav, dark elements)
Forest:           #1B4332  (primary accent — CTAs, online dots, highlights)
Mid Green:        #2D6A4F  (hover state of Forest, secondary accent)
Warm Grey:        #E8E6E1  (borders, dividers, background tints)
White:            #FFFFFF  (cards, panels, interactive surfaces)
```

### Extended Grey Scale (5-grey system)
| Name | Hex | Usage |
|------|-----|-------|
| **Grey 900** | `#1A1A1A` | Primary text, headings, nav active state, icons (charcoal) |
| **Grey 700** | `#4A4A4A` | Secondary text, help text, disabled borders |
| **Grey 500** | `#8A8A8A` | Tertiary text, subtle elements, lighter icons |
| **Grey 300** | `#E8E6E1` | Borders, dividers, input field borders, light background tints (Warm Grey) |
| **Grey 100** | `#FAF9F6` | Subtle background, hover states on light surfaces, card backgrounds (Cream) |

### Status & Semantic
```
Success:   #1B4332  (Forest green — agent online, checks — matches brand accent)
Error:     #C0392B  (deep red, failures, alerts)
Warning:   #D97706  (amber, inactive/paused agents)
Info:      #2563EB  (blue, informational banners)
Accent:    #1B4332  (Forest — online status dots, CTAs, highlights)
```

---

## 2. Typography

### Font Family
```
Display:  Clash Display Bold (for hero headlines, Instagram posts, animated videos)
          Clash Display Semibold (for subheads, section titles)
Headings: Satoshi Bold / Black (for H2–H4 in UI)
Body:     Satoshi Regular (for body copy)
Mono:     SF Mono, Regular (for logs, code, data)
```

**Sources:**
- Clash Display: Fontshare (fontshare.com/fonts/clash-display) — free, no license issues
- Satoshi: Fontshare (fontshare.com/fonts/satoshi) — free, no license issues

**CDN (for HTML animated videos):**
```css
@import url('https://api.fontshare.com/v2/css?f[]=clash-display@700,600&display=swap');
@import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&display=swap');
```

**Note:** Clash Display is the display/marketing font. Satoshi remains the UI font for the web app and mobile app. Both from Fontshare.

### Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| **H1** | 48px | Satoshi Black | 1.1 (52.8px) | Landing hero, page title (desktop only) |
| **H2** | 36px | Satoshi Bold | 1.2 (43.2px) | Section title, dashboard header |
| **H3** | 28px | Satoshi Bold | 1.3 (36.4px) | Card title, subsection |
| **H4** | 20px | Satoshi Bold | 1.4 (28px) | Form label, agent name, list item title |
| **Body** | 16px | Satoshi Regular | 1.5 (24px) | Main content, paragraphs, agent description |
| **Body Small** | 14px | Satoshi Regular | 1.5 (21px) | Secondary text, helper text, breadcrumbs |
| **Caption** | 12px | Satoshi Regular | 1.4 (16.8px) | Timestamps, metadata, footer text |
| **Mono** | 13px | SF Mono Regular | 1.5 (19.5px) | API responses, logs, inline code |

---

## 3. Spacing Scale

8px base unit (inspired by Tailwind, Linear, Apple):

```
xs:     4px    (tight)
sm:     8px    (1 unit)
md:     12px   (1.5 units)
lg:     16px   (2 units)
xl:     24px   (3 units)
2xl:    32px   (4 units)
3xl:    48px   (6 units)
4xl:    64px   (8 units)
5xl:    80px   (10 units)
```

### Common Spacing Rules
- **Card padding:** 20px (lg + sm, Apple Standard Padding)
- **Page padding (desktop):** 24px (xl)
- **Page padding (mobile):** 16px (lg)
- **Section gap:** 32px (2xl)
- **Input field height:** 40px (20px top/bottom padding + 16px / line height)

---

## 4. Border Radius

Subtle, not aggressive:

```
none:     0px
sm:       4px    (slight softness on inputs)
md:       8px    (standard cards, modals, buttons)
lg:       12px   (larger cards, hero sections)
xl:       16px   (expanded modals, hero overlays)
full:     9999px (pills, avatars, badge shapes)
```

**Default usage:**
- Buttons: `border-radius: 8px` (md)
- Cards: `border-radius: 8px` (md)
- Input fields: `border-radius: 8px` (md)
- Avatar/icons: `border-radius: 9999px` (full)
- Modals: `border-radius: 12px` (lg)

---

## 5. Shadows

### Card Shadow (Standard Depth)
```
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
```
**Use:** Default cards, dropdowns, tooltips (subtle presence)

### Elevated Shadow (Deep Depth)
```
box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12), 0 4px 6px rgba(0, 0, 0, 0.08);
```
**Use:** Modals, floating panels, hero overlays (strong presence)

### No shadow
Interactive elements (buttons, links) — let whitespace + colour define depth.

---

## 6. Component States

All components follow these state rules:

### Buttons (Primary)
| State | Background | Text | Border | Shadow |
|-------|-----------|------|--------|--------|
| **Default** | `#1B4332` (Forest) | `#FFFFFF` | none | none |
| **Hover** | `#2D6A4F` (Mid Green) | `#FFFFFF` | none | Card shadow |
| **Active/Pressed** | `#163829` (darker Forest) | `#FFFFFF` | none | Card shadow |
| **Disabled** | `#E8E6E1` (Warm Grey) | `#8A8A8A` | none | none |

### Secondary Buttons
| State | Background | Text | Border |
|-------|-----------|------|--------|
| **Default** | `#FAF9F6` (Cream) | `#1A1A1A` | `1px #E8E6E1` |
| **Hover** | `#E8E6E1` (Warm Grey) | `#1A1A1A` | `1px #E8E6E1` |
| **Active** | `#D9D7D2` | `#1A1A1A` | `1px #8A8A8A` |
| **Disabled** | `#FAF9F6` | `#8A8A8A` | `1px #E8E6E1` |

### Input Fields
| State | Background | Border | Text |
|-------|-----------|--------|------|
| **Default** | `#FFFFFF` | `1px #E8E6E1` | `#1A1A1A` |
| **Hover** | `#FFFFFF` | `1px #8A8A8A` | `#1A1A1A` |
| **Focus** | `#FFFFFF` | `2px #1B4332` | `#1A1A1A` |
| **Disabled** | `#FAF9F6` | `1px #E8E6E1` | `#8A8A8A` |
| **Error** | `#FFFFFF` | `1px #C0392B` | `#1A1A1A` |

### Cards & Panels
| State | Background | Border | Shadow |
|-------|-----------|--------|--------|
| **Default** | `#FFFFFF` | `1px #FAF9F6` | Card shadow |
| **Hover** | `#FFFFFF` | `1px #E8E6E1` | Card shadow |
| **Selected** | `#FFFFFF` | `2px #1B4332` | Card shadow |
| **Disabled/Inactive** | `#FAF9F6` | `1px #E8E6E1` | none |

### Toggles & Checkboxes
| State | Fill | Border |
|-------|------|--------|
| **Off (default)** | `#FFFFFF` | `1px #E8E6E1` |
| **On (checked)** | `#1B4332` | none |
| **Hover (off)** | `#FFFFFF` | `1px #8A8A8A` |
| **Disabled (off)** | `#FAF9F6` | `1px #E8E6E1` |
| **Disabled (on)** | `#E8E6E1` | none |

### Status Indicators (Dots)
| Status | Colour | Usage |
|--------|--------|-------|
| **Online** | `#1B4332` (Forest) | Agent active, real-time connection |
| **Idle** | `#8A8A8A` (Grey 500) | Agent paused or waiting |
| **Offline** | `#4A4A4A` (Grey 700) | Agent disconnected |
| **Error** | `#C0392B` (deep red) | Agent error/failure |

---

## 7. Interaction & Animation Principles

### Transitions
```
Default:       150ms cubic-bezier(0.4, 0, 0.2, 1)  (fast, iOS-style)
Slow:          300ms cubic-bezier(0.4, 0, 0.2, 1)  (entrance/exit animations)
Instant:       0ms                                  (status updates, real-time changes)
```

### Opacity Rules
- **Hover:** +10% opacity increase on non-button elements
- **Disabled:** 50% opacity, cursor: not-allowed
- **Loading skeletons:** 60% opacity warm grey (`#E8E6E1` at 60%)

---

## 8. Usage Rules (Locked)

### Background Palette
- **Page background:** `#FAF9F6` (Cream — never pure white)
- **Card/panel background:** `#FFFFFF` (pure white for contrast)
- **Input/textarea background:** `#FFFFFF` (match cards)
- **Hover background:** `#FAF9F6` (Cream, subtle)
- **Disabled background:** `#FAF9F6` (Cream, 50% opacity)

### Text Hierarchy
- **Primary text:** Charcoal (`#1A1A1A`) — headings, labels, body
- **Secondary text:** Grey 700 (`#4A4A4A`) — subtitles, metadata
- **Tertiary text:** Grey 500 (`#8A8A8A`) — helper text, timestamps
- **Disabled text:** Grey 500 at 50% opacity

### Accent Usage (Forest Green)
- **CTAs (buttons):** Forest `#1B4332` — every primary action
- **Status online:** Forest `#1B4332` — agent active indicator
- **Focus states:** Forest `#1B4332` — input borders on focus
- **Selected states:** Forest `#1B4332` — card borders, active nav
- **Never use Forest for body text.** Forest is interaction + status only.

### Borders
- **Default borders:** Warm Grey (`#E8E6E1`, 1px)
- **Hover borders:** Grey 500 (`#8A8A8A`, 1px)
- **Focus borders:** Forest `#1B4332` (2px, input fields)
- **Dividers (horizontal lines):** Cream (`#FAF9F6`, 1px)

---

## 9. Dark Mode (Deferred)

Not in Sprint 1. Will be designed in Sprint 2+ if user requests.

---

## 10. Implementation Checklist

### For Frontend Engineer
- [ ] Create Tailwind `tailwind.config.ts` with exact hex values from this doc
- [ ] Import Satoshi from Fontshare in `layout.tsx` (use `@font-face` or next/font local)
- [ ] Create `@/constants/brand.ts` exporting all hex values as constants
- [ ] Create reusable component variants (Button, Input, Card, Badge) matching state tables
- [ ] Test all states (default, hover, active, disabled) on every component
- [ ] Verify colour contrast ratios (WCAG AA: 4.5:1 text, 3:1 graphics)
- [ ] No hardcoded hex values — always use Tailwind classes or brand constants

### For Mobile (NativeWind)
- [ ] NativeWind applies same Tailwind config to React Native
- [ ] All hex values from this doc work directly in NativeWind
- [ ] Typography scale maps 1:1 (H1–Caption sizes match across web + mobile)
- [ ] Test on both iOS and Android simulators for colour accuracy

---

## 11. Locked & Final

**Decision authority:** Eyad (Founder)
**Date locked:** 2026-03-27
**Status:** FINAL — palette updated from graphite/yellow to Forest green system.

### Palette (quick reference)
| Token | Hex | Name |
|-------|-----|------|
| `--color-bg` | `#FAF9F6` | Cream |
| `--color-fg` | `#1A1A1A` | Charcoal |
| `--color-accent` | `#1B4332` | Forest |
| `--color-accent-hover` | `#2D6A4F` | Mid Green |
| `--color-border` | `#E8E6E1` | Warm Grey |
| `--color-surface` | `#FFFFFF` | White |

This is the source of truth. Frontend Engineer and Mobile Engineer reference this file for every colour, font, spacing, shadow, and state. No improvisation. No design-time decisions.
