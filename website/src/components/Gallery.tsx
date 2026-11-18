"use client";
import { useCallback, useEffect, useState } from "react";
import { imgSize } from "@/data/fish";

type Item = { id: string; title: string; note: string };
const tabs: { label: string; items: Item[] }[] = [
  { label: "Performance", items: [
    { id: "cv-performance", title: "Nested-CV performance analysis", note: "Fold-wise scores, score distributions, per-class F1 and training curves." },
    { id: "cv-confusion", title: "Confusion matrix", note: "Aggregated over outer folds." },
    { id: "cv-hyperparams", title: "Hyper-parameter selection", note: "Configurations chosen by the inner loop." },
    { id: "per-class-f1", title: "Per-class F1, sorted", note: "Which species are easiest and hardest." },
    { id: "confusion-normalized", title: "Normalised confusion matrix", note: "Duplicate-aware grouped-CV run, row-normalised." },
  ]},
  { label: "Embeddings", items: [
    { id: "summary", title: "Comprehensive visualisation summary", note: "PCA, t-SNE, UMAP, 3D UMAP, class distribution and feature correlation." },
    { id: "umap-flowsom", title: "UMAP + FlowSOM-style clustering", note: "Labels, meta-clusters, SOM grid, network, composition heatmap and dendrogram." },
    { id: "pca", title: "PCA analysis", note: "Global linear structure of the embeddings." },
    { id: "parametric-umap", title: "Parametric UMAP", note: "Learned, reusable 2D mapping." },
    { id: "tsne", title: "t-SNE", note: "Local-neighbourhood view." },
    { id: "umap", title: "UMAP", note: "Balance of local and global structure." },
    { id: "rna-style", title: "Single-cell-style view", note: "Embedding drawn with single-cell-genomics conventions." },
  ]},
  { label: "3D views", items: [
    { id: "3d-umap", title: "3D UMAP", note: "Species form separated strands in three dimensions." },
    { id: "3d-tsne", title: "3D t-SNE", note: "" },
    { id: "3d-umap-front", title: "3D UMAP · front", note: "" },
    { id: "3d-umap-side", title: "3D UMAP · side", note: "" },
    { id: "3d-umap-back", title: "3D UMAP · back", note: "" },
    { id: "3d-umap-diagonal", title: "3D UMAP · diagonal", note: "" },
  ]},
  { label: "Diagnostics", items: [
    { id: "reliability", title: "Reliability diagram", note: "Calibration of predicted confidence." },
    { id: "confidence", title: "Confidence histogram", note: "" },
    { id: "adversarial-roc", title: "ROC curves (micro / macro)", note: "One-vs-rest ROC from out-of-fold predictions." },
    { id: "outlier-scores", title: "Outlier score histogram", note: "Isolation Forest scores on ResNet50 embeddings." },
    { id: "val-metrics", title: "Validation metric curve", note: "" },
    { id: "train-loss", title: "Training loss curve", note: "" },
    { id: "misclassified", title: "Misclassification gallery", note: "Errors tend to be visually similar species." },
    { id: "outliers", title: "Outlier gallery", note: "Most atypical images flagged for review." },
  ]},
];

export function Gallery() {
  const [t, setT] = useState(0);
  const [open, setOpen] = useState<Item | null>(null);
  const items = tabs[t].items;
  const step = useCallback((d: number) => {
    setOpen((cur) => { if (!cur) return cur; const i = items.findIndex((x) => x.id === cur.id); return items[(i + d + items.length) % items.length]; });
  }, [items]);
  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(null); if (e.key === "ArrowRight") step(1); if (e.key === "ArrowLeft") step(-1); };
    window.addEventListener("keydown", h);
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", h); document.body.style.overflow = ""; };
  }, [open, step]);
  return (
    <div className="mt-8">
      <div role="tablist" className="flex flex-wrap gap-2">
        {tabs.map((x, i) => (
          <button key={x.label} role="tab" aria-selected={t === i} onClick={() => setT(i)} className={`rounded-full border px-4 py-1.5 text-sm ${t === i ? "border-teal bg-teal text-ink" : "border-line text-mist hover:text-white"}`}>{x.label}</button>
        ))}
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((it) => (
          <button key={it.id} onClick={() => setOpen(it)} className="card group overflow-hidden text-left transition-colors hover:border-teal/40">
            <div className="flex aspect-[4/3] items-center justify-center overflow-hidden bg-white p-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/plots/${it.id}.webp`} alt={it.title} loading="lazy" className="max-h-full max-w-full object-contain transition-transform duration-500 group-hover:scale-[1.03]" />
            </div>
            <div className="p-4"><h4 className="text-sm font-semibold">{it.title}</h4>{it.note && <p className="mt-1 text-xs text-mist">{it.note}</p>}</div>
          </button>
        ))}
      </div>
      {open && (() => { const s = imgSize("plot:" + open.id); return (
        <div className="fixed inset-0 z-50 flex flex-col bg-black/90 p-4 backdrop-blur" onClick={() => setOpen(null)} role="dialog" aria-modal="true" aria-label={open.title}>
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 pb-3" onClick={(e) => e.stopPropagation()}>
            <div><h4 className="font-semibold">{open.title}</h4>{open.note && <p className="text-xs text-mist">{open.note}</p>}</div>
            <div className="flex gap-2">
              <button className="btn btn-ghost !px-3 !py-1.5" onClick={() => step(-1)} aria-label="Previous">←</button>
              <button className="btn btn-ghost !px-3 !py-1.5" onClick={() => step(1)} aria-label="Next">→</button>
              <a className="btn btn-ghost !px-3 !py-1.5" href={`/plots/${open.id}.webp`} target="_blank" rel="noopener noreferrer">Open ↗</a>
              <button className="btn btn-ghost !px-3 !py-1.5" onClick={() => setOpen(null)} aria-label="Close">✕</button>
            </div>
          </div>
          <div className="min-h-0 flex-1 overflow-auto" onClick={(e) => e.stopPropagation()}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`/plots/${open.id}.webp`} width={s.w} height={s.h} alt={open.title} className="mx-auto max-h-full max-w-full rounded-lg bg-white object-contain" />
          </div>
        </div>); })()}
    </div>
  );
}
