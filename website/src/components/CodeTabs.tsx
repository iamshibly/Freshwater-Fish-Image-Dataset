"use client";
import { useState } from "react";
import { CopyButton } from "./ui";

type Item = { file: string; title: string; tag: string; desc: string; html: string; lines: number };

export function CodeTabs({ items }: { items: Item[] }) {
  const [i, setI] = useState(0);
  const it = items[i];
  return (
    <div className="grid gap-4 lg:grid-cols-[17rem_1fr]">
      <div role="tablist" aria-orientation="vertical" className="thin-scroll flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
        {items.map((x, k) => (
          <button key={x.file} role="tab" aria-selected={i === k} onClick={() => setI(k)}
            className={`card shrink-0 px-4 py-3 text-left text-sm transition-colors lg:shrink ${i === k ? "!border-teal/60 !bg-teal/10" : "hover:border-teal/30"}`}>
            <span className="block font-semibold">{x.title}</span>
            <span className="font-mono text-[11px] text-amber">{x.tag}</span>
          </button>
        ))}
      </div>
      <div className="card min-w-0 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-3">
          <div className="min-w-0"><div className="truncate font-mono text-sm">{it.file}</div><div className="text-xs text-mist">{it.lines} lines</div></div>
          <div className="flex gap-2">
            <CopyButton text={`/downloads/code/${it.file}`} label="Copy link" />
            <a className="btn btn-ghost !py-1.5 !px-3 !text-xs" href={`/downloads/code/${it.file}`} download>Download .py ↓</a>
          </div>
        </div>
        <p className="border-b border-line px-5 py-3 text-sm text-mist">{it.desc}</p>
        <div className="code-scroll bg-[#0d1117] p-4" tabIndex={0} aria-label={`Source of ${it.file}`} dangerouslySetInnerHTML={{ __html: it.html }} />
      </div>
    </div>
  );
}
