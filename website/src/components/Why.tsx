import { Section } from "./Section";
import { Reveal } from "./ui";

const gaps = [
  { k: "≈7.2 g", t: "animal protein per person per day in Bangladesh, versus ≈80 g/day in the US — fish is a cornerstone of the diet." },
  { k: "Image-only", t: "Existing Bangladeshi fish image datasets say what a fish is, but not what it is worth nutritionally." },
  { k: "Tabular-only", t: "Nutrient-composition tables exist for dozens of species, yet none are paired with images." },
];

const contributions = [
  { n: "01", t: "Author-curated multimodal dataset", d: "5,520 real-market images of 23 small indigenous freshwater species, paired with species-level nutritional metadata for identification and nutrition-aware analysis." },
  { n: "02", t: "Raw + augmented, ready to reuse", d: "All originals preserved without resizing or preprocessing, plus 19,868 controlled augmented images for training, class rebalancing and benchmarking." },
  { n: "03", t: "Nutrition linked to every species", d: "Energy, protein, fat, vitamins A and B12, minerals and omega-3/6 fatty acids per 100 g edible portion — reviewed by a certified nutrition professional." },
  { n: "04", t: "Rigorous baseline validation", d: "Nested cross-validation with MobileNetV3-Small plus PCA, t-SNE, 2D/3D UMAP, hierarchical and FlowSOM-style clustering show the data is learnable and consistently labelled." },
];

export function Why() {
  return (
    <>
      <Section
        id="why"
        eyebrow="Why it matters"
        title={<>A riverine nation, a protein gap, and no dataset that connects the two.</>}
        intro="“Mache Bhaate Bangali” — fish and rice make a Bengali. Yet shoppers, especially younger ones, often cannot tell local small fish apart, and nutrient knowledge rarely travels with the image. South Asia’s freshwater fish are under-represented in computer-vision resources; this dataset starts to close that gap."
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
              pipelines that recognise a fish and immediately retrieve what it offers nutritionally.
            </p>
            <p className="mt-4 rounded-xl border border-line bg-white/[0.03] p-4 font-mono text-sm text-mist">
              I<sub>protein</sub> = Σ p<sub>sᵢ</sub> · q<sub>i</sub>
              <span className="mt-1 block font-sans text-xs opacity-70">Total protein intake from K recognised fish: protein per 100 g × quantity (in 100 g units).</span>
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
                    ["Nutrient composition table", "Tabular", "—", "55"],
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
