import { Section } from "./Section";
import { Reveal } from "./ui";
import { Distribution } from "./Distribution";
import { imgSize } from "@/data/fish";

const steps = [
  { t: "Collect", d: "Repeated visits in April–May 2025 to Bottola Hat, New Market and Horipur Bazar (Chapai Nawabganj) and Kawran Bazar (Dhaka); whatever small species were on sale that day were photographed." },
  { t: "Capture", d: "iPhone 15 Pro Max, 48 MP main camera with optical stabilisation; ambient market lighting, no external lights." },
  { t: "Isolate", d: "One specimen per photograph on a plain background to limit overlap and occlusion." },
  { t: "Clean", d: "Blurred, poorly exposed and duplicate frames discarded; accepted images sorted into species folders." },
  { t: "Name", d: "Market names matched to scientific names against Rahman’s Freshwater Fishes of Bangladesh before any nutrition value was looked up." },
  { t: "Augment", d: "Raw files stay untouched; augmented copies (4 per image for 21 classes) are generated and released separately." },
];

const specs = [
  ["Species", "23"], ["Raw images", "5,520"], ["Augmented images", "19,868"], ["Total pool", "25,388"],
  ["Resolution", "640×640 → 4284×5712 px"], ["Collected", "April–May 2025"],
  ["Smallest class", "Goti · 43 raw"], ["Largest class", "Bacha · 763 raw"],
];

export function Dataset() {
  const aug = imgSize("plot:augmentation");
  const pipe = imgSize("plot:pipeline");
  return (
    <Section
      id="dataset"
      eyebrow="The dataset"
      title="From market stalls to a benchmark-ready resource."
      intro="Every image was captured by the authors under practical, real-market conditions — not a laboratory. The species list follows market availability, not taxonomy: read it as a sample of what these markets sell, not of Bangladeshi freshwater fish as a whole."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {specs.map(([k, v], i) => (
          <Reveal key={k} delay={i * 40}>
            <div className="card px-5 py-4">
              <div className="text-xs uppercase tracking-wider text-mist/80">{k}</div>
              <div className="mt-1 font-display text-xl font-semibold">{v}</div>
            </div>
          </Reveal>
        ))}
      </div>

      <ol className="mt-14 grid gap-4 md:grid-cols-3">
        {steps.map((s, i) => (
          <Reveal key={s.t} delay={(i % 3) * 80}>
            <li className="card h-full list-none p-6">
              <span className="font-mono text-xs text-teal">STEP {i + 1}</span>
              <h3 className="mt-1 text-lg font-semibold">{s.t}</h3>
              <p className="mt-2 text-sm leading-relaxed text-mist">{s.d}</p>
            </li>
          </Reveal>
        ))}
      </ol>

      <Reveal>
        <figure className="card mt-16 grid items-center gap-6 p-5 md:grid-cols-[1.1fr_1fr] md:p-8">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/plots/pipeline.webp" width={pipe.w} height={pipe.h} loading="lazy" alt="Pipeline: image and nutrition branches join on the species label into the released dataset, which feeds baseline validation and feature-space analysis" className="h-auto w-full rounded-xl bg-white" />
          <figcaption>
            <h3 className="font-display text-2xl font-semibold">How the two modalities fit together</h3>
            <p className="mt-3 text-mist">The image branch and the nutrition branch are joined on the species label. Raw and augmented folders are released separately, and <strong className="text-foam">only the raw folder feeds the validation</strong> — no augmented image enters any fold.</p>
            <p className="mt-2 text-xs text-mist/70">Figure 1 of the paper.</p>
          </figcaption>
        </figure>
      </Reveal>

      <div className="mt-20">
        <Reveal>
          <h3 className="font-display text-2xl font-semibold md:text-3xl">Class balance: raw vs augmented</h3>
          <p className="mt-3 max-w-2xl text-mist">
            The raw set is naturally imbalanced (43 → 763 images per species). Class-dependent augmentation
            (α<sub>c</sub> = N<sub>aug</sub>/N<sub>raw</sub>) is 4 for 21 of the 23 classes, 3 for Cheng and 2 for Bacha — the two largest, which needed less expansion. Hover or tap a row for details.
          </p>
        </Reveal>
        <Distribution />
      </div>

      <div className="mt-20 grid items-center gap-10 lg:grid-cols-2">
        <Reveal>
          <h3 className="font-display text-2xl font-semibold md:text-3xl">Controlled augmentation</h3>
          <p className="mt-4 leading-relaxed text-mist">
            Brightness, contrast, hue and saturation shifts mimic lighting and white-balance changes. Horizontal and
            vertical flips and rotation (≈ ±45°) remove dependence on a fixed orientation. Noise injection and mild
            Gaussian blur cover sensor noise, defocus and motion blur — pushing models toward body shape, texture,
            fin structure and colour pattern rather than the conditions of one photograph.
          </p>
        </Reveal>
        <Reveal delay={100}>
          <figure className="card overflow-hidden p-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/plots/augmentation.webp" width={aug.w} height={aug.h} loading="lazy" alt="Ten original market photographs above their augmented counterparts" className="h-auto w-full rounded-xl" />
            <figcaption className="px-3 py-2 text-xs text-mist">Originals (top) and augmented variants (bottom).</figcaption>
          </figure>
        </Reveal>
      </div>
    </Section>
  );
}
