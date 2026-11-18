"use client";
import { useEffect, useState } from "react";
import { nav, site } from "@/data/site";

export function Nav() {
  const [active, setActive] = useState("");
  const [open, setOpen] = useState(false);
  const [solid, setSolid] = useState(false);
  useEffect(() => {
    const onScroll = () => setSolid(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: "-45% 0px -50% 0px" },
    );
    nav.forEach((n) => { const el = document.getElementById(n.id); if (el) io.observe(el); });
    return () => { window.removeEventListener("scroll", onScroll); io.disconnect(); };
  }, []);
  return (
    <header className={`fixed inset-x-0 top-0 z-40 transition-all ${solid || open ? "border-b border-line bg-ink/80 backdrop-blur-xl" : ""}`}>
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
        <a href="#top" className="flex items-center gap-2.5 font-display text-lg font-semibold">
          <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden><path d="M3 16c5-8 13-9 19-4l7-4-2 8 2 8-7-4c-6 5-14 4-19-4z" fill="#2dd4bf"/><circle cx="9" cy="14.5" r="1.4" fill="#04141a"/></svg>
          {site.name}
        </a>
        <nav className="hidden items-center gap-1 lg:flex" aria-label="Sections">
          {nav.map((n) => (
            <a key={n.id} href={`#${n.id}`} className={`rounded-full px-3 py-1.5 text-sm transition-colors ${active === n.id ? "bg-white/10 text-white" : "text-mist hover:text-white"}`}>{n.label}</a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <a href={site.links.drive} target="_blank" rel="noopener noreferrer" className="btn btn-primary !py-2 !px-4 !text-sm">Download</a>
          <button className="btn btn-ghost !px-3 !py-2 lg:hidden" aria-label="Menu" aria-expanded={open} onClick={() => setOpen(!open)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d={open ? "M6 6l12 12M18 6L6 18" : "M4 7h16M4 12h16M4 17h16"} /></svg>
          </button>
        </div>
      </div>
      {open && (
        <nav className="border-t border-line bg-ink/95 px-5 pb-4 lg:hidden" aria-label="Mobile sections">
          {nav.map((n) => (
            <a key={n.id} href={`#${n.id}`} onClick={() => setOpen(false)} className="block py-3 text-mist hover:text-white">{n.label}</a>
          ))}
        </nav>
      )}
    </header>
  );
}
