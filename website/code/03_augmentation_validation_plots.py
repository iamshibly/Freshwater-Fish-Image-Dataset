# ==========================================================
# FISH DATASET: Advanced Augmentation + Validation + PLOTS
# Mac M1 Pro + Jupyter (MPS), Duplicate-aware Grouped CV
# ==========================================================

import os, random, math
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights

from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    accuracy_score, f1_score, confusion_matrix, classification_report,
    roc_curve, auc, precision_recall_curve, average_precision_score
)
from sklearn.preprocessing import label_binarize
import umap
import cv2

# -------------------------
# SETTINGS
# -------------------------
DATA_DIR   = "/path/to/Fish Dataset Raw"
OUT_DIR    = "./fish_outputs_advanced"
os.makedirs(OUT_DIR, exist_ok=True)

SEED       = 42
IMG_SIZE   = 224
BATCH_SIZE = 24
EPOCHS     = 6
FOLDS      = 5
LR         = 3e-4

# Duplicate grouping strength (fast approximate)
USE_NEAR_DUP_GROUPING = False   # set True to try near-duplicate union within buckets
HAMMING_THR = 3                 # for near-duplicate union
BUCKET_BITS = 16                # bucketing for speed (higher -> fewer comparisons)

# Plots / galleries
NUM_OUTLIER_IMAGES = 24
NUM_MISCLS_IMAGES  = 24
NUM_GRADCAM_IMAGES = 12

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Using device:", device)

IMG_EXT = {".jpg",".jpeg",".png",".bmp",".webp"}

# -------------------------
# UTIL: index imagefolder
# -------------------------
def index_imagefolder(root):
    root = Path(root)
    classes = sorted([d.name for d in root.iterdir() if d.is_dir()])
    if not classes:
        raise ValueError("No class subfolders found.")
    class_to_idx = {c:i for i,c in enumerate(classes)}
    items = []
    for c in classes:
        for p in (root/c).rglob("*"):
            if p.is_file() and p.suffix.lower() in IMG_EXT:
                items.append((str(p), class_to_idx[c]))
    return items, classes, class_to_idx

items, class_names, class_to_idx = index_imagefolder(DATA_DIR)
paths  = np.array([p for p,_ in items])
labels = np.array([y for _,y in items], dtype=np.int64)

print("Total images:", len(paths))
print("Total classes:", len(class_names))

# -------------------------
# PLOT: Class distribution
# -------------------------
def plot_class_distribution(labels, class_names, outpath):
    counts = np.bincount(labels, minlength=len(class_names))
    plt.figure(figsize=(12,5))
    plt.bar(np.arange(len(class_names)), counts)
    plt.xticks(np.arange(len(class_names)), class_names, rotation=90, fontsize=7)
    plt.title("Class Distribution (images per class)")
    plt.tight_layout()
    plt.savefig(outpath, dpi=220)
    plt.close()

plot_class_distribution(labels, class_names, os.path.join(OUT_DIR, "class_distribution.png"))
print("Saved:", os.path.join(OUT_DIR, "class_distribution.png"))

# -------------------------
# DATASET
# -------------------------
class FishDataset(Dataset):
    def __init__(self, paths, labels, transform=None):
        self.paths = list(paths)
        self.labels = list(labels)
        self.transform = transform
    def __len__(self):
        return len(self.paths)
    def __getitem__(self, idx):
        p = self.paths[idx]
        y = int(self.labels[idx])
        img = Image.open(p).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, y, p

