"""Builds web-optimised assets from the repo's original files.
Run from anywhere:  python3 website/scripts/build_assets.py
"""
import json, os, re, shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "website"
VAL = ROOT / "Validation Code and Plots"
FISH_SRC = ROOT / "Fish Images"

FISH = {  # slug -> source file name
 "bacha":"Bacha","baim":"Baim","bele":"Bele","chanda":"Chanda","cheng":"Cheng","dairka":"Dairka",
 "dhaira":"Dhaira","dhyala-pithali":"Dhyala-pithali ","fasa":"Fasa","goti":"Goti","guchi":"Guchi",
 "itha":"Itha","jiyol":"Jiyol","kakila":"Kakila","khori":"Khori","koi":"Koi","mohola":"Mohola",
 "pabda":"Pabda","paloa-tengra":"Poala Tengra","piyali":"Piyali","puthi":"Puthi","rewa":"Rewa","veda":"Veda"}

PLOTS = {  # out name -> relative source, max width
 "cv-performance":("fish_outputs_mobilenet/plots/performance_analysis.png",2000),
 "cv-confusion":("fish_outputs_mobilenet/plots/confusion_matrix.png",2200),
 "cv-hyperparams":("fish_outputs_mobilenet/plots/hyperparameter_analysis.png",2000),
 "umap-flowsom":("fish_outputs_publication/clustering/umap_flowsom.png",2200),
 "summary":("fish_outputs_publication/visualizations/comprehensive_summary.png",2400),
 "pca":("fish_outputs_publication/dimensionality_reduction/pca_analysis.png",2000),
 "parametric-umap":("fish_outputs_publication/dimensionality_reduction/parametric_umap.png",2000),
 "rna-style":("fish_outputs_publication/visualizations/single_cell_rna_style.png",2200),
 "3d-umap":("fish_outputs_publication/3d_plots/3d_umap.png",1800),
 "3d-tsne":("fish_outputs_publication/3d_plots/3d_tsne.png",1800),
 "3d-umap-front":("fish_outputs_publication/3d_plots/3d_umap_front.png",1400),
 "3d-umap-side":("fish_outputs_publication/3d_plots/3d_umap_side.png",1400),
 "3d-umap-back":("fish_outputs_publication/3d_plots/3d_umap_back.png",1400),
 "3d-umap-diagonal":("fish_outputs_publication/3d_plots/3d_umap_diagonal.png",1400),
 "tsne":("fish_paper_plots_pro/tsne.png",1800),
 "umap":("fish_paper_plots_pro/umap.png",1800),
 "class-distribution":("fish_paper_plots_pro/class_distribution.png",2200),
 "per-class-f1":("fish_paper_plots_pro/per_class_f1_sorted.png",2200),
 "confusion-normalized":("fish_paper_plots_pro/confusion_normalized.png",2000),
 "confusion-raw":("fish_paper_plots_pro/confusion_raw.png",2000),
 "reliability":("fish_paper_plots_pro/reliability_diagram.png",1400),
 "confidence":("fish_paper_plots_pro/confidence_hist.png",1400),
 "adversarial-roc":("fish_paper_plots_pro/adversarial_roc.png",1400),
 "outlier-scores":("fish_paper_plots_pro/outlier_score_hist.png",1400),
 "val-metrics":("fish_paper_plots_pro/val_metrics_curve.png",1400),
 "train-loss":("fish_paper_plots_pro/train_loss_curve.png",1400),
 "augmentation":("fish_paper_plots_pro/original_vs_augmented.png",2400),
 "misclassified":("fish_paper_plots_pro/misclassification_gallery.png",2400),
 "outliers":("fish_paper_plots_pro/outlier_gallery.png",2400),
}

# notebook cell index -> (file name, title)
CELLS = {3:"01_mobilenetv3_nested_cv.py",6:"02_resnet50_grouped_cv.py",9:"03_augmentation_validation_plots.py",
         10:"04_gradcam_saliency.py",12:"05_nested_cv_resnet_efficientnet.py",13:"06_nested_cv_resnet50.py"}

def webp(src, dst, maxw, q=80):
    im = Image.open(src).convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, round(im.height*maxw/im.width)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=q, method=6)
    return im.size

def clean(s):  # remove personal local paths
    return re.sub(r'"/Users/[^"]*"', '"/path/to/Fish Dataset Raw"', s)

def main():
    sizes = {}
    for slug, name in FISH.items():
        sizes[slug] = webp(FISH_SRC/f"{name}.png", WEB/"public/fish"/f"{slug}.webp", 1100, 82)
    for name,(rel,mw) in PLOTS.items():
        sizes["plot:"+name] = webp(VAL/rel, WEB/"public/plots"/f"{name}.webp", mw, 78)
    json.dump(sizes, open(WEB/"src/data/image-sizes.json","w"), indent=1)

    nb = json.load(open(VAL/"Data-in-brief-data-validation.ipynb"))
    (WEB/"code").mkdir(exist_ok=True)
    (WEB/"public/downloads/code").mkdir(parents=True, exist_ok=True)
    for i,fn in CELLS.items():
        src = clean("".join(nb["cells"][i]["source"]))
        (WEB/"code"/fn).write_text(src)
        (WEB/"public/downloads/code"/fn).write_text(src)
    for c in nb["cells"]:
        if "source" in c: c["source"] = [clean(l) for l in c["source"]]
        c["outputs"] = []; c["execution_count"] = None
    json.dump(nb, open(WEB/"public/downloads/data-in-brief-data-validation.ipynb","w"), indent=1)
    print("done", sum(os.path.getsize(p) for p in (WEB/"public").rglob("*") if p.is_file())/1e6, "MB")
main()
