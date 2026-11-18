import { Section } from "./Section";
import { Reveal } from "./ui";
import { Distribution } from "./Distribution";
import { imgSize } from "@/data/fish";

const steps = [
  { t: "Collect", d: "Photographed in real fish markets in Chapai Nawabganj and Dhaka — Bottola Hat, New Market, Horipur Bazar and Kawran Bazar." },
  { t: "Capture", d: "iPhone 15 Pro Max, 48 MP main camera with optical stabilisation; ambient market lighting, no external lights." },
  { t: "Isolate", d: "One specimen per photograph on a plain background to limit overlap and occlusion." },
  { t: "Clean", d: "Blurry, low-quality and duplicate images removed; only sharp, well-focused images kept." },
  { t: "Organise", d: "Sorted into species folders labelled with the local Bengali name and scientific name." },
  { t: "Augment", d: "Raw files stay untouched; 3–5 controlled variants per image generated separately." },
];

const specs = [
  ["Species", "23"], ["Raw images", "5,520"], ["Augmented images", "19,868"], ["Total pool", "25,388"],
  ["Resolution", "640×640 → 4284×5712 px"], ["File size", "≈38.7 KB → 1.8 MB"],
  ["Smallest class", "Goti · 43 raw"], ["Largest class", "Bacha · 763 raw"],
];

export function Dataset() {
  const aug = imgSize("plot:augmentation");
  return (
    <Section
      id="dataset"
      eyebrow="The dataset"
      title="From market stalls to a benchmark-ready resource."
      intro="Every image was captured by the authors under practical, real-market conditions — not a laboratory — so models trained on it face the variation they will meet in the field."
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

      <div className="mt-20">
        <Reveal>
          <h3 className="font-display text-2xl font-semibold md:text-3xl">Class balance: raw vs augmented</h3>
          <p className="mt-3 max-w-2xl text-mist">
            The raw set is naturally imbalanced (43 → 763 images per species). Class-dependent augmentation
            (α<sub>c</sub> = N<sub>aug</sub>/N<sub>raw</sub>) adds 2 to 4 variants per original — the most for the rarest species. Hover or tap a row for details.
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
            Gaussian blur reflect sensor noise and slight defocus — pushing models toward body shape, texture, fin
            structure and colour pattern rather than acquisition artefacts.
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
