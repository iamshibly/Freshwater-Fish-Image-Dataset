# ===============================
# NESTED CROSS-VALIDATION PIPELINE
# 5 OUTER FOLDS × 2 INNER FOLDS
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
from torchvision.models import resnet50, ResNet50_Weights, efficientnet_b0, EfficientNet_B0_Weights

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix, 
                            classification_report, precision_score, recall_score,
                            roc_auc_score, balanced_accuracy_score)
from sklearn.preprocessing import StandardScaler
import itertools

# ===============================
# SETTINGS
# ===============================

DATA_DIR = "/path/to/Fish Dataset Raw"
OUTPUT_DIR = "./fish_outputs_nested_cv"
OUTER_FOLDS = 5
INNER_FOLDS = 2
RANDOM_SEED = 42
IMG_SIZE = 224
BATCH_SIZE = 24

# Set random seeds
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "plots"), exist_ok=True)

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

print("="*70)
print("NESTED CROSS-VALIDATION PIPELINE")
print("Bangladesh Fish Dataset - Data in Brief Publication")
print("="*70)
print(f"Device: {device}")
print(f"Outer Folds: {OUTER_FOLDS}")
print(f"Inner Folds: {INNER_FOLDS}")
print(f"Total model trainings: {OUTER_FOLDS * INNER_FOLDS * N_HYPERPARAMS} (per hyperparameter set)")
print("="*70)

# ===============================
# HYPERPARAMETER SEARCH SPACE
# ===============================

HYPERPARAMETER_GRID = [
    {
        'name': 'Config_1',
        'lr': 1e-4,
        'weight_decay': 1e-4,
        'epochs': 5,
        'dropout': 0.2,
        'label_smoothing': 0.1,
        'optimizer': 'adamw'
    },
    {
        'name': 'Config_2',
        'lr': 3e-4,
        'weight_decay': 1e-5,
        'epochs': 5,
        'dropout': 0.3,
        'label_smoothing': 0.05,
        'optimizer': 'adamw'
    },
    {
        'name': 'Config_3',
        'lr': 1e-3,
        'weight_decay': 1e-3,
        'epochs': 5,
        'dropout': 0.4,
        'label_smoothing': 0.15,
        'optimizer': 'sgd'
    },
    {
        'name': 'Config_4',
        'lr': 5e-4,
        'weight_decay': 5e-5,
        'epochs': 6,
        'dropout': 0.25,
        'label_smoothing': 0.1,
        'optimizer': 'adamw'
    },
]

N_HYPERPARAMS = len(HYPERPARAMETER_GRID)
print(f"Hyperparameter configurations: {N_HYPERPARAMS}")
for i, hp in enumerate(HYPERPARAMETER_GRID):
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
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = re.sub(r'-+', '-', cleaned)
    cleaned = cleaned.strip(' _-')
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = re.sub(r'\[\s*\]', '', cleaned)
    cleaned = re.sub(r'\([^a-zA-Z0-9]*\)', '', cleaned)
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

