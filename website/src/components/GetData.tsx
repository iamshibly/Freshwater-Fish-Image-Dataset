import { Section } from "./Section";
import { Reveal, CopyButton } from "./ui";
import { site } from "@/data/site";

const bibtexData = `@misc{ahmod${site.year}smallfish,
  title        = {Small Bangladeshi Fish Image and Nutrition Dataset},
  author       = {Ahmod, Tanvir and Shibly, Md. Zubayer Ahmad and Hassan, Md. Maruf},
  year         = {${site.year}},
  publisher    = {Kaggle},
  doi          = {${site.links.doi}}
}`;

const bibtex = `@inproceedings{nutrifishbd${site.year},
  title     = {A Multimodal Freshwater Fish Image Dataset with Nutritional Metadata for Computer Vision-Based Species Recognition in Bangladesh},
  author    = {${site.authors}},
  booktitle = {${site.conferenceFull}},
  year      = {${site.year}},
  note      = {Dataset and code: ${site.links.github}}
}`;

const tree = `Fish Dataset/
├── Fish Dataset Raw/         5,520 original images, 23 species folders
├── Fish Dataset Augmented/  19,868 augmented images, 23 species folders
└── nutrition_metadata_per_100g.csv`;

export function GetData() {
  return (
    <Section id="get" eyebrow="Get the data" className="!pt-0"
      title="Open for research. Download in one click."
      intro="The raw images, the augmented images and the nutrition CSV are published on Kaggle under a permanent DOI, as cited in the paper. This website only links to the archive — nothing is re-hosted here.">
      <div className="grid gap-5 lg:grid-cols-3">
        <Reveal><div className="card flex h-full flex-col p-7">
          <p className="eyebrow">Dataset</p>
          <h3 className="font-display mt-2 text-2xl font-semibold">Images + nutrition CSV</h3>
          <p className="mt-2 flex-1 text-mist">Raw and augmented images in species folders, plus per-100 g nutrition metadata. DOI: <span className="font-mono text-xs">{site.links.doi}</span></p>
          <div className="mt-6 grid gap-2">
            <a className="btn btn-primary justify-center" href={site.links.kaggle} target="_blank" rel="noopener noreferrer">Open on Kaggle (DOI) ↗</a>
            <a className="btn btn-ghost justify-center" href={site.links.drive} target="_blank" rel="noopener noreferrer">Google Drive mirror ↗</a>
          </div>
        </div></Reveal>
        <Reveal delay={80}><div className="card flex h-full flex-col p-7">
          <p className="eyebrow">Code</p>
          <h3 className="font-display mt-2 text-2xl font-semibold">Validation code & plots</h3>
          <p className="mt-2 flex-1 text-mist">Supplementary notebook, scripts and generated figures in the GitHub repository (not part of the archived release).</p>
          <div className="mt-6 grid gap-2">
            <a className="btn btn-ghost justify-center" href={site.links.github} target="_blank" rel="noopener noreferrer">GitHub repository ↗</a>
            <a className="btn btn-ghost justify-center" href={site.links.notebook} download>Notebook (.ipynb) ↓</a>
          </div>
        </div></Reveal>
        <Reveal delay={160}><div className="card flex h-full flex-col p-7">
          <p className="eyebrow">Metadata</p>
          <h3 className="font-display mt-2 text-2xl font-semibold">Nutrition table</h3>
          <p className="mt-2 flex-1 text-mist">The paper’s Table 3 (12 nutrients × 23 species) as a ready-to-use CSV, with the Paloa Tengra proxy row flagged. The archive contains the full file with additional micronutrients.</p>
          <a className="btn btn-ghost mt-6 justify-center" href={site.links.csv} download>Download CSV ↓</a>
        </div></Reveal>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <Reveal><div className="card h-full p-7">
          <h3 className="font-semibold">Folder layout</h3>
          <pre className="mt-3 overflow-x-auto font-mono text-sm leading-relaxed text-mist">{tree}</pre>
          <p className="mt-4 text-sm text-mist">Raw images are unresized and unprocessed (≈640×640 up to 4284×5712 px), so you can apply your own pipeline.</p>
        </div></Reveal>
        <Reveal delay={90}><div className="card h-full p-7">
          <div className="flex items-center justify-between"><h3 className="font-semibold">Cite the paper</h3><CopyButton text={bibtex} label="Copy BibTeX" /></div>
          <pre className="thin-scroll mt-3 overflow-x-auto rounded-lg bg-black/30 p-4 font-mono text-xs leading-relaxed text-mist">{bibtex}</pre>
          <div className="mt-5 flex items-center justify-between"><h3 className="font-semibold">Cite the dataset</h3><CopyButton text={bibtexData} label="Copy BibTeX" /></div>
          <pre className="thin-scroll mt-3 overflow-x-auto rounded-lg bg-black/30 p-4 font-mono text-xs leading-relaxed text-mist">{bibtexData}</pre>
        </div></Reveal>
      </div>

      <Reveal>
        <div className="mt-16 grid gap-8 md:grid-cols-2">
          <div>
            <h3 className="font-display text-2xl font-semibold">What you can build</h3>
            <ul className="mt-4 grid grid-cols-1 gap-x-6 gap-y-2 text-mist sm:grid-cols-2">
              {["Species recognition", "Transfer learning", "Food image recognition", "Multimodal image + tabular learning", "Nutrition-aware recommendation", "Fisheries decision support", "Biodiversity informatics", "Dataset benchmarking"].map((a) => (
                <li key={a} className="flex gap-2"><span className="text-teal">▸</span>{a}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-display text-2xl font-semibold">Limitations</h3>
            <ul className="mt-4 space-y-2 text-mist">
              <li className="flex gap-2"><span className="text-amber">▸</span>Nutrition values are compiled reference values, not lab measurements; Paloa Tengra uses a proxy species’ row.</li>
              <li className="flex gap-2"><span className="text-amber">▸</span>One two-month window (April–May 2025), mostly one district — no seasonal or regional spread.</li>
              <li className="flex gap-2"><span className="text-amber">▸</span>Class imbalance remains (43 to 763 raw images); species list follows market availability.</li>
              <li className="flex gap-2"><span className="text-amber">▸</span>Single specimens on plain backgrounds; folds split images, not sessions, so scores may be slightly inflated.</li>
            </ul>
          </div>
        </div>
      </Reveal>
    </Section>
  );
}
