# Reconcile — template.psd (Language Center flyer)

**Source:** `imports/template.psd` (Adobe PSD, 600×3755)  
**Extracts:** `.working/import-template-psd-*.png` / `*.jpg` (composite + slices)  
**Decisions:** `.memlog.md` (Brand & Style / visual language) · `capture-visual-language.md`  
**Status:** Closed for coaching — no new brand decisions invented here

---

## 1. Qualitative ideas in the PSD

Long-form marketing flyer for a generic “Language Center,” vertical scroll, brochure density (airy whitespace, full-width color bands).

| Bucket | What the flyer showed |
|--------|------------------------|
| **A — Palette** | Coral as hero accent and large solid blocks; white / light grey; charcoal dark sections; coral used for links, bullets, and CTA-like emphasis |
| **B — Typography** | Clean modern sans throughout; section titles often ALL CAPS + bold; body regular/legible |
| **C — Motifs** | Short horizontal accent rules beside section headers; solid coral numbered circles (e.g. “6 reasons”); coral list markers; stylized coral globe mark in header |
| **D — Photography** | Stock people holding national flags (color hero); grayscale group of smiling adults; international “classroom” imagery |
| **E — Mood** | Warm adult education — approachable, professional, instructional; not kids-app and not sterile SaaS |

Also present as brochure chrome (not product UI): contact/address stack, social icons, email footer / unsubscribe, course-copy blocks on coral and charcoal full-bleed bands.

---

## 2. What was adopted into spines / visual language

| Lift | How it landed in product UI |
|------|-----------------------------|
| **A palette** | Coral `#FF8161` as spark (next lesson, today accents, CTA, missed `!`, soft coral fills); neutrals from **neutral-cool-lines** (cool greys + white / charcoal dark mode) — not brochure-scale coral planes |
| **B typography** | Clean sans stack: `"Segoe UI", "Helvetica Neue", Arial, sans-serif`. ALL CAPS reserved for panel/section labels; app nav **sentence case** (hybrid fork A) |
| **C motifs** | Numbered coral circles + short accent rules in plan / side panel (hybrid **1+3**: coral-accent-tool density + numbered-coach motifs). Circles full-round; chrome radius ~4px |
| **E mood** | Warm adult education emotional register, constrained by brand mood **рабочий инструмент** and voice **дружеский**; anti: sterile SaaS / kids language-app |

**Direction lock:** hybrid **1+3** + theme **neutral-cool-lines** (light + dark). Warm wash `#FFF9F7` from numbered-coach fork B retained only as **today-tint** on the calendar today cell — not as primary surface wash (surface-wash override via theme pick).

---

## 3. Explicitly dropped (and why)

| Dropped | Why |
|---------|-----|
| **D — stock people + flags photography** | Decision: not lifted into product UI. Avoids generic international-school brochure look; product is a dense working tool (calendar, lesson tape, dashboards), not a marketing flyer. Applies to both color flag-holding hero and grayscale people bands. |
| **Coral / charcoal as large carrying surfaces** | Direction 2-style full coral blocks and brochure charcoal planes were explored then not chosen as primary chrome. Coral is **spark only**; light sidebar / cool grey surfaces win under neutral-cool-lines. |
| **Full-bleed warm wash UI** | Hybrid fork B warm wash overridden: primary light surfaces stay cool grey (`#F7F8F9` / white / `#F3F4F6`), not `#FFF9F7` everywhere. |
| **Flyer / brochure layout grammar** | Centered sparse stacks, email footer, social row, globe lockup as brand mark — not adopted as app structure. Product density stays Outlook-like. |

No new logo, photography, or brochure-layout system was added as a brand decision.

---

## 4. Residual risks

1. **Brochure vs dense tool** — PSD motifs (numbered circles, accent rules, coral warmth) come from an airy flyer; product chrome is Outlook-like calendar + lesson plan / chat density. Risk: motifs feel decorative or oversized if not kept small and local (plan/side panel), or conversely get lost if over-shrunk.
2. **Warmth vs cool-lines** — Mood E was “warm adult education,” but surfaces are deliberately cool grey with coral spark and only a faint today-tint. Risk: product reads cooler / more SaaS-tool than the flyer unless coral and motifs stay consistently present on key states (next, today, CTA, plan steps).
3. **ALL CAPS inheritance** — Flyer uses caps broadly; product limits caps to panel/section labels. Risk: drift toward flyer-like shouting headers if implementers copy PSD type habits beyond the locked rule.
4. **Photography vacuum** — Dropping D removes the flyer’s main emotional imagery. Empty states and onboarding must rely on typography, coral spark, and motifs — not substituted stock people/flags without a later explicit decision.

---

## Trace

- Memlog: lift A/B/C/E, not D; hybrid 1+3; neutral-cool-lines; surface-wash override (today-tint only)
- Capture: `capture-visual-language.md`
- Artifacts: `direction-*.html`, `color-themes-hybrid-1-3.html`, PSD extracts above
