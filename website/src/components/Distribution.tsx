"use client";
import { useState } from "react";
import { fish } from "@/data/fish";

export function Distribution() {
  const [sort, setSort] = useState<"raw" | "aug" | "id">("raw");
  const [hover, setHover] = useState<number | null>(null);
  const rows = [...fish].sort((a, b) => (sort === "id" ? a.id - b.id : b[sort] - a[sort]));
  const max = 2046;
  return (
    <div className="card mt-8 p-5 md:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-5 text-sm text-mist">
          <span className="flex items-center gap-2"><i className="h-3 w-3 rounded-sm bg-teal" /> Raw</span>
          <span className="flex items-center gap-2"><i className="h-3 w-3 rounded-sm bg-amber/80" /> Augmented</span>
        </div>
        <div role="group" aria-label="Sort" className="flex gap-1 rounded-full border border-line p-1 text-sm">
          {([["raw", "Raw"], ["aug", "Augmented"], ["id", "Paper order"]] as const).map(([k, l]) => (
            <button key={k} aria-pressed={sort === k} onClick={() => setSort(k)} className={`rounded-full px-3 py-1 transition-colors ${sort === k ? "bg-teal text-ink" : "text-mist hover:text-white"}`}>{l}</button>
          ))}
        </div>
      </div>
      <ul className="mt-6 space-y-2.5">
        {rows.map((f) => (
          <li key={f.slug} onMouseEnter={() => setHover(f.id)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(f.id)} onClick={() => setHover(f.id)} tabIndex={0}
              className={`grid grid-cols-[6.5rem_1fr_4.5rem] items-center gap-3 rounded-lg px-2 py-1 text-sm md:grid-cols-[10rem_1fr_6.5rem] ${hover === f.id ? "bg-white/[0.06]" : ""}`}>
            <span className="truncate">{f.name}</span>
            <span className="space-y-1">
              <span className="block h-2 rounded-full bg-teal" style={{ width: `${(f.raw / max) * 100}%`, minWidth: 3 }} />
              <span className="block h-2 rounded-full bg-amber/80" style={{ width: `${(f.aug / max) * 100}%`, minWidth: 3 }} />
            </span>
            <span className="text-right font-mono text-xs text-mist tabular-nums">
              {f.raw}<span className="opacity-50"> → </span>{f.aug.toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-5 text-xs text-mist/80">Totals: 5,520 raw · 19,868 augmented · 25,388 combined.</p>
    </div>
  );
}
