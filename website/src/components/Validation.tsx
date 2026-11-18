"use client";
import { useState } from "react";
import { cv, fish } from "@/data/fish";
import { Section } from "./Section";
import { Reveal, CountUp } from "./ui";
import { Gallery } from "./Gallery";

function FoldChart() {
  const W = 560, H = 260, p = { l: 44, r: 12, t: 14, b: 34 };
  const lo = 0.95, hi = 1.0;
  const x = (i: number) => p.l + ((W - p.l - p.r) * (i + 0.5)) / 5;
  const y = (v: number) => p.t + (H - p.t - p.b) * (1 - (v - lo) / (hi - lo));
  const series = [["acc", "Accuracy", "#2dd4bf"], ["bal", "Balanced acc.", "#22b8e6"], ["f1", "Macro-F1", "#fbbf24"]] as const;
  const [h, setH] = useState<number | null>(null);
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Accuracy, balanced accuracy and macro-F1 across the five outer folds">
        {[0.95, 0.96, 0.97, 0.98, 0.99, 1.0].map((t) => (
          <g key={t}><line x1={p.l} x2={W - p.r} y1={y(t)} y2={y(t)} stroke="rgba(160,230,240,.12)" /><text x={p.l - 8} y={y(t) + 4} textAnchor="end" fontSize="10" fill="#a9c7cf">{(t * 100).toFixed(0)}%</text></g>
        ))}
        {series.map(([k, , c]) => (
          <g key={k}>
            <polyline fill="none" stroke={c} strokeWidth="2.5" points={cv.folds.map((f, i) => `${x(i)},${y(f[k])}`).join(" ")} />
            {cv.folds.map((f, i) => <circle key={i} cx={x(i)} cy={y(f[k])} r={h === i ? 6 : 4} fill={c} />)}
          </g>
        ))}
        {cv.folds.map((_, i) => (
          <g key={i} onMouseEnter={() => setH(i)} onMouseLeave={() => setH(null)}>
            <rect x={x(i) - 40} y={p.t} width="80" height={H - p.t - p.b} fill="transparent" />
            <text x={x(i)} y={H - 12} textAnchor="middle" fontSize="11" fill="#a9c7cf">Fold {i + 1}</text>
          </g>
        ))}
      </svg>
      <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-mist">
        {series.map(([k, l, c]) => <span key={k} className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full" style={{ background: c }} />{l}</span>)}
        <span className="ml-auto font-mono">{h !== null ? `Fold ${h + 1}: ${(cv.folds[h].acc * 100).toFixed(2)} / ${(cv.folds[h].bal * 100).toFixed(2)} / ${(cv.folds[h].f1 * 100).toFixed(2)}` : "hover a fold"}</span>
      </div>
    </div>
  );
}

function F1Chart() {
  const rows = [...fish].sort((a, b) => b.f1 - a.f1);
  return (
    <ul className="space-y-1">
      {rows.map((f) => (
        <li key={f.slug} className="grid grid-cols-[6.5rem_1fr_2.6rem] items-center gap-2 text-xs md:grid-cols-[8rem_1fr_3rem]">
          <span className="truncate text-mist">{f.name}</span>
          <span className="h-2 rounded-full bg-white/5">
            <span className="block h-full rounded-full" style={{ width: `${((f.f1 - 0.88) / 0.12) * 100}%`, background: f.f1 >= 0.98 ? "#2dd4bf" : f.f1 >= 0.95 ? "#22b8e6" : "#fbbf24" }} />
          </span>
          <span className="text-right font-mono tabular-nums">{f.f1.toFixed(2)}</span>
        </li>
      ))}
    </ul>
  );
}

export function Validation() {
  return (
    <Section id="validation" eyebrow="Validation"
      title="Learnable, consistently labelled, and stable across every split."
      intro="To test the data fairly, a lightweight ImageNet-pretrained MobileNetV3-Small was fine-tuned under nested cross-validation: 5 outer folds estimate final performance, 2 inner folds choose learning rate, weight decay, dropout, label smoothing and epochs.">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cv.summary.map((m, i) => (
          <Reveal key={m.label} delay={i * 60}>
            <div className="card p-6">
              <div className="text-sm text-mist">{m.label}</div>
              <div className="font-display mt-1 text-4xl font-semibold text-teal"><CountUp to={m.mean} suffix="%" decimals={2} />
              </div>
              <div className="mt-1 font-mono text-xs text-mist">± {m.std}% · 95% CI {m.ci}</div>
            </div>
          </Reveal>
        ))}
      </div>
      <p className="mt-4 text-sm text-mist">Mean ± standard deviation over 5 outer folds · {cv.params} parameters · evaluated on the 5,520 raw images.</p>

      <div className="mt-12 grid gap-6 lg:grid-cols-2">
        <Reveal><div className="card h-full p-6"><h3 className="font-semibold">Performance across outer folds</h3><p className="mb-4 text-sm text-mist">No reliance on a single favourable split.</p><FoldChart /></div></Reveal>
        <Reveal delay={90}><div className="card h-full p-6"><h3 className="font-semibold">Per-class F1</h3><p className="mb-4 text-sm text-mist">Even Goti, with just 43 raw images, reaches 0.94.</p><F1Chart /></div></Reveal>
      </div>

      <div className="mt-20">
        <Reveal>
          <h3 className="font-display text-2xl font-semibold md:text-3xl">Inside the embedding space</h3>
          <p className="mt-3 max-w-3xl text-mist">
            Embeddings from the CNN’s final pooling layer were projected with PCA, t-SNE and UMAP, then clustered with a
            FlowSOM-style self-organising map and meta-clustering. Images of the same species form compact, meaningful
            groups — the structure reflects real species-specific visual cues, not visualisation artefacts.
          </p>
        </Reveal>
        <Gallery />
      </div>
    </Section>
  );
}
