# NutriFish-BD — dataset website

Next.js 16 (App Router) + Tailwind v4, fully static. Lives in `website/` of the dataset repo.

```bash
cd website
npm install
npm run dev        # http://localhost:3000
npm run build && npm start
```

## Where to edit
| What | File |
|---|---|
| Name, conference, authors, Kaggle DOI / Drive mirror / GitHub links, BibTeX | `src/data/site.ts` |
| Paper pages (camera-ready PDF rendered to WebP) | `public/paper/page-01..15.webp` |
| Species table, class counts, nutrition values, per-class F1, CV results | `src/data/fish.json`, `src/data/fish.ts` |
| Page sections | `src/components/*.tsx` |
| Code shown in the "Code" section | `code/*.py` (also served from `public/downloads/code/`) |

## Regenerating assets
`npm run assets` re-creates the optimised WebP images, the sanitised notebook and the `.py` files from
`Fish Images/` and `Validation Code and Plots/` (needs Python + Pillow). Local `/Users/...` paths are replaced
with `/path/to/Fish Dataset Raw`.

## Deploy (Vercel)
Import the GitHub repo, set **Root Directory = `website`**, framework auto-detects as Next.js. No env vars are required;
optionally set `NEXT_PUBLIC_SITE_URL` to your final domain (used for social-share image URLs).
