import os, random, math
from pathlib import Path
from collections import defaultdict, Counter

import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, Subset, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights

from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

# ----------------------------
# CONFIG
# ----------------------------
DATA_DIR = "/path/to/Fish Dataset Raw"
OUT_DIR  = "./fish_outputs_grouped"
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 42
FOLDS = 5
IMG_SIZE = 224
BATCH_SIZE = 24
EPOCHS = 6
LR = 3e-4

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Using device:", device)

IMG_EXT = {".jpg",".jpeg",".png",".bmp",".webp"}

# ----------------------------
# DATASET INDEXING (paths + labels)
# ----------------------------
def index_imagefolder(root):
    root = Path(root)
    classes = sorted([d.name for d in root.iterdir() if d.is_dir()])
    class_to_idx = {c:i for i,c in enumerate(classes)}

    items = []
    for c in classes:
        for p in (root/c).rglob("*"):
            if p.is_file() and p.suffix.lower() in IMG_EXT:
                items.append((str(p), class_to_idx[c]))
    return items, classes, class_to_idx

items, class_names, class_to_idx = index_imagefolder(DATA_DIR)
print("Total images:", len(items))
print("Total classes:", len(class_names))

paths = np.array([p for p,_ in items])
labels = np.array([y for _,y in items])

# ----------------------------
# A) PERCEPTUAL HASH (dHash) for near-duplicate grouping
# ----------------------------
def dhash_pil(img: Image.Image, hash_size=8):
    # dHash: resize to (hash_size+1, hash_size), compare adjacent pixels horizontally
    img = img.convert("L").resize((hash_size+1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.array(img, dtype=np.int32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    # pack bits into int
    bit_string = diff.flatten().astype(np.uint8)
    h = 0
    for b in bit_string:
        h = (h << 1) | int(b)
    return h

def hamming(a:int, b:int):
    return (a ^ b).bit_count()

print("\n[1/4] Computing perceptual hashes (dHash)...")
hashes = np.zeros(len(paths), dtype=np.uint64)

for i,p in enumerate(tqdm(paths)):
    try:
        img = Image.open(p).convert("RGB")
        hashes[i] = dhash_pil(img, hash_size=8)
    except Exception:
        hashes[i] = 0

# Cluster into groups using exact hash match (fast, safe)
# (If you want approximate matching (hamming <= 3), tell me; it’s heavier.)
hash_to_gid = {}
groups = np.zeros(len(paths), dtype=np.int64)
gid = 0
for i,h in enumerate(hashes):
    if int(h) not in hash_to_gid:
        hash_to_gid[int(h)] = gid
        gid += 1
    groups[i] = hash_to_gid[int(h)]

num_groups = gid
print(f"Unique hash groups: {num_groups}")
# Show how many groups have duplicates
group_sizes = Counter(groups.tolist())
dup_groups = sum(1 for g,s in group_sizes.items() if s > 1)
max_group = max(group_sizes.values())
print(f"Groups with >=2 images (exact duplicates/near-duplicates): {dup_groups}")
print(f"Largest group size: {max_group}")

# Save a quick report
dup_report = os.path.join(OUT_DIR, "duplicate_groups_report.txt")
with open(dup_report, "w") as f:
    f.write("group_id\tcount\n")
    for g,s in group_sizes.most_common(200):
        if s > 1:
            f.write(f"{g}\t{s}\n")
print("Saved:", dup_report)

# ----------------------------
# Torch Dataset
# ----------------------------
class FishDataset(Dataset):
    def __init__(self, paths, labels, transform=None):
        self.paths = list(paths)
        self.labels = list(labels)
        self.transform = transform
    def __len__(self):
        return len(self.paths)
    def __getitem__(self, idx):
        p = self.paths[idx]
        y = self.labels[idx]
        img = Image.open(p).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, y, p

# ----------------------------
# Transforms
# ----------------------------
train_tf_aug = transforms.Compose([
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8,1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.20, contrast=0.20, saturation=0.20, hue=0.05),
    transforms.ToTensor(),
    transforms.RandomApply([transforms.GaussianBlur(kernel_size=3)], p=0.15),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

train_tf_noaug = transforms.Compose([
    transforms.Resize(int(IMG_SIZE*1.14)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize(int(IMG_SIZE*1.14)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

# ----------------------------
# Helper: class-balanced sampler
# ----------------------------
def make_weighted_sampler(y_train):
    counts = np.bincount(y_train, minlength=len(class_names))
    w = 1.0 / (counts + 1e-9)
    sample_w = w[y_train]
    return WeightedRandomSampler(torch.tensor(sample_w, dtype=torch.double),
                                 num_samples=len(y_train),
                                 replacement=True)

# ----------------------------
# Model
# ----------------------------
def build_model(num_classes):
    m = resnet50(weights=ResNet50_Weights.DEFAULT)
    m.fc = nn.Linear(m.fc.in_features, num_classes)
    return m

@torch.no_grad()
def evaluate(model, loader):
    model.eval()
    yt, yp = [], []
    for x,y,_ in loader:
        x = x.to(device)
        logits = model(x)
        pred = logits.argmax(1).cpu().numpy()
        yt.append(np.array(y))
        yp.append(pred)
    yt = np.concatenate(yt)
    yp = np.concatenate(yp)
    return accuracy_score(yt, yp), f1_score(yt, yp, average="macro"), yt, yp

def train_one_epoch(model, loader, opt):
    model.train()
    total = 0.0
    for x,y,_ in loader:
        x = x.to(device)
        y = torch.tensor(y, device=device)
        logits = model(x)
        loss = F.cross_entropy(logits, y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        total += float(loss.item()) * x.size(0)
    return total / len(loader.dataset)

# ----------------------------
# B) GROUPED CROSS-VALIDATION
# ----------------------------
print("\n[2/4] Grouped Cross-Validation (GroupKFold) to prevent duplicate leakage...")

gkf = GroupKFold(n_splits=FOLDS)

def run_grouped_cv(use_augmentation: bool):
    fold_metrics = []
    all_true, all_pred = [], []

    for fold,(tr_idx, va_idx) in enumerate(gkf.split(paths, labels, groups), start=1):
        train_tf = train_tf_aug if use_augmentation else train_tf_noaug

        ds_train = FishDataset(paths[tr_idx], labels[tr_idx], transform=train_tf)
        ds_val   = FishDataset(paths[va_idx], labels[va_idx], transform=val_tf)

        sampler = make_weighted_sampler(labels[tr_idx])

        # ✅ Jupyter-safe: num_workers=0
        dl_train = DataLoader(ds_train, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
        dl_val   = DataLoader(ds_val, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

        model = build_model(len(class_names)).to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)

        best_f1, best_state = -1.0, None
        for ep in range(1, EPOCHS+1):
            loss = train_one_epoch(model, dl_train, opt)
            acc, mf1, _, _ = evaluate(model, dl_val)
            print(f"[{'AUG' if use_augmentation else 'NOAUG'}] Fold {fold}/{FOLDS} Ep {ep:02d} "
                  f"loss={loss:.4f} val_acc={acc:.4f} val_macroF1={mf1:.4f}")
            if mf1 > best_f1:
                best_f1 = mf1
                best_state = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}

        model.load_state_dict(best_state)
        acc, mf1, yt, yp = evaluate(model, dl_val)
        fold_metrics.append((acc, mf1))
        all_true.append(yt); all_pred.append(yp)

    all_true = np.concatenate(all_true)
    all_pred = np.concatenate(all_pred)

    mean_acc = float(np.mean([m[0] for m in fold_metrics]))
    std_acc  = float(np.std([m[0] for m in fold_metrics]))
    mean_f1  = float(np.mean([m[1] for m in fold_metrics]))
    std_f1   = float(np.std([m[1] for m in fold_metrics]))

    return (mean_acc, std_acc, mean_f1, std_f1, all_true, all_pred)


# Run BOTH: no augmentation vs augmentation (strong evidence for the paper)
noaug_res = run_grouped_cv(use_augmentation=False)
aug_res   = run_grouped_cv(use_augmentation=True)

def write_summary(tag, res):
    mean_acc, std_acc, mean_f1, std_f1, yt, yp = res
    p = os.path.join(OUT_DIR, f"grouped_cv_summary_{tag}.txt")
    with open(p, "w") as f:
        f.write(f"Grouped CV ({tag})\n")
        f.write(f"Mean Acc: {mean_acc:.4f} ± {std_acc:.4f}\n")
        f.write(f"Mean MacroF1: {mean_f1:.4f} ± {std_f1:.4f}\n\n")
        f.write(classification_report(yt, yp, target_names=class_names, digits=4))
    print("Saved:", p)

print("\nGrouped CV Summary (NO AUG):", noaug_res[:4])
print("Grouped CV Summary (AUG):   ", aug_res[:4])

write_summary("noaug", noaug_res)
write_summary("aug",   aug_res)

# Confusion matrices
def save_confmat(tag, yt, yp):
    cm = confusion_matrix(yt, yp)
    cmn = cm.astype(np.float32) / (cm.sum(axis=1, keepdims=True)+1e-9)
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12,10))
    plt.imshow(cmn, interpolation="nearest")
    plt.title(f"Confusion Matrix (Normalized) - {tag}")
    plt.colorbar()
    ticks = np.arange(len(class_names))
    plt.xticks(ticks, class_names, rotation=90, fontsize=7)
    plt.yticks(ticks, class_names, fontsize=7)
    plt.tight_layout()
    outp = os.path.join(OUT_DIR, f"confusion_matrix_{tag}.png")
    plt.savefig(outp, dpi=220)
    plt.close()
    print("Saved:", outp)

save_confmat("noaug", noaug_res[4], noaug_res[5])
save_confmat("aug",   aug_res[4],   aug_res[5])

# ----------------------------
# C) ADVERSARIAL VALIDATION (distribution shift / split detect)
# Train a classifier to distinguish Train vs Val based on embeddings.
# If it gets >> 0.5 accuracy, your split distributions differ.
# ----------------------------
print("\n[3/4] Adversarial Validation on embeddings (train vs val separability)...")

@torch.no_grad()
def extract_embeddings_for_indices(idxs):
    tf = val_tf
    ds = FishDataset(paths[idxs], labels[idxs], transform=tf)
    dl = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    backbone = resnet50(weights=ResNet50_Weights.DEFAULT)
    backbone.fc = nn.Identity()
    backbone = backbone.to(device)
    backbone.eval()

    feats = []
    for x,_,_ in tqdm(dl, desc="Embedding"):
        x = x.to(device)
        f = backbone(x).detach().cpu().numpy()
        feats.append(f)
    return np.concatenate(feats, axis=0)

# Use one fold split as probe (fold 1)
(tr_idx, va_idx) = next(iter(gkf.split(paths, labels, groups)))
X_tr = extract_embeddings_for_indices(tr_idx)
X_va = extract_embeddings_for_indices(va_idx)
X = np.vstack([X_tr, X_va])
y_adv = np.array([0]*len(X_tr) + [1]*len(X_va))

clf = make_pipeline(StandardScaler(with_mean=True), LogisticRegression(max_iter=2000, n_jobs=None))
clf.fit(X, y_adv)
adv_pred = clf.predict(X)
adv_acc = accuracy_score(y_adv, adv_pred)

print(f"Adversarial validation accuracy (0=train,1=val): {adv_acc:.4f}")
print("Interpretation:")
print("- ~0.50 = train/val distributions are similar (good)")
print("- >0.60 = noticeable shift (review split strategy / leakage / source bias)")

# ----------------------------
# D) Optional: save top duplicate groups for manual inspection
# ----------------------------
print("\n[4/4] Saving example file lists for duplicate groups (top 30 groups with duplicates)...")
dup_groups_sorted = [g for g,s in group_sizes.most_common() if s > 1][:30]

dup_examples_path = os.path.join(OUT_DIR, "duplicate_group_examples.txt")
with open(dup_examples_path, "w") as f:
    for g in dup_groups_sorted:
        idxs = np.where(groups == g)[0]
        f.write(f"\nGROUP {g} (count={len(idxs)}):\n")
        for i in idxs[:20]:
            f.write(f"  {paths[i]} | label={class_names[labels[i]]}\n")
print("Saved:", dup_examples_path)

print("\nDONE. Outputs saved to:", OUT_DIR)
