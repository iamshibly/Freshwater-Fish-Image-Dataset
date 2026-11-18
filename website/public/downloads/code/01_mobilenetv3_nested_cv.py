# ===============================
# NESTED CROSS-VALIDATION PIPELINE
# MOBILENET V3 - BALANCED RESULTS
# FOR DATA IN BRIEF PUBLICATION
# ===============================

import os
import re
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import time
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

from torch.utils.data import Dataset, DataLoader, Subset, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix, 
                            classification_report, precision_score, recall_score,
                            balanced_accuracy_score)

# ===============================
# SETTINGS
# ===============================

DATA_DIR = "/path/to/Fish Dataset Raw"
OUTPUT_DIR = "./fish_outputs_mobilenet"
OUTER_FOLDS = 5
INNER_FOLDS = 2
RANDOM_SEED = 42
IMG_SIZE = 224
BATCH_SIZE = 32

# Set random seeds
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "plots"), exist_ok=True)

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

print("="*70)
print("NESTED CROSS-VALIDATION WITH MOBILENET V3")
print("Bangladesh Fish Dataset - Data in Brief Publication")
print("="*70)
print(f"Device: {device}")
print(f"Outer Folds: {OUTER_FOLDS}")
print(f"Inner Folds: {INNER_FOLDS}")
print("="*70)


# ===============================
# MODEL DEFINITION
# ===============================

class MobileNetV3Classifier(nn.Module):
    """
    MobileNetV3-Small with custom classifier
    ~2.5M parameters - Good balance between size and performance
    """
    def __init__(self, num_classes, dropout=0.3, pretrained=True):
        super().__init__()
        
        if pretrained:
            self.backbone = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
        else:
            self.backbone = mobilenet_v3_small(weights=None)
        
        # Freeze early layers for better generalization (optional - can reduce overfitting)
        # Uncomment below to freeze first few layers:
        # for param in list(self.backbone.parameters())[:-20]:
        #     param.requires_grad = False
        
        in_features = self.backbone.classifier[0].in_features
        
        self.backbone.classifier = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.Hardswish(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.Hardswish(),
            nn.Dropout(dropout),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)


