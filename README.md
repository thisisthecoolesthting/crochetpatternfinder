# ssc-site — affiliate Astro template

**Agent entry:** `build/AFFILIATE_BUILD_TEMPLATE.md`  
**Spine spec:** `build/AFFILIATE_SITE_TEMPLATE_SPINE.md`  
**Path:** `templates/ssc-site/` (DEv1 repo root)

Every new affiliate site is spawned from this shell, then receives per-slug design tokens and content.

---

## Directory map

```
templates/ssc-site/
├── astro.config.mjs
├── package.json
├── tailwind.config.mjs
├── public/              # favicons, heroes/, videos/ (per site after spawn)
└── src/
    ├── layouts/BaseLayout.astro
    ├── components/      # Header, PageHero, HeroCompact, TrustStrip, sectionAds, …
    ├── pages/           # index, articles, pillars, products, legal, …
    ├── content/         # articles/, products/, pillars/ (empty at template)
    ├── data/spawn-home.json   # GA4, amazon_tag, nav, homepage compare row
    ├── styles/global.css
    └── utils/product-image.ts
```

---

## Promotion (template → spawned site)

```powershell
python scripts/apply_uipro_spine.py --site-path C:\Projects\sites\<slug>
# Windows helper:
powershell -File scripts/apply-uipro-spine.ps1 -SitePath C:\Projects\sites\<slug> -FactoryRoot C:\Users\reasn\Documents\Claude\Projects\DEv1
```

Source of truth for copied files: `COPY_MAP` in `scripts/apply_uipro_spine.py`.  
After template changes: run `promote_refillwatch_spine_to_template.py` first, then apply to fleet.

---

## Phase 0 checks before content gen

- [ ] `Header.astro` reads `spawn-home.json` (not hardcoded nav)
- [ ] List routes use `sectionAds` / `sectionAdsCompact`
- [ ] No legacy `PhoneCasePromo` or wrong ad slot sizes
- [ ] `isHeroImageAvailable` (or equivalent) — no index cards without hero files
- [ ] Product inline Amazon cards use live image URLs (see `fix-amazon-inline-cards.mjs` in build gate)

---

## Spawn

```powershell
python scripts/spawn_factory_site.py <slug> --force
python scripts/finish_wave_site.py --site <slug> --spine-homepage
```

Requires `niche_specs/<slug>.json` in DEv1.

---

_Last updated: 2026-06-07_
