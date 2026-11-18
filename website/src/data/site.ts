// Single place to edit site-wide facts. Everything else reads from here.
export const site = {
  name: "NutriFish-BD",
  tagline: "A multimodal freshwater fish image dataset with nutritional metadata",
  title:
    "A Multimodal Freshwater Fish Image Dataset with Nutritional Metadata for Computer Vision-Based Species Recognition in Bangladesh",
  conference: "MIET", // TODO: replace with the full conference name if desired
  authors: "Anonymous Author(s)", // TODO: replace once the camera-ready author list is public
  year: "2026",
  links: {
    drive: "https://drive.google.com/file/d/1OhmyKxcqPe6FMafaNCIP1Pb4VP97VvIR/view?usp=drive_link",
    github: "https://github.com/iamshibly/Freshwater-Fish-Image-Dataset",
    githubCode:
      "https://github.com/iamshibly/Freshwater-Fish-Image-Dataset/tree/main/Validation%20Code%20and%20Plots",
    notebook: "/downloads/data-in-brief-data-validation.ipynb",
    csv: "/downloads/nutrition_metadata_per_100g_from_paper.csv",
    paper: "", // TODO: add the paper / DOI URL when available; the button hides while empty
  },
  stats: { species: 23, raw: 5520, augmented: 19868, total: 25388 },
} as const;

export const nav = [
  { id: "why", label: "Why it matters" },
  { id: "dataset", label: "Dataset" },
  { id: "species", label: "Species" },
  { id: "nutrition", label: "Nutrition" },
  { id: "validation", label: "Validation" },
  { id: "code", label: "Code" },
  { id: "get", label: "Get the data" },
];