def get_train_transform(augment_strength='medium'):
    """Get training transforms with different augmentation strengths"""
    if augment_strength == 'light':
        return transforms.Compose([
            transforms.RandomResizedCrop(IMG_SIZE, scale=(0.9, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=15),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    elif augment_strength == 'medium':
        return transforms.Compose([
            transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.2),
            transforms.RandomRotation(degrees=25),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
            transforms.ToTensor(),
            transforms.RandomApply([transforms.GaussianBlur(kernel_size=3)], p=0.2),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    else:  # strong
        return transforms.Compose([
            transforms.RandomResizedCrop(IMG_SIZE, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.3),
            transforms.RandomRotation(degrees=45),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
            transforms.ToTensor(),
            transforms.RandomApply([transforms.GaussianBlur(kernel_size=5)], p=0.3),
            transforms.RandomErasing(p=0.2, scale=(0.02, 0.2)),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

val_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


# ===============================
# MODEL WITH CONFIGURABLE DROPOUT
# ===============================

class FishClassifier(nn.Module):
    """ResNet50 with configurable dropout"""
    def __init__(self, num_classes, dropout=0.2, pretrained=True):
        super().__init__()
        if pretrained:
            self.backbone = resnet50(weights=ResNet50_Weights.DEFAULT)
        else:
            self.backbone = resnet50(weights=None)
        
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        
        self.classifier = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(p=dropout),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        return self.classifier(features)
    
    def get_features(self, x):
        return self.backbone(x)


# ===============================
# TRAINING FUNCTION
# ===============================

def train_model(model, train_loader, val_loader, hyperparams, device, verbose=False):
    """Train model with given hyperparameters and return validation metrics"""
    
    if hyperparams['optimizer'] == 'adamw':
        optimizer = torch.optim.AdamW(
            model.parameters(), 
            lr=hyperparams['lr'], 
            weight_decay=hyperparams['weight_decay']
        )
    else:  # sgd
        optimizer = torch.optim.SGD(
            model.parameters(), 
            lr=hyperparams['lr'], 
            momentum=0.9,
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
            loss = F.cross_entropy(
                outputs, lbls, 
                label_smoothing=hyperparams['label_smoothing']
            )
            
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
    """Evaluate model and return detailed metrics"""
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
    all_probs = np.array(all_probs)
    
    metrics = {
        'accuracy': accuracy_score(all_trues, all_preds),
        'balanced_accuracy': balanced_accuracy_score(all_trues, all_preds),
        'macro_f1': f1_score(all_trues, all_preds, average='macro'),
        'weighted_f1': f1_score(all_trues, all_preds, average='weighted'),
        'macro_precision': precision_score(all_trues, all_preds, average='macro', zero_division=0),
        'macro_recall': recall_score(all_trues, all_preds, average='macro', zero_division=0),
        'predictions': all_preds,
        'true_labels': all_trues,
        'probabilities': all_probs
    }
    
    return metrics


# ===============================
# NESTED CROSS-VALIDATION
# ===============================

print("\n" + "="*70)
print("STARTING NESTED CROSS-VALIDATION")
print("="*70)

# Load dataset
dataset_train = FishDataset(DATA_DIR, transform=get_train_transform('medium'), clean_names=True)
dataset_val = FishDataset(DATA_DIR, transform=val_transform, clean_names=True)

print(f"\nDataset: {len(dataset_train)} images, {len(dataset_train.idx_to_class)} classes")

# Print class distribution
print("\nClass Distribution:")
for idx in range(len(dataset_train.idx_to_class)):
    name = dataset_train.idx_to_class[idx]
    count = dataset_train.class_counts.get(idx, 0)
    print(f"  [{idx:2d}] {name:<45} n={count}")

y = np.array([lbl for _, lbl in dataset_train.samples])

# Outer CV
outer_cv = StratifiedKFold(n_splits=OUTER_FOLDS, shuffle=True, random_state=RANDOM_SEED)

# Store results
outer_fold_results = []
all_outer_predictions = []
all_outer_true_labels = []
best_hyperparams_per_fold = []

start_time = time.time()

for outer_fold, (outer_train_idx, test_idx) in enumerate(outer_cv.split(np.zeros(len(y)), y)):
    
    print(f"\n{'='*70}")
    print(f"OUTER FOLD {outer_fold + 1}/{OUTER_FOLDS}")
    print(f"{'='*70}")
    print(f"Outer train size: {len(outer_train_idx)}, Test size: {len(test_idx)}")
    
    # Inner CV for hyperparameter selection
    inner_cv = StratifiedKFold(n_splits=INNER_FOLDS, shuffle=True, random_state=RANDOM_SEED + outer_fold)
    
    # Track best hyperparameters
    hyperparam_scores = {hp['name']: [] for hp in HYPERPARAMETER_GRID}
    
    print(f"\n  --- Inner CV for Hyperparameter Selection ---")
    
    for inner_fold, (inner_train_idx, inner_val_idx) in enumerate(inner_cv.split(
        np.zeros(len(outer_train_idx)), y[outer_train_idx]
    )):
        print(f"\n  Inner Fold {inner_fold + 1}/{INNER_FOLDS}")
        
        # Map inner indices to original indices
        actual_train_idx = outer_train_idx[inner_train_idx]
        actual_val_idx = outer_train_idx[inner_val_idx]
        
        print(f"    Train: {len(actual_train_idx)}, Val: {len(actual_val_idx)}")
        
        # Create data subsets
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
        
        # Test each hyperparameter configuration
        for hp in HYPERPARAMETER_GRID:
            print(f"    Testing {hp['name']}...", end=" ")
            
            model = FishClassifier(
                num_classes=len(dataset_train.class_to_idx),
                dropout=hp['dropout']
            ).to(device)
            
            val_acc, _ = train_model(model, train_loader, val_loader, hp, device, verbose=False)
            hyperparam_scores[hp['name']].append(val_acc)
            
            print(f"Val Acc: {val_acc:.2f}%")
            
            del model
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    # Select best hyperparameters based on mean inner CV score
    mean_scores = {name: np.mean(scores) for name, scores in hyperparam_scores.items()}
    std_scores = {name: np.std(scores) for name, scores in hyperparam_scores.items()}
    
    best_hp_name = max(mean_scores, key=mean_scores.get)
    best_hp = next(hp for hp in HYPERPARAMETER_GRID if hp['name'] == best_hp_name)
    
    print(f"\n  --- Inner CV Results ---")
    for name in hyperparam_scores:
        print(f"    {name}: {mean_scores[name]:.2f}% ± {std_scores[name]:.2f}%")
    print(f"  Best Hyperparameters: {best_hp_name}")
    
    best_hyperparams_per_fold.append({
        'outer_fold': outer_fold + 1,
        'best_config': best_hp_name,
        'mean_inner_score': mean_scores[best_hp_name],
        'std_inner_score': std_scores[best_hp_name],
        'all_scores': mean_scores
    })
    
    # Train final model on full outer training set with best hyperparameters
    print(f"\n  --- Training Final Model for Outer Fold {outer_fold + 1} ---")
    
    train_subset = Subset(dataset_train, outer_train_idx)
    test_subset = Subset(dataset_val, test_idx)
    
    # Class balancing
    train_labels = y[outer_train_idx]
    class_counts = np.bincount(train_labels, minlength=len(dataset_train.class_to_idx))
    weights = 1.0 / (class_counts + 1e-6)
    sample_weights = weights[train_labels]
    sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)
    
    train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    test_loader = DataLoader(test_subset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    # Train with best hyperparameters
    final_model = FishClassifier(
        num_classes=len(dataset_train.class_to_idx),
        dropout=best_hp['dropout']
    ).to(device)
    
    val_acc, history = train_model(
        final_model, train_loader, test_loader, 
        best_hp, device, verbose=True
    )
    
    # Evaluate on test set
    print(f"\n  --- Evaluating on Test Set ---")
    test_metrics = evaluate_model(final_model, test_loader, device)
    
    print(f"  Test Results:")
    print(f"    Accuracy:          {test_metrics['accuracy']:.4f}")
    print(f"    Balanced Accuracy: {test_metrics['balanced_accuracy']:.4f}")
    print(f"    Macro F1:          {test_metrics['macro_f1']:.4f}")
    print(f"    Weighted F1:       {test_metrics['weighted_f1']:.4f}")
    print(f"    Precision:         {test_metrics['macro_precision']:.4f}")
    print(f"    Recall:            {test_metrics['macro_recall']:.4f}")
    
    # Store results
    outer_fold_results.append({
        'outer_fold': outer_fold + 1,
        'best_hyperparams': best_hp_name,
        **{k: v for k, v in test_metrics.items() if k not in ['predictions', 'true_labels', 'probabilities']},
        'history': history
    })
    
    all_outer_predictions.extend(test_metrics['predictions'])
    all_outer_true_labels.extend(test_metrics['true_labels'])
    
    del final_model
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

total_time = time.time() - start_time

# ===============================
# RESULTS SUMMARY
# ===============================

print("\n" + "="*70)
print("NESTED CROSS-VALIDATION RESULTS SUMMARY")
print("="*70)

# Extract metrics
metrics_names = ['accuracy', 'balanced_accuracy', 'macro_f1', 'weighted_f1', 
                 'macro_precision', 'macro_recall']

print(f"\nTotal time: {timedelta(seconds=int(total_time))}")
print(f"\nOuter Folds: {OUTER_FOLDS}, Inner Folds: {INNER_FOLDS}")

print("\n" + "-"*70)
print("Per-Fold Results:")
print("-"*70)
print(f"{'Fold':<6} {'Best Config':<12} {'Accuracy':>10} {'Bal Acc':>10} {'Macro F1':>10} {'Weighted F1':>12}")
print("-"*70)

for result in outer_fold_results:
    print(f"{result['outer_fold']:<6} {result['best_hyperparams']:<12} "
          f"{result['accuracy']:>10.4f} {result['balanced_accuracy']:>10.4f} "
          f"{result['macro_f1']:>10.4f} {result['weighted_f1']:>12.4f}")

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
    print(f"{metric:<20}: {mean_val:.4f} ± {std_val:.4f}  (95% CI: [{mean_val-ci_95:.4f}, {mean_val+ci_95:.4f}])")

print("\n" + "-"*70)
print("Hyperparameter Selection Summary:")
print("-"*70)

hp_selection_counts = {}
for fold_hp in best_hyperparams_per_fold:
    config = fold_hp['best_config']
    hp_selection_counts[config] = hp_selection_counts.get(config, 0) + 1
    print(f"Fold {fold_hp['outer_fold']}: {config} "
          f"(Inner CV: {fold_hp['mean_inner_score']:.2f}% ± {fold_hp['std_inner_score']:.2f}%)")

print(f"\nHyperparameter selection frequency:")
for config, count in sorted(hp_selection_counts.items(), key=lambda x: -x[1]):
    print(f"  {config}: {count}/{OUTER_FOLDS} folds")


# ===============================
# GENERATE PLOTS
# ===============================

print("\n" + "="*70)
print("GENERATING PLOTS")
print("="*70)

# Set plot style
plt.rcParams.update({
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
})

# 1. Confusion Matrix
print("Generating confusion matrix...")
all_preds = np.array(all_outer_predictions)
all_trues = np.array(all_outer_true_labels)
class_names = [dataset_train.idx_to_class[i] for i in range(len(dataset_train.idx_to_class))]

cm = confusion_matrix(all_trues, all_preds)
cm_normalized = cm.astype('float') / (cm.sum(axis=1)[:, np.newaxis] + 1e-10)

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# Raw counts
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

# Normalized
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

plt.suptitle(f'Nested CV Results ({OUTER_FOLDS} Outer × {INNER_FOLDS} Inner Folds)', 
            fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "plots", "confusion_matrix.png"), 
           dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

# 2. Performance Summary Plot
print("Generating performance summary...")
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Plot 1: Metrics across folds
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
ax.set_title('(A) Performance Across Outer Folds', fontweight='bold')
ax.legend(loc='lower right')
ax.set_xticks(folds)
ax.set_ylim([0.8, 1.02])
ax.grid(True, alpha=0.3)

# Plot 2: Box plots
ax = axes[0, 1]
data_for_box = [aggregated_results[m]['values'] for m in metrics_to_plot]
labels_box = [m.replace('_', '\n').title() for m in metrics_to_plot]

bp = ax.boxplot(data_for_box, labels=labels_box, patch_artist=True, widths=0.6)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Add individual points
for i, data in enumerate(data_for_box):
    x = np.random.normal(i+1, 0.04, size=len(data))
    ax.scatter(x, data, c='black', alpha=0.6, s=30, zorder=3)

ax.set_ylabel('Score', fontweight='bold')
ax.set_title('(B) Score Distribution (Outer Folds)', fontweight='bold')
ax.set_ylim([0.8, 1.02])
ax.grid(True, alpha=0.3, axis='y')

# Plot 3: Per-class F1 scores
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

# Add value labels
for i, f1 in enumerate(class_f1):
    ax.text(f1 + 0.01, i, f'{f1:.2f}', va='center', fontsize=6)

# Plot 4: Training curves (last fold)
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

plt.suptitle(f'Nested Cross-Validation Performance Analysis\n'
             f'Accuracy: {aggregated_results["accuracy"]["mean"]:.4f} ± {aggregated_results["accuracy"]["std"]:.4f}', 
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "plots", "performance_analysis.png"), 
           dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

# 3. Hyperparameter Analysis
print("Generating hyperparameter analysis...")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Inner CV scores for each hyperparameter
ax = axes[0]
hp_names = [hp['name'] for hp in HYPERPARAMETER_GRID]
inner_scores_by_hp = {name: [] for name in hp_names}

for fold_result in best_hyperparams_per_fold:
    for hp_name, score in fold_result['all_scores'].items():
        inner_scores_by_hp[hp_name].append(score)

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
ax.set_title('(A) Hyperparameter Performance in Inner CV', fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Selection frequency
ax = axes[1]
hp_counts = {name: 0 for name in hp_names}
for fold_hp in best_hyperparams_per_fold:
    hp_counts[fold_hp['best_config']] += 1

bars = ax.bar(hp_names, [hp_counts[name] for name in hp_names], color=box_colors, edgecolor='black')
ax.set_ylabel('Times Selected', fontweight='bold')
ax.set_xlabel('Hyperparameter Configuration', fontweight='bold')
ax.set_title('(B) Hyperparameter Selection Frequency', fontweight='bold')
ax.set_xticklabels(hp_names, rotation=45, ha='right')

# Add count labels
for bar, count in zip(bars, [hp_counts[name] for name in hp_names]):
    if count > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
               str(count), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "plots", "hyperparameter_analysis.png"), 
           dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("All plots saved!")


# ===============================
# SAVE DETAILED REPORT
# ===============================

print("\n" + "="*70)
print("SAVING DETAILED REPORT")
print("="*70)

report_path = os.path.join(OUTPUT_DIR, "nested_cv_report.txt")
with open(report_path, 'w') as f:
    f.write("="*70 + "\n")
    f.write("NESTED CROSS-VALIDATION REPORT\n")
    f.write("Bangladesh Fish Dataset - Data in Brief Publication\n")
    f.write("="*70 + "\n\n")
    
    f.write("EXPERIMENTAL SETUP\n")
    f.write("-"*70 + "\n")
    f.write(f"Outer Folds: {OUTER_FOLDS}\n")
    f.write(f"Inner Folds: {INNER_FOLDS}\n")
    f.write(f"Total Samples: {len(dataset_train)}\n")
    f.write(f"Total Classes: {len(dataset_train.idx_to_class)}\n")
    f.write(f"Total Training Time: {timedelta(seconds=int(total_time))}\n")
    f.write(f"Device: {device}\n\n")
    
    f.write("HYPERPARAMETER SEARCH SPACE\n")
    f.write("-"*70 + "\n")
    for hp in HYPERPARAMETER_GRID:
        f.write(f"  {hp['name']}:\n")
        for k, v in hp.items():
            if k != 'name':
                f.write(f"    {k}: {v}\n")
    f.write("\n")
    
    f.write("AGGREGATED RESULTS\n")
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
    for result in outer_fold_results:
        f.write(f"Fold {result['outer_fold']}:\n")
        f.write(f"  Best Hyperparameters: {result['best_hyperparams']}\n")
        f.write(f"  Accuracy: {result['accuracy']:.4f}\n")
        f.write(f"  Balanced Accuracy: {result['balanced_accuracy']:.4f}\n")
        f.write(f"  Macro F1: {result['macro_f1']:.4f}\n")
        f.write(f"  Weighted F1: {result['weighted_f1']:.4f}\n\n")
    
    f.write("HYPERPARAMETER SELECTION SUMMARY\n")
    f.write("-"*70 + "\n")
    for config, count in sorted(hp_selection_counts.items(), key=lambda x: -x[1]):
        f.write(f"  {config}: Selected in {count}/{OUTER_FOLDS} folds\n")
    f.write("\n")
    
    f.write("CLASSIFICATION REPORT\n")
    f.write("-"*70 + "\n")
    f.write(classification_report(all_trues, all_preds, target_names=class_names, zero_division=0))
    f.write("\n")
    
    f.write("CLASS NAMES\n")
    f.write("-"*70 + "\n")
    for idx in range(len(dataset_train.idx_to_class)):
        cleaned = dataset_train.idx_to_class[idx]
        original = dataset_train.idx_to_original_class[idx]
        count = dataset_train.class_counts.get(idx, 0)
        f.write(f"[{idx:2d}] {cleaned:<45} (n={count:4d})\n")

print(f"Report saved to: {report_path}")


# ===============================
# FINAL SUMMARY
# ===============================

print("\n" + "="*70)
print("NESTED CROSS-VALIDATION COMPLETED")
print("="*70)
print(f"\nOutput Directory: {OUTPUT_DIR}")
print("\nGenerated Files:")
print(f"  📊 {OUTPUT_DIR}/plots/confusion_matrix.png")
print(f"  📊 {OUTPUT_DIR}/plots/performance_analysis.png")
print(f"  📊 {OUTPUT_DIR}/plots/hyperparameter_analysis.png")
print(f"  📄 {OUTPUT_DIR}/nested_cv_report.txt")

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

# Note about high accuracy
print("\n" + "="*70)
print("NOTE ON HIGH ACCURACY")
print("="*70)
print("""
If accuracy remains very high even with Nested CV, this suggests:

1. DISTINCT VISUAL FEATURES: Fish species have clearly distinguishable 
   visual characteristics (colors, patterns, body shapes).

2. GOOD DATA QUALITY: Images are well-captured with consistent conditions.

3. APPROPRIATE MODEL: ResNet50 is well-suited for this classification task.

This is VALID for a Data in Brief paper! High accuracy on a well-constructed
dataset with proper validation methodology (Nested CV) is publishable.

Consider adding to your paper:
- Discussion of inter-class visual differences
- Sample images showing distinguishing features
- Comparison with other fish datasets
- Analysis of misclassified samples (if any)
""")
print("="*70)