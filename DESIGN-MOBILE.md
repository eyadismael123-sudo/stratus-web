# Stratus — Mobile Design Brief

**Status:** ✅ COMPLETE — All 8 pages mobile-responsive, verified at 390×844px
**Owner:** 🎨 Creative Artist
**Last Updated:** 2026-03-21

---

## Breakpoints

| Breakpoint | Width | Use |
|---|---|---|
| Mobile | 375–390px | Primary (iPhone-first) |
| Tablet | 768px | Mid breakpoint |
| Desktop | 1280px+ | Full layout |

All media queries use `@media (max-width: 768px)`.

---

## Mobile Bottom Tab Bar

All app pages (04–08) have a fixed mobile bottom tab bar replacing the sidebar:
- Fixed at bottom, 60px height, `z-index: 999`
- 3 tabs: **Team** (dashboard icon) | **Hire** (marketplace icon) | **Billing** or **Admin** (context-specific)
- Active tab: white icon + label. Inactive: 30% white.
- Safe area inset: `padding-bottom: env(safe-area-inset-bottom)`
- Sidebar hidden via `transform: translateX(-100%)` on mobile
- Main content: `margin-left: 0`, `padding-bottom: 72px`

---

## Mobile Fixes by Page (Session 2026-03-21)

### 02-landing-page.html ✅
- Responsive from original build
- Font: Satoshi (Fontshare CDN)
- Hero scroll journey works at mobile width

### 03-auth.html ✅
- Centred card layout naturally responsive
- No overflow issues

### 04-dashboard.html ✅
- Sidebar hidden, mobile tab bar shown
- Agent cards: 1-column grid on mobile
- Category tabs: horizontally scrollable (overflow-x: auto)

### 05-agent-detail.html ✅ FIXED
**Problem:** Horizontal overflow from log card text
**Root cause:** Flex children without `min-width: 0` can't shrink below intrinsic content width
**Fix applied:**
```css
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); }
  .main { margin-left: 0; padding-bottom: 72px; overflow-x: hidden; }
  .topbar { padding: 0 16px; }
  .topbar-actions { display: none; }
  .content-grid { grid-template-columns: 1fr; }
  .col-profile { display: none; }
  .col-activity { padding: 16px; min-width: 0; }
  .log-entry { min-width: 0; }
  .log-body { min-width: 0; }
  .log-card { overflow-x: hidden; overflow-wrap: break-word; }
  .log-time { display: none; }
}
```
**Key lesson:** Always add `min-width: 0` to flex children that use `flex: 1` and contain text.

### 06-marketplace.html ✅
- Sidebar hidden, tab bar shown
- Category tabs scrollable
- Agent cards: 1-column on mobile

### 07-billing.html ✅ FIXED
**Problem:** 4-col stats grid overflowing, sub-row "Manage" button clipped
**Fix applied:**
```css
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); }
  .main { margin-left: 0; padding-bottom: 72px; overflow-x: hidden; }
  .content { padding: 16px; }
  .topbar { padding: 0 16px; }
  .topbar-actions { display: none; }
  .billing-summary { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .billing-grid { grid-template-columns: 1fr; }
  .sub-row { flex-wrap: wrap; gap: 8px; padding: 16px; }
  .sub-info { min-width: 0; }
  .sub-status, .sub-price, .sub-actions { flex-shrink: 0; }
  .sub-price { margin-left: auto; }
  .sub-actions { width: 100%; margin-top: 4px; }
  .section { overflow-x: auto; }
  .invoice-table { min-width: 480px; }
}
```

### 08-admin.html ✅ FIXED
**Problem:** Page-level horizontal scroll — content extending beyond 390px viewport
**Root cause:** `overflow-x: hidden` on `.main` alone is insufficient; `html` and `body` also need it
**Fix applied:**
```css
@media (max-width: 768px) {
  html, body { overflow-x: hidden; }
  .sidebar { transform: translateX(-100%); }
  .main { margin-left: 0; padding-bottom: 72px; overflow-x: hidden; width: 100%; }
  .topbar { padding: 0 16px; width: 100%; }
  .topbar-right { display: none; }
  .page-content { padding: 16px; overflow-x: hidden; }
  .status-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .tabs { overflow-x: auto; width: 100%; -webkit-overflow-scrolling: touch; }
  .tab { white-space: nowrap; padding: 8px 14px; }
  .overview-grid { grid-template-columns: 1fr; }
  .card { overflow-x: auto; }
  .agent-table { min-width: 560px; }
}
```
**Verified:** `document.documentElement.scrollWidth === 390` — no horizontal scroll.

---

## Mobile Design Rules (LOCKED)

1. **No horizontal scroll** — ever. Verify with `scrollWidth === clientWidth`.
2. **`html, body { overflow-x: hidden; }`** — always set this in addition to container overflow rules.
3. **`min-width: 0` on flex children** — required for any `flex: 1` child containing text.
4. **Wide tables** — contain inside `overflow-x: auto` card + `min-width` on the table itself.
5. **Multi-column grids** — max 2 columns on mobile. Stats grids: 2×N. Never 3+ on 390px.
6. **Top bar actions** — hide on mobile (`.topbar-actions { display: none; }`). Use bottom tab bar instead.
7. **Sidebars** — always `transform: translateX(-100%)` on mobile. Never `display: none` (breaks animations).
8. **`flex-wrap: wrap`** — use on any flex row that has 3+ items at desktop, so they stack on mobile.
9. **`word-break: break-all` is too aggressive** — use `overflow-wrap: break-word` for log text.
10. **Verify with Playwright** — always screenshot at 390×844 after every mobile fix.

---

## Verification Status (2026-03-21)

| Page | Mobile Verified | scrollWidth Check |
|---|---|---|
| 02-landing-page.html | ✅ | — |
| 03-auth.html | ✅ | — |
| 04-dashboard.html | ✅ | — |
| 05-agent-detail.html | ✅ Screenshot clean | — |
| 06-marketplace.html | ✅ | — |
| 07-billing.html | ✅ Screenshot clean | — |
| 08-admin.html | ✅ Screenshot clean | scrollWidth === 390 ✅ |
