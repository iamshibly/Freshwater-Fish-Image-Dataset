# A Multimodal Freshwater Fish Image Dataset with Nutritional Metadata for Computer Vision-Based Species Recognition in Bangladesh

## Dataset and Nutrition Metadata

**Dataset and nutrition metadata are available here:**

**Google Drive Link:** https://drive.google.com/file/d/1OhmyKxcqPe6FMafaNCIP1Pb4VP97VvIR/view?usp=drive_link

The Google Drive link provides access to the freshwater fish image dataset and the species-level nutritional metadata CSV file.

The dataset includes:

- Raw freshwater fish images
- Species-wise image folders
- Processed image files for validation and benchmarking
- Per-100 g nutritional metadata CSV file
- Supporting files required for dataset inspection and analysis

---

## Overview

This repository supports the paper titled:

**A Multimodal Freshwater Fish Image Dataset with Nutritional Metadata for Computer Vision-Based Species Recognition in Bangladesh**

The work introduces a multimodal freshwater fish dataset from Bangladesh by combining fish images with structured nutritional metadata. The dataset is designed to support both computer vision-based species recognition and nutrition-aware machine learning.

The dataset can support research and development in:

- Freshwater fish species recognition
- Image classification
- Transfer learning
- Food image recognition
- Multimodal image and tabular learning
- Nutrition-aware analysis
- Fisheries decision-support systems
- Biodiversity informatics
- Dataset benchmarking

---

## Repository Structure

```text
repository-root/
|
|-- Fish Images/
|   `-- Fish image dataset files and class-wise image folders
|
|-- Validation Code and Plots/
|   `-- Validation scripts, generated plots, and feature-space analysis outputs
|
`-- README.md
```

---

## Dataset Summary

| Component | Description |
|---|---:|
| Total fish categories | 23 |
| Raw images | 5,520 |
| Processed images | 19,868 |
| Total image pool | 25,388 |
| Metadata type | Species-level nutritional values |
| Nutrition unit | Per 100 g edible portion |
| Main data modalities | Image + tabular nutrition metadata |

The dataset is organized by species. Raw images are preserved without resizing or preprocessing so that users can apply their own preprocessing, classification, feature extraction, or benchmarking pipelines.

---

## Dataset Organization

Expected dataset layout:

```text
Fish Dataset/
|
|-- Fish Dataset Raw/
|   |-- Bacha/
|   |-- Baim/
|   |-- Bele/
|   |-- Chanda/
|   |-- Cheng/
|   |-- Dairka/
|   |-- Dhaira/
|   |-- Dhyala-pithali/
|   |-- Fasa/
|   |-- Goti/
|   |-- Guchi/
|   |-- Itha/
|   |-- Jiyol/
|   |-- Kakila/
|   |-- Khori/
|   |-- Koi/
|   |-- Mohola/
|   |-- Pabda/
|   |-- Paloa Tengra/
|   |-- Piyali/
|   |-- Puthi/
|   |-- Rewa/
|   `-- Veda/
|
|-- Fish Dataset Augmented/
|   |-- Bacha/
|   |-- Baim/
|   |-- Bele/
|   |-- Chanda/
|   |-- Cheng/
|   |-- Dairka/
|   |-- Dhaira/
|   |-- Dhyala-pithali/
|   |-- Fasa/
|   |-- Goti/
|   |-- Guchi/
|   |-- Itha/
|   |-- Jiyol/
|   |-- Kakila/
|   |-- Khori/
|   |-- Koi/
|   |-- Mohola/
|   |-- Pabda/
|   |-- Paloa Tengra/
|   |-- Piyali/
|   |-- Puthi/
|   |-- Rewa/
|   `-- Veda/
|
`-- nutrition_metadata_per_100g.csv
```

---

## Fish Species Included

| No. | Category | Folder Name |
|---:|---|---|
| 1 | Bacha | Bacha |
| 2 | Baim | Baim |
| 3 | Bele | Bele |
| 4 | Chanda | Chanda |
| 5 | Cheng | Cheng |
| 6 | Dairka | Dairka |
| 7 | Dhaira | Dhaira |
| 8 | Dhyala / Pithali | Dhyala-pithali |
| 9 | Fasa | Fasa |
| 10 | Goti | Goti |
| 11 | Guchi | Guchi |
| 12 | Itha | Itha |
| 13 | Jiyol | Jiyol |
| 14 | Kakila | Kakila |
| 15 | Khori | Khori |
| 16 | Koi | Koi |
| 17 | Mohola | Mohola |
| 18 | Pabda | Pabda |
| 19 | Paloa Tengra | Paloa Tengra |
| 20 | Piyali | Piyali |
| 21 | Puthi | Puthi |
| 22 | Rewa | Rewa |
| 23 | Veda | Veda |

---

## Class Distribution

| No. | Category | Raw Images | Processed Images |
|---:|---|---:|---:|
| 1 | Bacha | 763 | 1526 |
| 2 | Baim | 175 | 700 |
| 3 | Bele | 316 | 1264 |
| 4 | Chanda | 183 | 732 |
| 5 | Cheng | 683 | 2046 |
| 6 | Dairka | 187 | 748 |
| 7 | Dhaira | 220 | 880 |
| 8 | Dhyala / Pithali | 256 | 1024 |
| 9 | Fasa | 120 | 480 |
| 10 | Goti | 43 | 172 |
| 11 | Guchi | 59 | 236 |
| 12 | Itha | 58 | 232 |
| 13 | Jiyol | 317 | 1268 |
| 14 | Kakila | 154 | 616 |
| 15 | Khori | 234 | 936 |
| 16 | Koi | 211 | 844 |
| 17 | Mohola | 61 | 244 |
| 18 | Pabda | 299 | 1196 |
| 19 | Paloa Tengra | 237 | 948 |
| 20 | Piyali | 289 | 1156 |
| 21 | Puthi | 216 | 864 |
| 22 | Rewa | 171 | 684 |
| 23 | Veda | 268 | 1072 |
|  | **Total** | **5,520** | **19,868** |

