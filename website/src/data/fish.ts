import raw from "./fish.json";
import sizes from "./image-sizes.json";

export type NutrientKey =
  | "energy" | "protein" | "fat" | "vitA" | "vitB12" | "calcium"
  | "phosphorus" | "potassium" | "sodium" | "iron" | "omega3" | "omega6";

export interface Fish {
  id: number; slug: string; name: string; sci: string;
  raw: number; aug: number; f1: number;
  nut: Record<NutrientKey, number | null>;
  flags: Partial<Record<NutrientKey, string>>;
}

export const fish = raw as Fish[];

export const nutrients: { key: NutrientKey; label: string; unit: string }[] = [
  { key: "energy", label: "Energy", unit: "kJ" },
  { key: "protein", label: "Protein", unit: "g" },
  { key: "fat", label: "Fat", unit: "g" },
  { key: "vitA", label: "Vitamin A", unit: "µg" },
  { key: "vitB12", label: "Vitamin B12", unit: "µg" },
  { key: "calcium", label: "Calcium", unit: "mg" },
  { key: "phosphorus", label: "Phosphorus", unit: "mg" },
  { key: "potassium", label: "Potassium", unit: "mg" },
  { key: "sodium", label: "Sodium", unit: "mg" },
  { key: "iron", label: "Iron", unit: "mg" },
  { key: "omega3", label: "Omega-3", unit: "g" },
  { key: "omega6", label: "Omega-6", unit: "g" },
];

export const imgSize = (k: string) => {
  const s = (sizes as Record<string, number[]>)[k];
  return { w: s[0], h: s[1] };
};

// Results reported in the paper (nested CV, MobileNetV3-Small, 5 outer x 2 inner folds)
export const cv = {
  folds: [
    { acc: 0.9918, bal: 0.9925, f1: 0.9845 },
    { acc: 0.9946, bal: 0.9906, f1: 0.9884 },
    { acc: 0.9674, bal: 0.9656, f1: 0.956 },
    { acc: 0.9846, bal: 0.9847, f1: 0.9797 },
    { acc: 0.9728, bal: 0.9682, f1: 0.9654 },
  ],
  summary: [
    { label: "Accuracy", mean: 98.22, std: 1.06, ci: "97.30–99.15" },
    { label: "Balanced accuracy", mean: 98.03, std: 1.13, ci: "97.04–99.02" },
    { label: "Macro-F1", mean: 97.48, std: 1.22, ci: "96.41–98.55" },
    { label: "Weighted-F1", mean: 98.23, std: 1.06, ci: "97.30–99.16" },
  ],
  params: "1,359,671",
};
