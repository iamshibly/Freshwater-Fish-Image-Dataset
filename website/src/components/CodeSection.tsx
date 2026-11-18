import fs from "node:fs";
import path from "node:path";
import { codeToHtml } from "shiki";
import { Section } from "./Section";
import { CodeTabs } from "./CodeTabs";
import { site } from "@/data/site";

const files = [
  { file: "01_mobilenetv3_nested_cv.py", title: "MobileNetV3 nested CV", tag: "Paper baseline", desc: "The baseline behind Section 5: MobileNetV3-Small (ImageNet-pretrained), 5 outer × 2 inner folds, hyper-parameter search, metrics, confusion matrix and performance plots." },
  { file: "02_resnet50_grouped_cv.py", title: "ResNet50 grouped CV", tag: "Leakage check", desc: "Duplicate-aware GroupKFold using perceptual dHash grouping, with and without augmentation, plus a logistic-regression probe on embeddings." },
  { file: "03_augmentation_validation_plots.py", title: "Augmentation & diagnostic plots", tag: "Plots", desc: "Advanced augmentation, grouped CV, ROC/PR curves, calibration, t-SNE/UMAP, Isolation-Forest outliers, misclassification gallery and Grad-CAM." },
  { file: "04_gradcam_saliency.py", title: "Grad-CAM & saliency", tag: "Explainability", desc: "Saliency maps, Grad-CAM and top-k activation maps with properly up-sampled heatmaps." },
  { file: "05_nested_cv_resnet_efficientnet.py", title: "Nested CV: ResNet50 / EfficientNet-B0", tag: "Exploratory", desc: "Nested cross-validation generalised to heavier backbones with a wider hyper-parameter grid." },
  { file: "06_nested_cv_resnet50.py", title: "Nested CV: ResNet50", tag: "Exploratory", desc: "ResNet50 nested cross-validation (5 × 2) with the same reporting pipeline." },
];

export async function CodeSection() {
  const items = await Promise.all(
    files.map(async (f) => {
      const src = fs.readFileSync(path.join(process.cwd(), "code", f.file), "utf8");
      const html = await codeToHtml(src, { lang: "python", theme: "github-dark-default" });
      return { ...f, html, lines: src.split("\n").length, bytes: src.length };
    }),
  );
  return (
    <Section id="code" eyebrow="Code" className="!pt-0"
      title="Every validation script, readable here and downloadable."
      intro="The validation notebook from the project repository, split into its scripts so you can read, copy and download them. Note: the paper’s Data Availability statement lists only the images and nutrition CSV as the archived release; the paper itself documents the model, fold structure and hyper-parameter space in full so the baseline can be reproduced from the description. These scripts are supplementary and exploratory — scripts 05 and 06 are additional backbones not reported in the paper.">
      <div className="mb-8 flex flex-wrap gap-3">
        <a className="btn btn-primary" href={site.links.notebook} download>Download notebook (.ipynb) ↓</a>
        <a className="btn btn-ghost" href={site.links.githubCode} target="_blank" rel="noopener noreferrer">View on GitHub ↗</a>
      </div>
      <CodeTabs items={items} />
      <div className="card mt-8 p-6">
        <h3 className="font-semibold">Run it yourself</h3>
        <pre className="mt-3 overflow-x-auto rounded-lg bg-black/30 p-4 font-mono text-sm text-mist"><code>{`pip install torch torchvision numpy pandas scikit-learn matplotlib pillow tqdm umap-learn opencv-python

# 1. download & unzip the dataset (Kaggle DOI in "Get the data"); use the raw folder
# 2. open the notebook / script and set DATA_DIR = "/path/to/Fish Dataset Raw"
python 01_mobilenetv3_nested_cv.py`}</code></pre>
        <p className="mt-3 text-sm text-mist">Scripts auto-select Apple MPS, CUDA or CPU. Nested CV on a laptop takes hours (the reported MobileNetV3 run took ≈5 h on an Apple M-series GPU); a CUDA GPU is recommended.</p>
      </div>
    </Section>
  );
}