# -------------------------
# TRANSFORMS (online augmentation)
# -------------------------
train_tf = transforms.Compose([
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.80, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.20, contrast=0.20, saturation=0.20, hue=0.05),
    transforms.ToTensor(),
    transforms.RandomApply([transforms.GaussianBlur(kernel_size=3)], p=0.15),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize(int(IMG_SIZE * 1.14)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

# -------------------------
# MODEL BUILD
# -------------------------
def build_model(num_classes):
    m = resnet50(weights=ResNet50_Weights.DEFAULT)
    m.fc = nn.Linear(m.fc.in_features, num_classes)
    return m

# -------------------------
# EMBEDDINGS for outliers/UMAP
# -------------------------
@torch.no_grad()
def extract_embeddings(paths_subset, labels_subset):
    ds = FishDataset(paths_subset, labels_subset, transform=val_tf)
    dl = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    backbone = resnet50(weights=ResNet50_Weights.DEFAULT)
    backbone.fc = nn.Identity()
    backbone = backbone.to(device)
    backbone.eval()

    feats = []
    ys = []
    ps = []
    for x,y,p in tqdm(dl, desc="Embedding"):
        x = x.to(device)
        f = backbone(x).detach().cpu().numpy()
        feats.append(f)
        ys.append(np.array(y, dtype=np.int64))
        ps.extend(list(p))
    return np.concatenate(feats, axis=0), np.concatenate(ys, axis=0), ps

print("\n[1] Extracting embeddings for outlier detection + UMAP...")
features, labels_embed, paths_embed = extract_embeddings(paths, labels)

# -------------------------
# OUTLIER DETECTION + plot gallery
# -------------------------
print("\n[2] Outlier detection (IsolationForest)...")
iso = IsolationForest(n_estimators=400, contamination=0.02, random_state=SEED)
pred = iso.fit_predict(features)     # -1 outlier
outlier_idx = np.where(pred == -1)[0].tolist()
print("Outliers detected:", len(outlier_idx))

# Save outlier list
outlier_txt = os.path.join(OUT_DIR, "outliers.txt")
with open(outlier_txt, "w") as f:
    for i in outlier_idx:
        f.write(f"{i}\t{labels[i]}\t{class_names[labels[i]]}\t{paths[i]}\n")
print("Saved:", outlier_txt)

def make_image_grid(image_paths, outpath, title, n=24, cols=6, thumb=160):
    sel = image_paths[:min(n, len(image_paths))]
    rows = math.ceil(len(sel)/cols)
    plt.figure(figsize=(cols*2.2, rows*2.2))
    for i,p in enumerate(sel):
        ax = plt.subplot(rows, cols, i+1)
        try:
            img = Image.open(p).convert("RGB")
            img = img.resize((thumb, thumb))
            ax.imshow(img)
            ax.axis("off")
        except Exception:
            ax.axis("off")
    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=220)
    plt.close()

outlier_paths = [paths[i] for i in outlier_idx]
make_image_grid(outlier_paths, os.path.join(OUT_DIR, "outlier_gallery.png"),
                "Outlier Gallery (IsolationForest)", n=NUM_OUTLIER_IMAGES)
print("Saved:", os.path.join(OUT_DIR, "outlier_gallery.png"))

# -------------------------
# UMAP plot
# -------------------------
print("\n[3] UMAP plot...")
reducer = umap.UMAP(n_neighbors=20, min_dist=0.1, metric="cosine", random_state=SEED)
emb2d = reducer.fit_transform(features)

plt.figure(figsize=(9,7))
plt.scatter(emb2d[:,0], emb2d[:,1], c=labels, s=6, alpha=0.8)
plt.title("UMAP of Fish Dataset (ResNet50 embeddings)")
plt.tight_layout()
umap_path = os.path.join(OUT_DIR, "umap.png")
plt.savefig(umap_path, dpi=220)
plt.close()
print("Saved:", umap_path)

# -------------------------
# DUPLICATE GROUPING (dHash)
# -------------------------
def dhash_pil(img: Image.Image, hash_size=8):
    img = img.convert("L").resize((hash_size+1, hash_size), Image.Resampling.LANCZOS)
    px = np.array(img, dtype=np.int32)
    diff = px[:, 1:] > px[:, :-1]
    bits = diff.flatten().astype(np.uint8)
    h = 0
    for b in bits:
        h = (h << 1) | int(b)
    return h

def hamming(a:int, b:int):
    return (a ^ b).bit_count()

print("\n[4] Computing dHash groups...")
hashes = np.zeros(len(paths), dtype=np.uint64)
for i,p in enumerate(tqdm(paths, desc="dHash")):
    try:
        img = Image.open(p).convert("RGB")
        hashes[i] = dhash_pil(img, hash_size=8)
    except Exception:
        hashes[i] = 0

# exact grouping
hash_to_gid = {}
groups = np.zeros(len(paths), dtype=np.int64)
gid = 0
for i,h in enumerate(hashes):
    hh = int(h)
    if hh not in hash_to_gid:
        hash_to_gid[hh] = gid
        gid += 1
    groups[i] = hash_to_gid[hh]

group_sizes = Counter(groups.tolist())
dup_groups = sum(1 for g,s in group_sizes.items() if s > 1)
print(f"Unique hash groups: {gid}")
print(f"Groups with >=2 images (exact duplicates/near-duplicates): {dup_groups}")
print(f"Largest group size: {max(group_sizes.values())}")

dup_report = os.path.join(OUT_DIR, "duplicate_groups_report.txt")
with open(dup_report, "w") as f:
    f.write("group_id\tcount\n")
    for g,s in group_sizes.most_common(500):
        if s > 1:
            f.write(f"{g}\t{s}\n")
print("Saved:", dup_report)

# Optional: near-duplicate union-find within buckets (faster than all-pairs)
if USE_NEAR_DUP_GROUPING:
    print("\n[4b] Near-duplicate grouping (approx, bucketed) ...")
    parent = np.arange(len(paths), dtype=np.int64)
    rank = np.zeros(len(paths), dtype=np.int8)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a,b):
        ra, rb = find(a), find(b)
        if ra == rb: return
        if rank[ra] < rank[rb]:
            parent[ra] = rb
        elif rank[ra] > rank[rb]:
            parent[rb] = ra
        else:
            parent[rb] = ra
            rank[ra] += 1

    # bucket by top BUCKET_BITS
    buckets = defaultdict(list)
    shift = 64 - BUCKET_BITS
    for i,h in enumerate(hashes):
        key = int(h) >> shift
        buckets[key].append(i)

    # compare within bucket
    for key, idxs in tqdm(buckets.items(), desc="Bucket union"):
        if len(idxs) < 2:
            continue
        # pairwise inside bucket (bucket sizes usually small)
        for a_i in range(len(idxs)):
            a = idxs[a_i]
            ha = int(hashes[a])
            for b_i in range(a_i+1, len(idxs)):
                b = idxs[b_i]
                hb = int(hashes[b])
                if hamming(ha, hb) <= HAMMING_THR:
                    union(a,b)

    # compress to group ids
    root_to_gid = {}
    new_groups = np.zeros(len(paths), dtype=np.int64)
    ngid = 0
    for i in range(len(paths)):
        r = find(i)
        if r not in root_to_gid:
            root_to_gid[r] = ngid
            ngid += 1
        new_groups[i] = root_to_gid[r]
    groups = new_groups
    group_sizes = Counter(groups.tolist())
    dup_groups = sum(1 for g,s in group_sizes.items() if s > 1)
    print(f"Near-dup groups: {ngid} | groups with >=2: {dup_groups} | max size: {max(group_sizes.values())}")

