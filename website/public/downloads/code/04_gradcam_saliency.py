# ==========================================================
# FIXED + BEAUTIFUL Saliency, Grad-CAM, Activation Heatmaps
# (Upsamples CAM properly, high-quality figures)
# ==========================================================

import os, math, random, warnings
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
import cv2

warnings.filterwarnings("ignore")

# -------------------------
# SETTINGS
# -------------------------
DATA_DIR = "/path/to/Fish Dataset Raw"
OUT_DIR  = "./fish_advanced_vis_fixed"
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 42
IMG_SIZE = 224
N_VIS = 12
DPI = 600

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Using device:", device)

IMG_EXT = {".jpg",".jpeg",".png",".bmp",".webp"}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 12,
    "savefig.dpi": DPI,
})

def savefig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()

# -------------------------
# Index dataset
# -------------------------
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

items, class_names, _ = index_imagefolder(DATA_DIR)
paths  = np.array([p for p,_ in items])
labels = np.array([y for _,y in items], dtype=np.int64)

print("Total images:", len(paths))
print("Total classes:", len(class_names))

# -------------------------
# Transforms
# -------------------------
val_tf = transforms.Compose([
    transforms.Resize(int(IMG_SIZE * 1.14)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

vis_tf = transforms.Compose([
    transforms.Resize(int(IMG_SIZE * 1.14)),
    transforms.CenterCrop(IMG_SIZE),
])

MEAN = np.array([0.485,0.456,0.406], dtype=np.float32)
STD  = np.array([0.229,0.224,0.225], dtype=np.float32)

def denorm_tensor(x_3hw):
    xx = x_3hw.detach().cpu().numpy().transpose(1,2,0)
    xx = (xx * STD + MEAN)
    return np.clip(xx, 0, 1)

# -------------------------
# Build model (pretrained + new head)
# NOTE: better to load YOUR trained weights if you have them.
# -------------------------
model = resnet50(weights=ResNet50_Weights.DEFAULT)
model.fc = nn.Linear(model.fc.in_features, len(class_names))
model = model.to(device)
model.eval()

# -------------------------
# Smooth / resize helpers for beautiful maps
# -------------------------
def normalize01(a):
    a = a.astype(np.float32)
    a -= a.min()
    a /= (a.max() + 1e-9)
    return a

def upsample_heatmap(heat, target_hw):
    """heat: HxW float, target_hw: (H,W). returns resized heat in [0,1]."""
    heat = normalize01(heat)
    H,W = target_hw
    heat_rs = cv2.resize(heat, (W,H), interpolation=cv2.INTER_CUBIC)
    heat_rs = normalize01(heat_rs)
    # optional smoothing
    heat_rs = cv2.GaussianBlur(heat_rs, (0,0), sigmaX=1.2, sigmaY=1.2)
    return normalize01(heat_rs)

def overlay_heatmap(img_rgb01, heat01, alpha=0.42, cmap=cv2.COLORMAP_TURBO):
    """img_rgb01: HxWx3 [0,1], heat01: HxW [0,1] same spatial size."""
    h = (heat01 * 255).astype(np.uint8)
    hm = cv2.applyColorMap(h, cmap)
    hm = cv2.cvtColor(hm, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    out = (1-alpha) * img_rgb01 + alpha * hm
    return np.clip(out, 0, 1)

# ==========================================================
# (1) SALIENCY MAP (smoothed input gradient)
# ==========================================================
def saliency_map(model, x, class_idx=None):
    model.zero_grad(set_to_none=True)
    x = x.clone().detach().requires_grad_(True)
    logits = model(x)
    pred = int(logits.argmax(dim=1).item()) if class_idx is None else int(class_idx)
    score = logits[:, pred].sum()
    score.backward()

    grad = x.grad.detach().abs().squeeze(0)   # (3,H,W)
    sal = grad.max(dim=0)[0].cpu().numpy()    # (H,W)
    sal = normalize01(sal)
    sal = cv2.GaussianBlur(sal, (0,0), 1.2)
    sal = normalize01(sal)
    return sal, pred

# ==========================================================
# (2) GRAD-CAM (returns low-res, we upsample)
# ==========================================================
class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.layer = target_layer
        self.grad = None
        self.act  = None
        self.hooks = []
        self._register()
    def _register(self):
        def fwd_hook(m, inp, out): self.act = out.detach()
        def bwd_hook(m, gin, gout): self.grad = gout[0].detach()
        self.hooks.append(self.layer.register_forward_hook(fwd_hook))
        self.hooks.append(self.layer.register_full_backward_hook(bwd_hook))
    def remove(self):
        for h in self.hooks: h.remove()
    def __call__(self, x, class_idx=None):
        self.model.zero_grad(set_to_none=True)
        logits = self.model(x)
        pred = int(logits.argmax(dim=1).item()) if class_idx is None else int(class_idx)
        score = logits[:, pred].sum()
        score.backward(retain_graph=True)
        w = self.grad.mean(dim=(2,3), keepdim=True)          # (1,C,1,1)
        cam = (w * self.act).sum(dim=1, keepdim=False)       # (1,H,W)
        cam = F.relu(cam).squeeze(0).detach().cpu().numpy()  # (H,W) e.g., 7x7
        cam = normalize01(cam)
        return cam, pred

gc = GradCAM(model, model.layer4[-1].conv3)

# ==========================================================
# (3) ACTIVATION HEATMAPS (nice top-k channels)
# ==========================================================
@torch.no_grad()
def get_activation_maps(model, x, layer):
    acts = []
    def hook(m, inp, out): acts.append(out.detach().cpu())
    h = layer.register_forward_hook(hook)
    _ = model(x)
    h.remove()
    return acts[0].squeeze(0)  # (C,H,W)

def topk_activation_maps(act_c_hw, k=16):
    C,H,W = act_c_hw.shape
    score = act_c_hw.abs().mean(dim=(1,2))
    idx = torch.topk(score, k=min(k,C)).indices.tolist()
    maps = []
    for i in idx:
        m = act_c_hw[i].numpy()
        m = normalize01(m)
        m = cv2.GaussianBlur(m, (0,0), 0.8)
        m = normalize01(m)
        maps.append(m)
    return maps

# ==========================================================
# Generate figures
# ==========================================================
vis_idx = np.random.choice(len(paths), size=min(N_VIS, len(paths)), replace=False)

for j, idx in enumerate(vis_idx):
    pth = paths[idx]
    yt  = int(labels[idx])

    img_pil = vis_tf(Image.open(pth).convert("RGB"))
    x = val_tf(img_pil).unsqueeze(0).to(device)
    base = denorm_tensor(x.squeeze(0))  # (224,224,3)

    # Saliency
    sal, pred_s = saliency_map(model, x, None)
    sal_rs = upsample_heatmap(sal, (IMG_SIZE, IMG_SIZE))
    sal_overlay = overlay_heatmap(base, sal_rs, alpha=0.40, cmap=cv2.COLORMAP_TURBO)

    # Grad-CAM
    cam_low, pred_c = gc(x, None)          # likely 7x7
    cam_rs = upsample_heatmap(cam_low, (IMG_SIZE, IMG_SIZE))
    cam_overlay = overlay_heatmap(base, cam_rs, alpha=0.42, cmap=cv2.COLORMAP_TURBO)

    # Activation maps (mid-level layer for nicer spatial detail than layer4)
    acts = get_activation_maps(model, x, model.layer3[-1].conv3)  # (C,h,w) usually 14x14
    amap = topk_activation_maps(acts, k=16)  # list of 16 maps

    # ---- Plot: 2 rows top + activation grid bottom
    fig = plt.figure(figsize=(14, 8), facecolor="white")

    ax = plt.subplot(2,3,1)
    ax.imshow(base); ax.axis("off")
    ax.set_title(f"Original\nTrue: {class_names[yt]}", pad=8)

    ax = plt.subplot(2,3,2)
    ax.imshow(sal_overlay); ax.axis("off")
    ax.set_title(f"Saliency Overlay\nPred: {class_names[pred_s]}", pad=8)

    ax = plt.subplot(2,3,3)
    ax.imshow(cam_overlay); ax.axis("off")
    ax.set_title(f"Grad-CAM Overlay\nPred: {class_names[pred_c]}", pad=8)

    # show the raw heatmaps too
    ax = plt.subplot(2,3,5)
    ax.imshow(cam_rs, cmap="magma"); ax.axis("off")
    ax.set_title("Grad-CAM Heatmap", pad=8)

    ax = plt.subplot(2,3,4)
    ax.imshow(sal_rs, cmap="magma"); ax.axis("off")
    ax.set_title("Saliency Heatmap", pad=8)

    # Activation grid (16 maps)
    grid = plt.subplot(2,3,6)
    grid.axis("off")
    # build a mini-grid inside
    gs = grid.get_subplotspec().subgridspec(4,4, wspace=0.05, hspace=0.05)
    for k in range(16):
        axk = fig.add_subplot(gs[k//4, k%4])
        axk.imshow(upsample_heatmap(amap[k], (IMG_SIZE, IMG_SIZE)), cmap="magma")
        axk.axis("off")
    grid.set_title("Activation Heatmaps (Top-16 Channels)", pad=10)

    plt.suptitle("Explainability: Saliency + Grad-CAM + Activations", fontsize=16, y=0.98)

    outp = os.path.join(OUT_DIR, f"explainability_beautiful_{j:02d}.png")
    plt.savefig(outp, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close()

gc.remove()

print("✅ Fixed and saved beautiful explainability plots to:", OUT_DIR)
