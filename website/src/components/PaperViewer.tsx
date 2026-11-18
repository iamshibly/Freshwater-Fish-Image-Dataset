"use client";
import { useCallback, useEffect, useState } from "react";
import { Section } from "./Section";

const N = 15;
const landscape = new Set<number>();
const titles: Record<number, string> = {
  1: "Title, authors & abstract", 2: "Introduction & contributions", 3: "Related work & dataset", 4: "Pipeline (Fig. 1)",
  5: "Species & Table 2", 6: "Nutritional metadata", 7: "Table 3 & data collection", 8: "Augmentation & protocol",
  9: "Protocol & metrics", 10: "Nested CV (Fig. 3)", 11: "Embeddings (Fig. 4)", 12: "Summary (Fig. 5) & limits",
  13: "Conclusion & acknowledgements", 14: "Data availability & references", 15: "References",
};
const src = (n: number) => `/paper/page-${String(n).padStart(2, "0")}.webp`;

export function PaperViewer() {
  const [n, setN] = useState(1);
  const [zoom, setZoom] = useState(false);
  const go = useCallback((d: number) => setN((c) => Math.min(N, Math.max(1, c + d))), []);
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (zoom && e.key === "Escape") setZoom(false);
      if (!zoom && !(e.target instanceof HTMLElement && /INPUT|TEXTAREA/.test(e.target.tagName))) return;
      if (e.key === "ArrowRight") go(1);
      if (e.key === "ArrowLeft") go(-1);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [zoom, go]);
  return (
    <Section id="paper" eyebrow="The paper" className="!pt-0"
      title="Read it page by page."
      intro="The camera-ready manuscript, right here — all 15 pages. Use the arrows, the page strip, or tap a page to enlarge it.">
      <div className="grid gap-6 lg:grid-cols-[1fr_16rem]">
        <div className="card p-3 md:p-5">
          <div className="flex items-center justify-between gap-3 pb-3">
            <div className="text-sm text-mist"><span className="font-semibold text-foam">Page {n}</span> / {N}{titles[n] && <span className="hidden sm:inline"> · {titles[n]}</span>}</div>
            <div className="flex gap-2">
              <button className="btn btn-ghost !px-3 !py-1.5" onClick={() => go(-1)} disabled={n === 1} aria-label="Previous page">← Prev</button>
              <button className="btn btn-ghost !px-3 !py-1.5" onClick={() => go(1)} disabled={n === N} aria-label="Next page">Next →</button>
            </div>
          </div>
          <button onClick={() => setZoom(true)} className="block w-full cursor-zoom-in overflow-hidden rounded-lg bg-white" aria-label={`Enlarge page ${n}`}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img key={n} src={src(n)} width={landscape.has(n) ? 1430 : 1105} height={landscape.has(n) ? 1105 : 1430} alt={`Paper page ${n} of ${N}`} className="mx-auto h-auto max-h-[80vh] w-auto max-w-full" />
          </button>
        </div>
        <div className="thin-scroll flex gap-2 overflow-x-auto lg:max-h-[46rem] lg:flex-col lg:overflow-y-auto lg:overflow-x-visible lg:pr-1" role="tablist" aria-label="Pages">
          {Array.from({ length: N }, (_, i) => i + 1).map((p) => (
            <button key={p} role="tab" aria-selected={p === n} onClick={() => setN(p)}
              className={`card flex shrink-0 items-center gap-3 p-2 text-left text-xs transition-colors lg:shrink ${p === n ? "!border-teal/70 !bg-teal/10" : "hover:border-teal/30"}`}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src(p)} alt="" loading="lazy" className="h-16 w-12 rounded-sm bg-white object-cover object-top" />
              <span><span className="font-mono text-teal">{String(p).padStart(2, "0")}</span><span className="hidden text-mist lg:block">{titles[p] ?? ""}</span></span>
            </button>
          ))}
        </div>
      </div>
      {zoom && (
        <div className="fixed inset-0 z-50 flex flex-col bg-black/90 p-4 backdrop-blur" onClick={() => setZoom(false)} role="dialog" aria-modal="true" aria-label={`Page ${n}`}>
          <div className="mx-auto flex w-full max-w-5xl items-center justify-between pb-3" onClick={(e) => e.stopPropagation()}>
            <span className="text-sm text-mist">Page {n} / {N}</span>
            <div className="flex gap-2">
              <button className="btn btn-ghost !px-3 !py-1.5" onClick={() => go(-1)} disabled={n === 1}>←</button>
              <button className="btn btn-ghost !px-3 !py-1.5" onClick={() => go(1)} disabled={n === N}>→</button>
              <button className="btn btn-ghost !px-3 !py-1.5" onClick={() => setZoom(false)} aria-label="Close">✕</button>
            </div>
          </div>
          <div className="min-h-0 flex-1 overflow-auto" onClick={(e) => e.stopPropagation()}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={src(n)} alt={`Paper page ${n}`} className="mx-auto h-auto w-full max-w-5xl rounded-lg bg-white" />
          </div>
        </div>
      )}
    </Section>
  );
}