---

## Nutritional Metadata

The dataset includes a CSV file with species-level nutritional values per 100 g edible portion. This metadata connects fish species recognition with nutrition-related information.

The nutrition CSV includes fields such as:

| Metadata Type | Example Fields |
|---|---|
| Species identity | Local name, scientific name |
| Energy | Energy value |
| Macronutrients | Protein, fat |
| Vitamins | Vitamin A, Vitamin B12 |
| Minerals | Calcium, phosphorus, potassium, sodium, iron |
| Fatty acids | Omega-3, Omega-6 |

The nutrition metadata can be used for:

- Nutrition-aware fish recognition
- Class-wise nutritional comparison
- Food recognition with nutritional lookup
- Dietary decision-support systems
- Multimodal image and tabular learning
- Fisheries and food analytics research

---

## Data Collection and Quality Control

Images were collected from local fish markets in Bangladesh under real-market conditions. The dataset therefore reflects practical imaging conditions rather than only controlled laboratory settings.

Key preparation steps include:

- Individual fish specimen photography
- Plain-background image capture
- Class-wise folder organization
- Removal of blurry images
- Removal of low-quality images
- Removal of duplicate images
- Preservation of raw images without resizing or preprocessing

The raw image resolution range is approximately 640 x 640 pixels to 4284 x 5712 pixels.

---

## Dataset Validation and Representation Analysis

The dataset was evaluated using a lightweight image classification baseline and feature-space visualization methods.

### Nested Cross-Validation

A MobileNetV3-Small classifier pretrained on ImageNet was used for nested cross-validation. The evaluation used 5 outer folds and 2 inner folds.

Reported validation results include:

| Metric | Result |
|---|---:|
| Accuracy | 98.22% +/- 1.06% |
| Balanced accuracy | 98.03% +/- 1.13% |
| Macro-F1 score | 97.48% +/- 1.22% |
| Weighted-F1 score | 98.23% +/- 1.06% |

The fold-wise results indicate that the dataset is visually learnable and that the labels are consistent across different train-test splits.

### Feature-Space and Clustering Analysis

Feature-space analysis was performed using image embeddings extracted from the CNN model.

The analysis includes:

- PCA projection
- t-SNE projection
- 2D UMAP projection
- 3D UMAP projection
- Hierarchical clustering
- Correlation heatmap
- FlowSOM-style clustering
- SOM-node visualization
- Cluster-composition analysis

These analyses support the conclusion that images from the same species form meaningful visual clusters and that the learned embedding space contains species-relevant structure.

---

## Recommended Environment

A standard Python-based image analysis environment is recommended.

```text
Python 3.8+
NumPy
Pandas
Scikit-learn
Matplotlib
Seaborn
OpenCV
Pillow
TensorFlow / Keras or PyTorch
UMAP-learn
```

Example installation:

```bash
pip install numpy pandas scikit-learn matplotlib seaborn opencv-python pillow umap-learn
```

If using TensorFlow:

```bash
pip install tensorflow
```

If using PyTorch:

```bash
pip install torch torchvision
```

---

## How to Use

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Download the Dataset

Download the dataset and nutrition metadata from the Google Drive link:

```text
https://drive.google.com/file/d/1OhmyKxcqPe6FMafaNCIP1Pb4VP97VvIR/view?usp=drive_link
```

Place the dataset folder in the project directory or update the dataset path in the validation scripts.

### 3. Run Validation Code

Open the validation folder:

```bash
cd "Validation Code and Plots"
```

Run the relevant validation or plotting script according to the file names provided in that folder.

Example:

```bash
python main.py
```

If the script name is different, replace `main.py` with the correct file name.

---

## Expected Outputs

Depending on the available scripts, the validation folder may generate:

- Fold-wise performance plots
- Metric distribution boxplots
- Per-class F1 score charts
- Training curves
- PCA plots
- t-SNE plots
- 2D UMAP plots
- 3D UMAP plots
- Class distribution plots
- Correlation heatmaps
- Hierarchical clustering plots
- FlowSOM-style clustering visualizations

---

## Possible Applications

This dataset and repository can support:

- Freshwater fish species recognition
- Bangladeshi fish image classification
- Food image recognition
- Multimodal image and nutrition learning
- Nutrition-aware recommendation systems
- Fisheries decision-support tools
- Biodiversity informatics
- Dataset benchmarking
- Transfer learning experiments
- Computer vision education and research

---

## Citation

If this dataset, validation materials, or repository is useful in research, please cite the related paper.

```text
A Multimodal Freshwater Fish Image Dataset with Nutritional Metadata for Computer Vision-Based Species Recognition in Bangladesh.
```

---

## License and Usage

This repository is intended for academic and research use.

Before using the dataset or validation materials for commercial purposes, check the license or permission statement associated with the dataset archive and repository.

---

## Contact

For questions, open an issue in this repository.
