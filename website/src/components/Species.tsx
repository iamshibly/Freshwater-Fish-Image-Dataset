"use client";
import { useEffect, useMemo, useState } from "react";
import { fish, nutrients, imgSize, type Fish } from "@/data/fish";
import { Section } from "./Section";

const fmt = (f: Fish, k: (typeof nutrients)[number]) => {
  const v = f.nut[k.key];
  return v === null ? f.flags[k.key] ?? "—" : String(v);
};

function Detail({ f, onClose }: { f: Fish; onClose: () => void }) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", h); document.body.style.overflow = ""; };
  }, [onClose]);
  const sz = imgSize(f.slug);
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-0 backdrop-blur-sm md:items-center md:p-6" onClick={onClose} role="dialog" aria-modal="true" aria-label={f.name}>
      <div className="card max-h-[92vh] w-full max-w-4xl overflow-y-auto !rounded-b-none bg-deep md:!rounded-b-[1.25rem]" onClick={(e) => e.stopPropagation()}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/fish/${f.slug}.webp`} width={sz.w} height={sz.h} alt={`${f.name}, ${f.sci}`} className="max-h-[42vh] w-full rounded-t-[1.25rem] bg-black/20 object-contain" />
        <div className="p-6 md:p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="eyebrow">Species {String(f.id).padStart(2, "0")} / 23</p>
              <h3 className="font-display mt-1 text-3xl font-semibold">{f.name}</h3>
              <p className="italic text-mist">{f.sci}</p>
            </div>
            <button className="btn btn-ghost !px-3 !py-1.5" onClick={onClose} aria-label="Close">✕</button>
          </div>
          <div className="mt-6 grid grid-cols-3 gap-3">
            {[["Raw images", f.raw.toLocaleString()], ["Augmented", f.aug.toLocaleString()], ["Baseline F1", f.f1.toFixed(3)]].map(([k, v]) => (
              <div key={k} className="rounded-xl border border-line bg-white/[0.03] p-3">
                <div className="text-xs text-mist">{k}</div><div className="font-display text-xl font-semibold">{v}</div>
              </div>
            ))}
          </div>
          <h4 className="mt-7 text-sm font-semibold uppercase tracking-wider text-mist">Nutrition per 100 g edible portion</h4>
          <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
            {nutrients.map((n) => (
              <div key={n.key} className="flex justify-between border-b border-line py-1.5">
                <dt className="text-mist">{n.label}</dt>
                <dd className="font-mono tabular-nums">{fmt(f, n)} <span className="text-mist/60">{n.unit}</span></dd>
              </div>
            ))}
          </dl>
          {f.proxy && (
            <p className="mt-4 rounded-lg border border-amber/40 bg-amber/10 p-3 text-sm text-amber">
              <strong>Proxy row.</strong> No published composition data exists for {f.sci}; these values are those reported for <em>{f.proxy}</em>, a bagrid catfish of comparable size and feeding habit. The released CSV flags it as a proxy.
            </p>
          )}
          <p className="mt-4 text-xs text-mist/70">ND = no reference value found. Values are compiled reference values, not laboratory measurements of the photographed fish, and vary with season, life stage and environment.</p>
        </div>
      </div>
    </div>
  );
}

export function Species() {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<"id" | "raw" | "f1">("id");
  const [sel, setSel] = useState<Fish | null>(null);
  const list = useMemo(() => {
    const t = q.trim().toLowerCase();
    return fish
      .filter((f) => !t || f.name.toLowerCase().includes(t) || f.sci.toLowerCase().includes(t))
      .sort((a, b) => (sort === "id" ? a.id - b.id : b[sort] - a[sort]));
  }, [q, sort]);
  return (
    <Section id="species" eyebrow="Species explorer" title="Meet all 23 species."
      intro="One representative photograph per species, labelled with its local name and scientific name (matched against Rahman’s reference). Open any card for class sizes, baseline F1 and its nutrient profile.">
      <div className="mb-8 flex flex-wrap items-center gap-3">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by local or scientific name…" aria-label="Search species"
          className="w-full max-w-sm rounded-full border border-line bg-white/5 px-5 py-2.5 text-sm outline-none placeholder:text-mist/60 focus:border-teal" />
        <div role="group" aria-label="Sort species" className="flex gap-1 rounded-full border border-line p-1 text-sm">
          {([["id", "Paper order"], ["raw", "Most images"], ["f1", "Highest F1"]] as const).map(([k, l]) => (
            <button key={k} aria-pressed={sort === k} onClick={() => setSort(k)} className={`rounded-full px-3 py-1 ${sort === k ? "bg-teal text-ink" : "text-mist hover:text-white"}`}>{l}</button>
          ))}
        </div>
        <span className="text-sm text-mist">{list.length} shown</span>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        {list.map((f) => (
          <button key={f.slug} onClick={() => setSel(f)} className="card group overflow-hidden text-left transition-transform hover:-translate-y-1 hover:border-teal/40">
            <div className="aspect-[16/10] overflow-hidden bg-black/20">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/fish/${f.slug}.webp`} alt={`${f.name} (${f.sci})`} loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
            </div>
            <div className="p-4">
              <div className="flex items-baseline justify-between gap-2">
                <h3 className="truncate font-semibold">{f.name}</h3>
                <span className="font-mono text-xs text-mist/60">#{f.id}</span>
              </div>
              <p className="truncate text-xs italic text-mist">{f.sci}</p>
              <p className="mt-2 text-xs text-mist/80">{f.raw} raw · F1 {f.f1.toFixed(2)}{f.proxy && <span className="ml-1 text-amber" title="Nutrition values are a proxy">· proxy nutrition</span>}</p>
            </div>
          </button>
        ))}
      </div>
      {list.length === 0 && <p className="py-12 text-center text-mist">No species match “{q}”.</p>}
      {sel && <Detail f={sel} onClose={() => setSel(null)} />}
    </Section>
  );
}
