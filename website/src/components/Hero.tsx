import { site } from "@/data/site";
import { fish } from "@/data/fish";
import { CountUp } from "./ui";

export function Hero() {
  const strip = [...fish, ...fish];
  return (
    <div id="top" className="bg-river relative overflow-hidden pt-28 md:pt-36">
      <div className="mx-auto max-w-6xl px-5">
        <div className="inline-flex items-center gap-2 rounded-full border border-line bg-white/5 px-4 py-1.5 text-sm text-mist">
          <span className="h-2 w-2 rounded-full bg-amber" />
          Accepted at <strong className="text-foam">{site.conference}</strong>
          <span className="opacity-40">·</span> {site.dates}
        </div>
        <p className="mt-3 max-w-2xl text-sm text-mist/80">{site.conferenceFull} — {site.venue}</p>
        <h1 className="font-display mt-7 max-w-4xl text-5xl font-semibold leading-[1.05] md:text-7xl">
          <span className="grad-text">{site.name}</span>
          <br />
          <span className="text-3xl font-normal text-foam/90 md:text-5xl">Freshwater fish, seen and nourished.</span>
        </h1>
        <p className="mt-7 max-w-2xl text-lg leading-relaxed text-mist md:text-xl">
          An image dataset of small indigenous Bangladeshi fish, with every species paired to a nutrition record —
          <strong className="text-foam"> 23 species</strong>, photographed in working markets, with a
          nested cross-validation baseline that tests whether the labels hold up.
        </p>
        <div className="mt-9 flex flex-wrap gap-3">
          <a className="btn btn-primary" href={site.links.kaggle} target="_blank" rel="noopener noreferrer">Download dataset ↓</a>
          <a className="btn btn-ghost" href="#paper">Read the paper</a>
          <a className="btn btn-ghost" href={site.links.github} target="_blank" rel="noopener noreferrer">GitHub ↗</a>
          
        </div>

        <p className="mt-8 max-w-3xl text-sm leading-relaxed text-mist">
          {site.authorList.map((a, i) => (
            <span key={a.name}>{a.name}<sup>{a.aff}{"corresponding" in a && a.corresponding ? "⋆" : ""}</sup>{i < site.authorList.length - 1 ? ", " : ""}</span>
          ))}
          <br />
          <span className="text-mist/70">{site.affiliations.map((x, i) => `${i + 1} ${x}`).join(" · ")}</span>
        </p>

        <dl className="mt-12 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-line bg-line md:grid-cols-4">
          {[
            { n: site.stats.species, l: "fish species" },
            { n: site.stats.raw, l: "raw market images" },
            { n: site.stats.augmented, l: "augmented images" },
            { n: 12, l: "nutrients per 100 g" },
          ].map((s) => (
            <div key={s.l} className="bg-deep/90 px-5 py-6">
              <dd className="font-display text-3xl font-semibold text-white md:text-4xl"><CountUp to={s.n} /></dd>
              <dt className="mt-1 text-sm text-mist">{s.l}</dt>
            </div>
          ))}
        </dl>
      </div>

      <div className="marquee relative mt-16 overflow-hidden pb-10" aria-label="Samples of the 23 species">
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-24 bg-gradient-to-r from-ink to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-24 bg-gradient-to-l from-ink to-transparent" />
        <div className="marquee-track">
          {strip.map((f, i) => (
            <figure key={i} className="relative h-40 w-72 shrink-0 overflow-hidden rounded-xl border border-line md:h-48 md:w-80" aria-hidden={i >= fish.length}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/fish/${f.slug}.webp`} alt={i < fish.length ? `${f.name} (${f.sci})` : ""} loading={i < 6 ? "eager" : "lazy"} className="h-full w-full object-cover" />
              <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 to-transparent px-3 pb-2 pt-8 text-xs">
                <span className="font-semibold">{f.name}</span> <em className="text-mist">{f.sci}</em>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </div>
  );
}
