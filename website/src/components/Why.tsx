import { Section } from "./Section";
import { Reveal } from "./ui";

const gaps = [
  { k: "≈7.2 g", t: "average animal protein per person per day in Bangladesh, against roughly 80 g/day in the United States. Small indigenous species are eaten whole, bones included." },
  { k: "≈40×", t: "spread in iron across small Bangladeshi fish (0.46 to 19.0 mg per 100 g, Byrd et al.) — exactly the difference a buyer would want to see, and currently cannot." },
  { k: "0", t: "existing Bangladeshi fish datasets that carry both images and nutrition. Composition tables have no pictures; image datasets have no composition." },
];

const contributions = [
  { n: "01", t: "A multimodal fish dataset from Bangladesh", d: "5,520 raw market images of 23 small indigenous freshwater species, each species carrying nutritional metadata, so identification and nutrition-aware analysis can run from the same files." },
  { n: "02", t: "Raw and augmented kept apart", d: "Originals at full resolution with no preprocessing; 19,868 augmented images provided separately for training or class rebalancing." },
  { n: "03", t: "A sourced nutrition record per species", d: "Energy, protein, fat, vitamins A and B12, four minerals, iron and omega-3/6 per 100 g — compiled by a practising nutritionist from five published Bangladeshi and FAO sources, released as a CSV." },
  { n: "04", t: "Validation of the data, not a leaderboard", d: "Nested cross-validation (raw images only) plus PCA, t-SNE, 2D/3D UMAP and FlowSOM-style clustering test whether labels are consistent and species separable without supervision." },
];

export function Why() {
  return (
    <>
      <Section
        id="why"
        eyebrow="Why it matters"
        title={<>A riverine nation, a protein gap, and no dataset that connects the two.</>}
        intro="“Mache Bhaate Bangali” — fish sits close to daily life here, and rivers supply most of the animal protein in the national diet. But many small species look alike on a market tray, local names shift between districts, and the figures that would justify choosing one species over another live in tables that carry no images. This dataset links the two halves."
      >
        <div className="grid gap-5 md:grid-cols-3">
          {gaps.map((g, i) => (
            <Reveal key={g.k} delay={i * 90}>
              <div className="card h-full p-7">
                <div className="font-display text-3xl font-semibold text-teal">{g.k}</div>
                <p className="mt-3 leading-relaxed text-mist">{g.t}</p>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="mt-16 grid items-start gap-10 lg:grid-cols-[1fr_1.1fr]">
          <Reveal>
            <h3 className="font-display text-2xl font-semibold md:text-3xl">What sets it apart</h3>
            <p className="mt-4 leading-relaxed text-mist">
              Compared with related Bangladeshi resources, this is the only one that joins both modalities, enabling
              pipelines that recognise a fish and retrieve its nutrition record. Anyone needing both modalities today must join them by hand on species names that are not standardised across sources.
            </p>
            <p className="mt-4 rounded-xl border border-line bg-white/[0.03] p-4 font-mono text-sm text-mist">
              I<sub>protein</sub> = Σ p<sub>sᵢ</sub> · q<sub>i</sub>
              <span className="mt-1 block font-sans text-xs opacity-70">Total protein from K fish: protein per 100 g × quantity (in 100 g units). Species-level only — an order-of-magnitude estimate for screening or recommendation, not a dietary measurement.</span>
            </p>
          </Reveal>
          <Reveal delay={100}>
            <div className="card thin-scroll overflow-x-auto">
              <table className="data">
                <thead><tr><th>Resource</th><th>Modality</th><th>Images</th><th>Classes</th></tr></thead>
                <tbody>
                  {[
                    ["SmallFishBD", "Image", "1,700", "10"],
                    ["Smartphone image dataset", "Image", "24,925", "21"],
                    ["BD freshwater fish", "Image", "4,389", "12"],
                    ["Nutrient composition (Bogard et al.)", "Tabular", "—", "55"],
                    ["Food Composition Table for Bangladesh", "Tabular", "—", "national"],
                  ].map((r) => (
                    <tr key={r[0]}>{r.map((c, i) => <td key={i} className={i === 0 ? "!text-mist" : ""}>{c}</td>)}</tr>
                  ))}
                  <tr className="text-teal">
                    {["This dataset", "Image + tabular", "5,520", "23"].map((c, i) => <td key={i} className="!font-bold !text-teal">{c}</td>)}
                  </tr>
                </tbody>
              </table>
            </div>
          </Reveal>
        </div>
      </Section>

      <section className="border-y border-line bg-deep/60">
        <div className="mx-auto max-w-6xl px-5 py-20 md:py-24">
          <Reveal>
            <p className="eyebrow">Contributions</p>
            <h2 className="font-display mt-3 text-3xl font-semibold md:text-4xl">Four things this work delivers</h2>
          </Reveal>
          <div className="mt-10 grid gap-5 md:grid-cols-2">
            {contributions.map((c, i) => (
              <Reveal key={c.n} delay={(i % 2) * 90}>
                <div className="card flex h-full gap-5 p-7">
                  <span className="font-mono text-sm text-amber">{c.n}</span>
                  <div>
                    <h3 className="text-lg font-semibold">{c.t}</h3>
                    <p className="mt-2 leading-relaxed text-mist">{c.d}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