def count_parameters(model):
    """Count trainable parameters"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# Test model
test_model = MobileNetV3Classifier(num_classes=23, pretrained=True)
n_params = count_parameters(test_model)
print(f"\nModel: MobileNetV3-Small")
print(f"Trainable Parameters: {n_params:,} ({n_params/1e6:.2f}M)")
del test_model


# ===============================
# HYPERPARAMETER SEARCH SPACE
# ===============================

HYPERPARAMETER_GRID = [
    {
        'name': 'Config_1',
        'lr': 1e-4,
        'weight_decay': 1e-4,
        'epochs': 4,
        'dropout': 0.3,
        'label_smoothing': 0.1,
    },
    {
        'name': 'Config_2',
        'lr': 3e-4,
        'weight_decay': 1e-5,
        'epochs': 4,
        'dropout': 0.4,
        'label_smoothing': 0.05,
    },
    {
        'name': 'Config_3',
        'lr': 5e-4,
        'weight_decay': 5e-5,
        'epochs': 3,
        'dropout': 0.35,
        'label_smoothing': 0.1,
    },
]

print("\nHyperparameter Configurations:")
for hp in HYPERPARAMETER_GRID:
    print(f"  {hp['name']}: lr={hp['lr']}, wd={hp['weight_decay']}, "
          f"epochs={hp['epochs']}, dropout={hp['dropout']}")


# ===============================
# HELPER FUNCTIONS
# ===============================

def remove_bangla_from_name(name):
    """Remove Bangla/Bengali characters from class names."""
    cleaned = re.sub(r'[\u0980-\u09FF]+', '', name)
    cleaned = re.sub(r'[^\x00-\x7F]+', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip(' _-')
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = cleaned.strip()
    return cleaned if cleaned else f"Species_{hash(name) % 1000}"


# ===============================
# DATASET
# ===============================

class FishDataset(Dataset):
    def __init__(self, root, transform=None, clean_names=True):
        self.root = Path(root)
        self.transform = transform
        
        classes = sorted([d.name for d in self.root.iterdir() if d.is_dir()])
        self.original_classes = classes.copy()
        
        if clean_names:
            self.cleaned_classes = [remove_bangla_from_name(c) for c in classes]
        else:
            self.cleaned_classes = classes.copy()
        
        self.class_to_idx = {c: i for i, c in enumerate(classes)}
        self.idx_to_class = {i: self.cleaned_classes[i] for i in range(len(classes))}
        self.idx_to_original_class = {i: classes[i] for i in range(len(classes))}
        
        self.samples = []
        self.class_counts = {}
        
        for c in classes:
            class_samples = []
            for img_path in (self.root / c).glob("*"):
                if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"]:
                    class_samples.append((str(img_path), self.class_to_idx[c]))
            self.samples.extend(class_samples)
            self.class_counts[self.class_to_idx[c]] = len(class_samples)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label, path


# ===============================
# TRANSFORMS
# ===============================

train_transform = transforms.Compose([
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(degrees=20),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
    transforms.ToTensor(),
    transforms.RandomApply([transforms.GaussianBlur(kernel_size=3)], p=0.2),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


# ===============================
# TRAINING FUNCTIONS
# ===============================

def train_model(model, train_loader, val_loader, hyperparams, device, verbose=False):
    """Train model and return validation accuracy"""
    
    optimizer = torch.optim.AdamW(
        model.parameters(), 
        lr=hyperparams['lr'], 
        weight_decay=hyperparams['weight_decay']
    )
    
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=hyperparams['epochs']
    )
    
    best_val_acc = 0
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    for epoch in range(hyperparams['epochs']):
        # Training
        model.train()
        train_loss = 0
        correct = 0
        total = 0
        
        for imgs, lbls, _ in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            
            outputs = model(imgs)
            loss = F.cross_entropy(outputs, lbls, label_smoothing=hyperparams['label_smoothing'])
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            total += lbls.size(0)
            correct += predicted.eq(lbls).sum().item()
        
        scheduler.step()
        train_acc = 100. * correct / total
        train_loss = train_loss / len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for imgs, lbls, _ in val_loader:
                imgs, lbls = imgs.to(device), lbls.to(device)
                outputs = model(imgs)
                loss = F.cross_entropy(outputs, lbls)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += lbls.size(0)
                val_correct += predicted.eq(lbls).sum().item()
        
        val_acc = 100. * val_correct / val_total
        val_loss = val_loss / len(val_loader)
        
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
        
        if verbose:
            print(f"    Epoch {epoch+1}/{hyperparams['epochs']} | "
                  f"Train: {train_acc:.2f}% | Val: {val_acc:.2f}%")
    
    return best_val_acc, history


def evaluate_model(model, test_loader, device):
    """Evaluate model and return metrics"""
    model.eval()
    
    all_preds = []
    all_trues = []
    all_probs = []
    
    with torch.no_grad():
        for imgs, lbls, _ in test_loader:
            imgs = imgs.to(device)
            outputs = model(imgs)
            probs = F.softmax(outputs, dim=1).cpu().numpy()
            preds = outputs.argmax(1).cpu().numpy()
            
            all_preds.extend(preds)
            all_trues.extend(lbls.numpy())
            all_probs.extend(probs)
    
    all_preds = np.array(all_preds)
    all_trues = np.array(all_trues)
    
    return {
        'accuracy': accuracy_score(all_trues, all_preds),
        'balanced_accuracy': balanced_accuracy_score(all_trues, all_preds),
        'macro_f1': f1_score(all_trues, all_preds, average='macro'),
        'weighted_f1': f1_score(all_trues, all_preds, average='weighted'),
        'macro_precision': precision_score(all_trues, all_preds, average='macro', zero_division=0),
        'macro_recall': recall_score(all_trues, all_preds, average='macro', zero_division=0),
        'predictions': all_preds,
        'true_labels': all_trues,
    }


# ===============================
# LOAD DATASET
# ===============================

print("\n" + "="*70)
print("LOADING DATASET")
print("="*70)

dataset_train = FishDataset(DATA_DIR, transform=train_transform, clean_names=True)
dataset_val = FishDataset(DATA_DIR, transform=val_transform, clean_names=True)

print(f"\nTotal images: {len(dataset_train)}")
print(f"Total classes: {len(dataset_train.idx_to_class)}")

print("\nClass Distribution:")
for idx in range(len(dataset_train.idx_to_class)):
    name = dataset_train.idx_to_class[idx]
    count = dataset_train.class_counts.get(idx, 0)
    print(f"  [{idx:2d}] {name:<45} n={count}")

y = np.array([lbl for _, lbl in dataset_train.samples])


# ===============================
# NESTED CROSS-VALIDATION
# ===============================

print("\n" + "="*70)
print("STARTING NESTED CROSS-VALIDATION")
print("="*70)

outer_cv = StratifiedKFold(n_splits=OUTER_FOLDS, shuffle=True, random_state=RANDOM_SEED)

outer_fold_results = []
all_outer_predictions = []
all_outer_true_labels = []
best_hyperparams_per_fold = []

start_time = time.time()

for outer_fold, (outer_train_idx, test_idx) in enumerate(outer_cv.split(np.zeros(len(y)), y)):
    
    print(f"\n{'='*70}")
    print(f"OUTER FOLD {outer_fold + 1}/{OUTER_FOLDS}")
    print(f"{'='*70}")
    print(f"Train: {len(outer_train_idx)}, Test: {len(test_idx)}")
    
    # Inner CV
    inner_cv = StratifiedKFold(n_splits=INNER_FOLDS, shuffle=True, random_state=RANDOM_SEED + outer_fold)
    hyperparam_scores = {hp['name']: [] for hp in HYPERPARAMETER_GRID}
    
    print(f"\n  --- Inner CV for Hyperparameter Selection ---")
    
    for inner_fold, (inner_train_idx, inner_val_idx) in enumerate(inner_cv.split(
        np.zeros(len(outer_train_idx)), y[outer_train_idx]
    )):
        print(f"\n  Inner Fold {inner_fold + 1}/{INNER_FOLDS}")
        
        actual_train_idx = outer_train_idx[inner_train_idx]
        actual_val_idx = outer_train_idx[inner_val_idx]
        
        train_subset = Subset(dataset_train, actual_train_idx)
        val_subset = Subset(dataset_val, actual_val_idx)
        
        # Class balancing
        train_labels = y[actual_train_idx]
        class_counts = np.bincount(train_labels, minlength=len(dataset_train.class_to_idx))
        weights = 1.0 / (class_counts + 1e-6)
        sample_weights = weights[train_labels]
        sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)
        
        train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
        val_loader = DataLoader(val_subset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
        
        for hp in HYPERPARAMETER_GRID:
            print(f"    Testing {hp['name']}...", end=" ", flush=True)
            
            model = MobileNetV3Classifier(
                num_classes=len(dataset_train.class_to_idx),
                dropout=hp['dropout'],
                pretrained=True
            ).to(device)
            
            val_acc, _ = train_model(model, train_loader, val_loader, hp, device, verbose=False)
            hyperparam_scores[hp['name']].append(val_acc)
            
            print(f"Val Acc: {val_acc:.2f}%")
            
            del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    # Select best hyperparameters
    mean_scores = {name: np.mean(scores) for name, scores in hyperparam_scores.items()}
    std_scores = {name: np.std(scores) for name, scores in hyperparam_scores.items()}
    
    best_hp_name = max(mean_scores, key=mean_scores.get)
    best_hp = next(hp for hp in HYPERPARAMETER_GRID if hp['name'] == best_hp_name)
    
    print(f"\n  --- Inner CV Results ---")
    for name in hyperparam_scores:
        print(f"    {name}: {mean_scores[name]:.2f}% ± {std_scores[name]:.2f}%")
    print(f"  ✓ Best: {best_hp_name}")
    
    best_hyperparams_per_fold.append({
        'outer_fold': outer_fold + 1,
        'best_config': best_hp_name,
        'mean_inner_score': mean_scores[best_hp_name],
        'std_inner_score': std_scores[best_hp_name],
        'all_scores': mean_scores
    })
    
    # Train final model
    print(f"\n  --- Training Final Model with {best_hp_name} ---")
    
    train_subset = Subset(dataset_train, outer_train_idx)
    test_subset = Subset(dataset_val, test_idx)
    
    train_labels = y[outer_train_idx]
    class_counts = np.bincount(train_labels, minlength=len(dataset_train.class_to_idx))
    weights = 1.0 / (class_counts + 1e-6)
    sample_weights = weights[train_labels]
    sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)
    
    train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    test_loader = DataLoader(test_subset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    final_model = MobileNetV3Classifier(
        num_classes=len(dataset_train.class_to_idx),
        dropout=best_hp['dropout'],
        pretrained=True
    ).to(device)
    
    val_acc, history = train_model(final_model, train_loader, test_loader, best_hp, device, verbose=True)
    
    # Evaluate
    print(f"\n  --- Test Results ---")
    test_metrics = evaluate_model(final_model, test_loader, device)
    
    print(f"  Accuracy:          {test_metrics['accuracy']:.4f}")
    print(f"  Balanced Accuracy: {test_metrics['balanced_accuracy']:.4f}")
    print(f"  Macro F1:          {test_metrics['macro_f1']:.4f}")
    print(f"  Weighted F1:       {test_metrics['weighted_f1']:.4f}")
    print(f"  Precision:         {test_metrics['macro_precision']:.4f}")
    print(f"  Recall:            {test_metrics['macro_recall']:.4f}")
    
    outer_fold_results.append({
        'outer_fold': outer_fold + 1,
        'best_hyperparams': best_hp_name,
        **{k: v for k, v in test_metrics.items() if k not in ['predictions', 'true_labels']},
        'history': history
    })
    
    all_outer_predictions.extend(test_metrics['predictions'])
    all_outer_true_labels.extend(test_metrics['true_labels'])
    
    del final_model

total_time = time.time() - start_time


# ===============================
# RESULTS SUMMARY
# ===============================

print("\n" + "="*70)
print("NESTED CROSS-VALIDATION RESULTS")
print("="*70)

metrics_names = ['accuracy', 'balanced_accuracy', 'macro_f1', 'weighted_f1', 
                 'macro_precision', 'macro_recall']

print(f"\nModel: MobileNetV3-Small (Pretrained)")
print(f"Parameters: {n_params:,}")
print(f"Total time: {timedelta(seconds=int(total_time))}")

print("\n" + "-"*70)
print("Per-Fold Results:")
print("-"*70)
print(f"{'Fold':<6} {'Config':<12} {'Accuracy':>10} {'Bal Acc':>10} {'Macro F1':>10} {'W-F1':>10}")
print("-"*70)

for result in outer_fold_results:
    print(f"{result['outer_fold']:<6} {result['best_hyperparams']:<12} "
          f"{result['accuracy']:>10.4f} {result['balanced_accuracy']:>10.4f} "
          f"{result['macro_f1']:>10.4f} {result['weighted_f1']:>10.4f}")

print("\n" + "-"*70)
print("Aggregated Results (Mean ± Std):")
print("-"*70)

aggregated_results = {}
for metric in metrics_names:
    values = [r[metric] for r in outer_fold_results]
    mean_val = np.mean(values)
    std_val = np.std(values)
    ci_95 = 1.96 * std_val / np.sqrt(len(values))
    aggregated_results[metric] = {'mean': mean_val, 'std': std_val, 'ci_95': ci_95, 'values': values}
    print(f"{metric:<20}: {mean_val:.4f} ± {std_val:.4f}  "
          f"(95% CI: [{mean_val-ci_95:.4f}, {mean_val+ci_95:.4f}])")

print("\n" + "-"*70)
print("Hyperparameter Selection:")
print("-"*70)
for fold_hp in best_hyperparams_per_fold:
    print(f"Fold {fold_hp['outer_fold']}: {fold_hp['best_config']} "
          f"(Inner CV: {fold_hp['mean_inner_score']:.2f}% ± {fold_hp['std_inner_score']:.2f}%)")


# ===============================
# GENERATE PLOTS
# ===============================

print("\n" + "="*70)
print("GENERATING PLOTS")
print("="*70)

plt.rcParams.update({
    'figure.dpi': 300, 
    'savefig.dpi': 300, 
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
})

class_names = [dataset_train.idx_to_class[i] for i in range(len(dataset_train.idx_to_class))]
all_preds = np.array(all_outer_predictions)
all_trues = np.array(all_outer_true_labels)

# 1. Confusion Matrix
print("  Generating confusion matrix...")
cm = confusion_matrix(all_trues, all_preds)
cm_normalized = cm.astype('float') / (cm.sum(axis=1)[:, np.newaxis] + 1e-10)

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

ax = axes[0]
im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
ax.set_title('(A) Confusion Matrix (Counts)', fontweight='bold')
plt.colorbar(im, ax=ax, shrink=0.8)
ax.set_xticks(range(len(class_names)))
ax.set_yticks(range(len(class_names)))
ax.set_xticklabels(class_names, rotation=45, ha='right', fontsize=6)
ax.set_yticklabels(class_names, fontsize=6)
ax.set_xlabel('Predicted Label', fontweight='bold')
ax.set_ylabel('True Label', fontweight='bold')

# Add text annotations for counts
thresh = cm.max() / 2
for i in range(len(class_names)):
    for j in range(len(class_names)):
        if cm[i, j] > 0:
            ax.text(j, i, str(cm[i, j]), ha='center', va='center',
                   color='white' if cm[i, j] > thresh else 'black', fontsize=5)

ax = axes[1]
im = ax.imshow(cm_normalized, interpolation='nearest', cmap='Blues', vmin=0, vmax=1)
ax.set_title('(B) Confusion Matrix (Normalized)', fontweight='bold')
plt.colorbar(im, ax=ax, shrink=0.8)
ax.set_xticks(range(len(class_names)))
ax.set_yticks(range(len(class_names)))
ax.set_xticklabels(class_names, rotation=45, ha='right', fontsize=6)
ax.set_yticklabels(class_names, fontsize=6)
ax.set_xlabel('Predicted Label', fontweight='bold')
ax.set_ylabel('True Label', fontweight='bold')

# Add text annotations for normalized values
for i in range(len(class_names)):
    for j in range(len(class_names)):
        if cm_normalized[i, j] > 0.01:
            ax.text(j, i, f'{cm_normalized[i, j]:.2f}', ha='center', va='center',
                   color='white' if cm_normalized[i, j] > 0.5 else 'black', fontsize=5)

plt.suptitle(f'MobileNetV3 - Nested CV Results ({OUTER_FOLDS} Outer × {INNER_FOLDS} Inner Folds)\n'
             f'Accuracy: {aggregated_results["accuracy"]["mean"]:.2%} ± {aggregated_results["accuracy"]["std"]:.2%}', 
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "plots", "confusion_matrix.png"), 
           dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

# 2. Performance Summary
print("  Generating performance summary...")
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Metrics across folds
ax = axes[0, 0]
folds = [r['outer_fold'] for r in outer_fold_results]
metrics_to_plot = ['accuracy', 'balanced_accuracy', 'macro_f1', 'weighted_f1']
colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6']
markers = ['o', 's', '^', 'd']

for metric, color, marker in zip(metrics_to_plot, colors, markers):
    values = [r[metric] for r in outer_fold_results]
    ax.plot(folds, values, f'-{marker}', color=color, label=metric.replace('_', ' ').title(), 
            markersize=8, linewidth=2)
    ax.axhline(y=np.mean(values), color=color, linestyle='--', alpha=0.5)

ax.set_xlabel('Outer Fold', fontweight='bold')
ax.set_ylabel('Score', fontweight='bold')
ax.set_title('(A) Performance Across Folds', fontweight='bold')
ax.legend(loc='lower right', fontsize=8)
ax.set_xticks(folds)
ax.grid(True, alpha=0.3)
# Adjust y-axis based on results
min_val = min([min([r[m] for r in outer_fold_results]) for m in metrics_to_plot])
ax.set_ylim([max(0, min_val - 0.05), 1.02])

# Box plots
ax = axes[0, 1]
data_for_box = [aggregated_results[m]['values'] for m in metrics_to_plot]
labels_box = [m.replace('_', '\n').title() for m in metrics_to_plot]

bp = ax.boxplot(data_for_box, labels=labels_box, patch_artist=True, widths=0.6)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

for i, data in enumerate(data_for_box):
    x = np.random.normal(i+1, 0.04, size=len(data))
    ax.scatter(x, data, c='black', alpha=0.6, s=30, zorder=3)

ax.set_ylabel('Score', fontweight='bold')
ax.set_title('(B) Score Distribution', fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Per-class F1
ax = axes[1, 0]
report = classification_report(all_trues, all_preds, output_dict=True, zero_division=0)
class_f1 = [report.get(str(i), {}).get('f1-score', 0) for i in range(len(class_names))]
class_colors = plt.cm.tab20(np.linspace(0, 1, len(class_names)))

bars = ax.barh(range(len(class_names)), class_f1, color=class_colors, edgecolor='black', linewidth=0.5)
ax.set_yticks(range(len(class_names)))
ax.set_yticklabels(class_names, fontsize=7)
ax.set_xlabel('F1-Score', fontweight='bold')
ax.set_title('(C) Per-Class F1-Score', fontweight='bold')
ax.axvline(x=np.mean(class_f1), color='red', linestyle='--', linewidth=2, 
          label=f'Mean: {np.mean(class_f1):.3f}')
ax.legend(loc='lower right')
ax.invert_yaxis()
ax.set_xlim([0, 1.05])

for i, f1 in enumerate(class_f1):
    ax.text(f1 + 0.01, i, f'{f1:.2f}', va='center', fontsize=6)

# Training curves
ax = axes[1, 1]
last_history = outer_fold_results[-1]['history']
epochs = range(1, len(last_history['train_acc']) + 1)

ax.plot(epochs, last_history['train_acc'], 'b-o', label='Train Acc', markersize=6, linewidth=2)
ax.plot(epochs, last_history['val_acc'], 'r-s', label='Val Acc', markersize=6, linewidth=2)
ax.set_xlabel('Epoch', fontweight='bold')
ax.set_ylabel('Accuracy (%)', fontweight='bold')
ax.set_title(f'(D) Training Curves (Fold {OUTER_FOLDS})', fontweight='bold')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)

plt.suptitle(f'MobileNetV3-Small Performance Analysis\n'
             f'Parameters: {n_params:,} | '
             f'Accuracy: {aggregated_results["accuracy"]["mean"]:.2%} ± {aggregated_results["accuracy"]["std"]:.2%}', 
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "plots", "performance_analysis.png"), 
           dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

# 3. Hyperparameter Analysis
print("  Generating hyperparameter analysis...")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

hp_names = [hp['name'] for hp in HYPERPARAMETER_GRID]
inner_scores_by_hp = {name: [] for name in hp_names}

for fold_result in best_hyperparams_per_fold:
    for hp_name, score in fold_result['all_scores'].items():
        inner_scores_by_hp[hp_name].append(score)

ax = axes[0]
positions = range(len(hp_names))
bp = ax.boxplot([inner_scores_by_hp[name] for name in hp_names], 
               positions=positions, patch_artist=True, widths=0.6)

box_colors = plt.cm.Set2(np.linspace(0, 1, len(hp_names)))
for patch, color in zip(bp['boxes'], box_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax.set_xticks(positions)
ax.set_xticklabels(hp_names, rotation=45, ha='right')
ax.set_ylabel('Inner CV Validation Accuracy (%)', fontweight='bold')
ax.set_title('(A) Hyperparameter Performance', fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

ax = axes[1]
hp_counts = {name: 0 for name in hp_names}
for fold_hp in best_hyperparams_per_fold:
    hp_counts[fold_hp['best_config']] += 1

bars = ax.bar(hp_names, [hp_counts[name] for name in hp_names], color=box_colors, edgecolor='black')
ax.set_ylabel('Times Selected', fontweight='bold')
ax.set_xlabel('Hyperparameter Configuration', fontweight='bold')
ax.set_title('(B) Selection Frequency', fontweight='bold')
ax.set_xticklabels(hp_names, rotation=45, ha='right')

for bar, count in zip(bars, [hp_counts[name] for name in hp_names]):
    if count > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
               str(count), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "plots", "hyperparameter_analysis.png"), 
           dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("  All plots saved!")


# ===============================
# SAVE DETAILED REPORT
# ===============================

print("\n" + "="*70)
print("SAVING REPORT")
print("="*70)

report_path = os.path.join(OUTPUT_DIR, "nested_cv_report.txt")
with open(report_path, 'w') as f:
    f.write("="*70 + "\n")
    f.write("NESTED CROSS-VALIDATION REPORT\n")
    f.write("Bangladesh Fish Dataset - Data in Brief Publication\n")
    f.write("="*70 + "\n\n")
    
    f.write("MODEL INFORMATION\n")
    f.write("-"*70 + "\n")
    f.write(f"Model: MobileNetV3-Small (Pretrained on ImageNet)\n")
    f.write(f"Parameters: {n_params:,}\n")
    f.write(f"Outer Folds: {OUTER_FOLDS}\n")
    f.write(f"Inner Folds: {INNER_FOLDS}\n")
    f.write(f"Total Training Time: {timedelta(seconds=int(total_time))}\n")
    f.write(f"Device: {device}\n\n")
    
    f.write("HYPERPARAMETER SEARCH SPACE\n")
    f.write("-"*70 + "\n")
    for hp in HYPERPARAMETER_GRID:
        f.write(f"  {hp['name']}: lr={hp['lr']}, wd={hp['weight_decay']}, "
                f"epochs={hp['epochs']}, dropout={hp['dropout']}, ls={hp['label_smoothing']}\n")
    f.write("\n")
    
    f.write("AGGREGATED RESULTS (Mean ± Std)\n")
    f.write("-"*70 + "\n")
    f.write(f"{'Metric':<25} {'Mean':>10} {'Std':>10} {'95% CI':>25}\n")
    f.write("-"*70 + "\n")
    for metric in metrics_names:
        r = aggregated_results[metric]
        f.write(f"{metric:<25} {r['mean']:>10.4f} {r['std']:>10.4f} "
                f"[{r['mean']-r['ci_95']:.4f}, {r['mean']+r['ci_95']:.4f}]\n")
    f.write("\n")
    
    f.write("PER-FOLD RESULTS\n")
    f.write("-"*70 + "\n")
    f.write(f"{'Fold':<6} {'Config':<12} {'Accuracy':>10} {'Bal Acc':>10} {'Macro F1':>10}\n")
    f.write("-"*70 + "\n")
    for result in outer_fold_results:
        f.write(f"{result['outer_fold']:<6} {result['best_hyperparams']:<12} "
                f"{result['accuracy']:>10.4f} {result['balanced_accuracy']:>10.4f} "
                f"{result['macro_f1']:>10.4f}\n")
    f.write("\n")
    
    f.write("HYPERPARAMETER SELECTION\n")
    f.write("-"*70 + "\n")
    for fold_hp in best_hyperparams_per_fold:
        f.write(f"Fold {fold_hp['outer_fold']}: {fold_hp['best_config']} "
                f"(Inner CV: {fold_hp['mean_inner_score']:.2f}% ± {fold_hp['std_inner_score']:.2f}%)\n")
    f.write("\n")
    
    f.write("CLASSIFICATION REPORT\n")
    f.write("-"*70 + "\n")
    f.write(classification_report(all_trues, all_preds, target_names=class_names, zero_division=0))
    f.write("\n")
    
    f.write("CLASS INFORMATION\n")
    f.write("-"*70 + "\n")
    for idx in range(len(dataset_train.idx_to_class)):
        cleaned = dataset_train.idx_to_class[idx]
        original = dataset_train.idx_to_original_class[idx]
        count = dataset_train.class_counts.get(idx, 0)
        f1 = class_f1[idx]
        f.write(f"[{idx:2d}] {cleaned:<40} n={count:4d}  F1={f1:.3f}\n")

print(f"Report saved: {report_path}")


# ===============================
# FINAL SUMMARY
# ===============================

print("\n" + "="*70)
print("NESTED CROSS-VALIDATION COMPLETED")
print("="*70)
print(f"\nOutput Directory: {OUTPUT_DIR}")
print(f"\nGenerated Files:")
print(f"  📊 {OUTPUT_DIR}/plots/confusion_matrix.png")
print(f"  📊 {OUTPUT_DIR}/plots/performance_analysis.png")
print(f"  📊 {OUTPUT_DIR}/plots/hyperparameter_analysis.png")
print(f"  📄 {OUTPUT_DIR}/nested_cv_report.txt")

print("\n" + "-"*70)
print("MODEL DETAILS:")
print("-"*70)
print(f"  Architecture: MobileNetV3-Small")
print(f"  Parameters: {n_params:,}")
print(f"  Pretrained: ImageNet")
print(f"  Training Time: {timedelta(seconds=int(total_time))}")

print("\n" + "-"*70)
print("FINAL RESULTS (Nested CV - Unbiased Estimate):")
print("-"*70)
print(f"  Accuracy:          {aggregated_results['accuracy']['mean']:.4f} ± {aggregated_results['accuracy']['std']:.4f}")
print(f"  Balanced Accuracy: {aggregated_results['balanced_accuracy']['mean']:.4f} ± {aggregated_results['balanced_accuracy']['std']:.4f}")
print(f"  Macro F1:          {aggregated_results['macro_f1']['mean']:.4f} ± {aggregated_results['macro_f1']['std']:.4f}")
print(f"  Weighted F1:       {aggregated_results['weighted_f1']['mean']:.4f} ± {aggregated_results['weighted_f1']['std']:.4f}")
print(f"  Precision:         {aggregated_results['macro_precision']['mean']:.4f} ± {aggregated_results['macro_precision']['std']:.4f}")
print(f"  Recall:            {aggregated_results['macro_recall']['mean']:.4f} ± {aggregated_results['macro_recall']['std']:.4f}")
print("="*70)

# Summary table for paper
print("\n" + "="*70)
print("TABLE FOR PAPER (Copy-Paste Ready):")
print("="*70)
print("""
| Metric            | Value           | 95% CI              |
|-------------------|-----------------|---------------------|""")
for metric in ['accuracy', 'balanced_accuracy', 'macro_f1', 'weighted_f1', 'macro_precision', 'macro_recall']:
    r = aggregated_results[metric]
    metric_name = metric.replace('_', ' ').title()
    print(f"| {metric_name:<17} | {r['mean']:.4f} ± {r['std']:.4f} | [{r['mean']-r['ci_95']:.4f}, {r['mean']+r['ci_95']:.4f}] |")
print("="*70)