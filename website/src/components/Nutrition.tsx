"use client";
import { useState } from "react";
import { fish, nutrients, type NutrientKey } from "@/data/fish";
import { Section } from "./Section";

const blurb: Partial<Record<NutrientKey, string>> = {
  vitA: "Mohola (mola) stands far above the rest — 2,500 µg per 100 g — followed by Dhela (930 µg) and Darkina (450 µg).",
  calcium: "Small fish eaten whole supply bone calcium: Dhela (1,250 mg), Chanda (1,160 mg) and Mohola (1,000 mg) lead on calcium.",
  iron: "Darkina (8.1 mg), Chanda (6.8 mg) and Mohola (5.8 mg) are the iron-richest in the set.",
  protein: "Protein is steady across species (14.8–19.2 g); Pabda tops the list.",
  fat: "Koi (9.2 g) and Shing/Jiyol (6.5 g) are the fattiest; Kakila is the leanest (0.9 g).",
  omega3: "Fasha (0.55 g), Shing/Jiyol (0.48 g) and Mohola (0.45 g) lead on omega-3.",
};

export function Nutrition() {
  const [key, setKey] = useState<NutrientKey>("vitA");
  const [showTable, setShowTable] = useState(false);
  const n = nutrients.find((x) => x.key === key)!;
  const rows = fish.map((f) => ({ f, v: f.nut[key] })).sort((a, b) => (b.v ?? -1) - (a.v ?? -1));
  const max = Math.max(...rows.map((r) => r.v ?? 0));
  return (
    <Section id="nutrition" eyebrow="Nutritional metadata" className="!pt-0"
      title="Every species carries 12 nutrient values."
      intro="Values are per 100 g edible portion, compiled from the published literature and reviewed by a certified nutrition professional. Pick a nutrient to rank all 23 species.">
      <div role="tablist" aria-label="Nutrient" className="flex flex-wrap gap-2">
        {nutrients.map((x) => (
          <button key={x.key} role="tab" aria-selected={key === x.key} onClick={() => setKey(x.key)}
            className={`rounded-full border px-3.5 py-1.5 text-sm transition-colors ${key === x.key ? "border-teal bg-teal text-ink" : "border-line text-mist hover:text-white"}`}>{x.label}</button>
        ))}
      </div>
      <div className="card mt-6 p-5 md:p-8">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="font-display text-2xl font-semibold">{n.label} <span className="text-base font-normal text-mist">· {n.unit} per 100 g</span></h3>
        </div>
        {blurb[key] && <p className="mt-2 text-sm text-mist">{blurb[key]}</p>}
        <ul className="mt-6 space-y-1.5">
          {rows.map(({ f, v }) => (
            <li key={f.slug} className="grid grid-cols-[7.5rem_1fr_4.5rem] items-center gap-3 text-sm md:grid-cols-[10rem_1fr_5.5rem]">
              <span className="truncate text-mist">{f.name}</span>
              <span className="h-2.5 rounded-full bg-white/5">
                <span className="block h-full rounded-full bg-gradient-to-r from-teal to-aqua transition-[width] duration-700" style={{ width: v === null ? 0 : `${Math.max(1.5, (v / max) * 100)}%` }} />
              </span>
              <span className="text-right font-mono tabular-nums">{v === null ? <span className="text-mist/60">{f.flags[key] ?? "—"}</span> : v}</span>
            </li>
          ))}
        </ul>
        <p className="mt-5 text-xs text-mist/70">ND = not detected. Nutrient content varies by season, life-cycle stage and environment — treat values as structured reference metadata, not exact per-specimen measurements.</p>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <button className="btn btn-ghost" onClick={() => setShowTable(!showTable)} aria-expanded={showTable}>{showTable ? "Hide" : "Show"} full table</button>
        <a className="btn btn-ghost" href="/downloads/nutrition_metadata_per_100g_from_paper.csv" download>Table 3 as CSV ↓</a>
      </div>
      {showTable && (
        <div className="card thin-scroll mt-4 max-h-[32rem] overflow-auto">
          <table className="data">
            <thead><tr><th>Species</th>{nutrients.map((x) => <th key={x.key}>{x.label}<br /><span className="font-normal opacity-60">{x.unit}</span></th>)}</tr></thead>
            <tbody>
              {fish.map((f) => (
                <tr key={f.slug}>
                  <td><span className="font-semibold">{f.name}</span><br /><em className="text-xs text-mist">{f.sci}</em></td>
                  {nutrients.map((x) => <td key={x.key}>{f.nut[x.key] ?? f.flags[x.key] ?? "—"}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Section>
  );
}