# -------------------------
# TRAIN / EVAL HELPERS
# -------------------------
def make_weighted_sampler(y_train):
    counts = np.bincount(y_train, minlength=len(class_names))
    w = 1.0 / (counts + 1e-9)
    sample_w = w[y_train]
    return WeightedRandomSampler(
        torch.tensor(sample_w, dtype=torch.double),
        num_samples=len(y_train),
        replacement=True
    )

def train_one_epoch(model, loader, opt):
    model.train()
    total = 0.0
    for x,y,_ in loader:
        x = x.to(device)
        y = torch.tensor(y, dtype=torch.long, device=device)
        logits = model(x)
        loss = F.cross_entropy(logits, y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        total += float(loss.item()) * x.size(0)
    return total / len(loader.dataset)

@torch.no_grad()
def predict_proba(model, loader):
    model.eval()
    all_probs, all_y, all_p = [], [], []
    for x,y,p in loader:
        x = x.to(device)
        logits = model(x)
        probs = torch.softmax(logits, dim=1).detach().cpu().numpy()
        all_probs.append(probs)
        all_y.append(np.array(y, dtype=np.int64))
        all_p.extend(list(p))
    return np.vstack(all_probs), np.concatenate(all_y), all_p

# -------------------------
# ADVANCED VALIDATION: Grouped CV
# Collects: fold metrics, OOF probabilities, misclassifications
# -------------------------
print("\n[5] Grouped Cross-Validation (duplicate-aware)...")

gkf = GroupKFold(n_splits=FOLDS)
fold_acc, fold_f1 = [], []
oof_probs = np.zeros((len(paths), len(class_names)), dtype=np.float32)
oof_pred  = np.zeros(len(paths), dtype=np.int64)
oof_true  = labels.copy()
miscls_records = []  # (path, true, pred, confidence)

for fold, (tr_idx, va_idx) in enumerate(gkf.split(paths, labels, groups), start=1):
    print(f"\nFold {fold}/{FOLDS}")

    ds_tr = FishDataset(paths[tr_idx], labels[tr_idx], transform=train_tf)
    ds_va = FishDataset(paths[va_idx], labels[va_idx], transform=val_tf)

    sampler = make_weighted_sampler(labels[tr_idx])
    dl_tr = DataLoader(ds_tr, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    dl_va = DataLoader(ds_va, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = build_model(len(class_names)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)

    best_f1 = -1.0
    best_state = None

    for ep in range(1, EPOCHS+1):
        loss = train_one_epoch(model, dl_tr, opt)
        probs_va, y_va, p_va = predict_proba(model, dl_va)
        pred_va = probs_va.argmax(axis=1)

        acc = accuracy_score(y_va, pred_va)
        mf1 = f1_score(y_va, pred_va, average="macro")
        print(f"  Ep {ep:02d} | loss={loss:.4f} | val_acc={acc:.4f} | val_macroF1={mf1:.4f}")

        if mf1 > best_f1:
            best_f1 = mf1
            best_state = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}

    model.load_state_dict(best_state)

    probs_va, y_va, p_va = predict_proba(model, dl_va)
    pred_va = probs_va.argmax(axis=1)

    acc = accuracy_score(y_va, pred_va)
    mf1 = f1_score(y_va, pred_va, average="macro")

    fold_acc.append(acc)
    fold_f1.append(mf1)

    # store OOF probs back into global arrays
    oof_probs[va_idx] = probs_va
    oof_pred[va_idx]  = pred_va

    # store misclassifications with confidence
    conf = probs_va.max(axis=1)
    for pth, yt, yp, cf in zip(p_va, y_va, pred_va, conf):
        if yt != yp:
            miscls_records.append((pth, int(yt), int(yp), float(cf)))

print("\nGrouped CV done.")
print("Mean Acc:", float(np.mean(fold_acc)), "Std:", float(np.std(fold_acc)))
print("Mean MacroF1:", float(np.mean(fold_f1)), "Std:", float(np.std(fold_f1)))

# Save CV summary + report
summary_txt = os.path.join(OUT_DIR, "grouped_cv_summary.txt")
with open(summary_txt, "w") as f:
    f.write("Grouped Cross-Validation (duplicate-aware)\n")
    f.write(f"Folds: {FOLDS}\n")
    f.write(f"Accuracy: mean={np.mean(fold_acc):.4f}, std={np.std(fold_acc):.4f}\n")
    f.write(f"MacroF1: mean={np.mean(fold_f1):.4f}, std={np.std(fold_f1):.4f}\n\n")
    f.write(classification_report(oof_true, oof_pred, target_names=class_names, digits=4))
print("Saved:", summary_txt)

# -------------------------
# PLOT: Fold metrics
# -------------------------
plt.figure(figsize=(8,4))
plt.plot(range(1,FOLDS+1), fold_acc, marker="o", label="Accuracy")
plt.plot(range(1,FOLDS+1), fold_f1, marker="o", label="Macro-F1")
plt.xticks(range(1,FOLDS+1))
plt.ylim(0, 1.0)
plt.title("Fold-wise Performance (Grouped CV)")
plt.legend()
plt.tight_layout()
fold_plot = os.path.join(OUT_DIR, "fold_metrics.png")
plt.savefig(fold_plot, dpi=220)
plt.close()
print("Saved:", fold_plot)

# -------------------------
# Confusion matrix (normalized)
# -------------------------
cm = confusion_matrix(oof_true, oof_pred)
cmn = cm.astype(np.float32) / (cm.sum(axis=1, keepdims=True) + 1e-9)

plt.figure(figsize=(12,10))
plt.imshow(cmn, interpolation="nearest")
plt.title("Confusion Matrix (Normalized) - Grouped CV")
plt.colorbar()
ticks = np.arange(len(class_names))
plt.xticks(ticks, class_names, rotation=90, fontsize=7)
plt.yticks(ticks, class_names, fontsize=7)
plt.tight_layout()
cm_path = os.path.join(OUT_DIR, "confusion_matrix_normalized.png")
plt.savefig(cm_path, dpi=220)
plt.close()
print("Saved:", cm_path)

# -------------------------
# Per-class F1 bar plot
# -------------------------
rep = classification_report(oof_true, oof_pred, target_names=class_names, digits=4, output_dict=True)
per_f1 = np.array([rep[c]["f1-score"] for c in class_names])

plt.figure(figsize=(12,5))
plt.bar(np.arange(len(class_names)), per_f1)
plt.xticks(np.arange(len(class_names)), class_names, rotation=90, fontsize=7)
plt.ylim(0, 1.0)
plt.title("Per-Class F1-score (Grouped CV)")
plt.tight_layout()
perclass_path = os.path.join(OUT_DIR, "per_class_f1.png")
plt.savefig(perclass_path, dpi=220)
plt.close()
print("Saved:", perclass_path)

# -------------------------
# ROC / PR curves (micro + macro) using OOF probabilities
# -------------------------
print("\n[6] ROC/PR curves (micro/macro, One-vs-Rest)...")

Y_bin = label_binarize(oof_true, classes=np.arange(len(class_names)))
# ROC micro
fpr_micro, tpr_micro, _ = roc_curve(Y_bin.ravel(), oof_probs.ravel())
roc_auc_micro = auc(fpr_micro, tpr_micro)

# ROC macro
fpr = dict(); tpr = dict(); roc_auc = dict()
for i in range(len(class_names)):
    fpr[i], tpr[i], _ = roc_curve(Y_bin[:,i], oof_probs[:,i])
    roc_auc[i] = auc(fpr[i], tpr[i])
roc_auc_macro = float(np.mean(list(roc_auc.values())))

plt.figure(figsize=(6,5))
plt.plot(fpr_micro, tpr_micro, label=f"micro AUC={roc_auc_micro:.3f}")
plt.plot([0,1],[0,1], linestyle="--")
plt.title("ROC Curve (micro)")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.legend()
plt.tight_layout()
roc_path = os.path.join(OUT_DIR, "roc_micro.png")
plt.savefig(roc_path, dpi=220)
plt.close()
print("Saved:", roc_path)

# PR micro
prec_micro, rec_micro, _ = precision_recall_curve(Y_bin.ravel(), oof_probs.ravel())
ap_micro = average_precision_score(Y_bin, oof_probs, average="micro")

plt.figure(figsize=(6,5))
plt.plot(rec_micro, prec_micro, label=f"micro AP={ap_micro:.3f}")
plt.title("Precision-Recall Curve (micro)")
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.legend()
plt.tight_layout()
pr_path = os.path.join(OUT_DIR, "pr_micro.png")
plt.savefig(pr_path, dpi=220)
plt.close()
print("Saved:", pr_path)

# -------------------------
# Calibration / Reliability diagram (top-label confidence)
# -------------------------
print("\n[7] Calibration plot (reliability diagram)...")
conf = oof_probs.max(axis=1)
correct = (oof_pred == oof_true).astype(np.int32)

bins = np.linspace(0,1,11)
bin_ids = np.digitize(conf, bins) - 1
bin_acc = []
bin_conf = []
for b in range(10):
    mask = bin_ids == b
    if mask.sum() == 0:
        bin_acc.append(np.nan); bin_conf.append((bins[b]+bins[b+1])/2)
    else:
        bin_acc.append(correct[mask].mean())
        bin_conf.append(conf[mask].mean())

plt.figure(figsize=(6,5))
plt.plot([0,1],[0,1], linestyle="--", label="perfect")
plt.plot(bin_conf, bin_acc, marker="o", label="model")
plt.title("Reliability Diagram (Grouped CV OOF)")
plt.xlabel("Confidence")
plt.ylabel("Accuracy")
plt.ylim(0,1)
plt.legend()
plt.tight_layout()
cal_path = os.path.join(OUT_DIR, "calibration.png")
plt.savefig(cal_path, dpi=220)
plt.close()
print("Saved:", cal_path)

# -------------------------
# Misclassification gallery (highest confidence wrong preds)
# -------------------------
print("\n[8] Misclassification gallery...")
miscls_records.sort(key=lambda x: x[3], reverse=True)  # high confidence wrong first
mis_paths = [r[0] for r in miscls_records[:NUM_MISCLS_IMAGES]]

def make_miscls_grid(records, outpath, n=24, cols=6, thumb=160):
    sel = records[:min(n, len(records))]
    rows = math.ceil(len(sel)/cols)
    plt.figure(figsize=(cols*2.6, rows*2.6))
    for i,(pth,yt,yp,cf) in enumerate(sel):
        ax = plt.subplot(rows, cols, i+1)
        try:
            img = Image.open(pth).convert("RGB").resize((thumb, thumb))
            ax.imshow(img)
            ax.set_title(f"T:{class_names[yt]}\nP:{class_names[yp]}\n{cf:.2f}", fontsize=7)
            ax.axis("off")
        except Exception:
            ax.axis("off")
    plt.suptitle("Top Misclassifications (High Confidence Wrong)")
    plt.tight_layout()
    plt.savefig(outpath, dpi=220)
    plt.close()

mis_grid = os.path.join(OUT_DIR, "misclassification_gallery.png")
make_miscls_grid(miscls_records, mis_grid, n=NUM_MISCLS_IMAGES)
print("Saved:", mis_grid)

# -------------------------
# Grad-CAM (final model trained on full data quickly)
# -------------------------
print("\n[9] Grad-CAM examples (final quick model)...")

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.hooks = []
        self._register()

    def _register(self):
        def fwd_hook(module, inp, out):
            self.activations = out.detach()
        def bwd_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()
        self.hooks.append(self.target_layer.register_forward_hook(fwd_hook))
        self.hooks.append(self.target_layer.register_full_backward_hook(bwd_hook))

    def remove(self):
        for h in self.hooks:
            h.remove()

    def __call__(self, x, class_idx=None):
        self.model.zero_grad(set_to_none=True)
        logits = self.model(x)
        if class_idx is None:
            class_idx = int(logits.argmax(dim=1).item())
        score = logits[:, class_idx].sum()
        score.backward(retain_graph=True)

        w = self.gradients.mean(dim=(2,3), keepdim=True)
        cam = (w * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-9)
        return cam, logits

def train_final_model():
    ds_full = FishDataset(paths, labels, transform=train_tf)
    sampler = make_weighted_sampler(labels)
    dl = DataLoader(ds_full, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)

    m = build_model(len(class_names)).to(device)
    opt = torch.optim.AdamW(m.parameters(), lr=LR, weight_decay=1e-4)

    for ep in range(1, max(2, EPOCHS//2) + 1):
        loss = train_one_epoch(m, dl, opt)
        print(f"  Final Ep {ep:02d} loss={loss:.4f}")
    return m

final_model = train_final_model()
final_model.eval()

# Prepare samples: mix of random + some misclassified if available
cam_indices = list(np.random.choice(len(paths), size=min(NUM_GRADCAM_IMAGES, len(paths)), replace=False))
if len(miscls_records) > 0:
    # add a few misclassified examples (by path lookup)
    mis_extra = [r[0] for r in miscls_records[:min(6, len(miscls_records))]]
    p_to_i = {p:i for i,p in enumerate(paths)}
    cam_indices.extend([p_to_i[p] for p in mis_extra if p in p_to_i])
    cam_indices = cam_indices[:NUM_GRADCAM_IMAGES]

cam_outdir = os.path.join(OUT_DIR, "gradcam_examples")
os.makedirs(cam_outdir, exist_ok=True)

target_layer = final_model.layer4[-1].conv3
cam = GradCAM(final_model, target_layer)

for k, idx in enumerate(cam_indices):
    pth = paths[idx]
    yt  = int(labels[idx])

    # model input tensor
    img_t = val_tf(Image.open(pth).convert("RGB")).unsqueeze(0).to(device)
    heat, logits = cam(img_t)
    pred = int(logits.argmax(dim=1).item())

    heat = heat.squeeze().detach().cpu().numpy()  # HxW

    # overlay on original (opencv)
    orig = cv2.imread(pth)
    if orig is None:
        continue
    orig = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB)
    orig = cv2.resize(orig, (heat.shape[1], heat.shape[0]))

    heatmap = (heat * 255).astype(np.uint8)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    overlay = (0.55 * orig + 0.45 * heatmap).astype(np.uint8)
    outp = os.path.join(cam_outdir, f"gradcam_{k}_T{class_names[yt]}_P{class_names[pred]}.png")
    cv2.imwrite(outp, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

cam.remove()
print("Saved Grad-CAM overlays to:", cam_outdir)

print("\nDONE. All advanced outputs saved in:", OUT_DIR)
