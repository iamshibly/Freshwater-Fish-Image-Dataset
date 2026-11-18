// Single place to edit site-wide facts. Everything else reads from here.
export const site = {
  name: "NutriFish-BD",
  tagline: "A multimodal freshwater fish image dataset with nutritional metadata",
  title:
    "A Multimodal Freshwater Fish Image Dataset with Nutritional Metadata for Computer Vision-Based Species Recognition in Bangladesh",
  conference: "MIET 2026",
  conferenceFull: "3rd International Conference on Machine Intelligence and Emerging Technologies (MIET 2026)",
  venue: "Noakhali Science and Technology University, Noakhali, Bangladesh",
  dates: "October 8–9, 2026",
  authors: "Tanvir Ahmod, Md. Zubayer Ahmad Shibly, Md. Maruf Hassan, Touhid Bhuiyan and Tanjina Noushin",
  authorList: [
    { name: "Tanvir Ahmod", aff: 1 },
    { name: "Md. Zubayer Ahmad Shibly", aff: 1 },
    { name: "Md. Maruf Hassan", aff: 1, corresponding: true },
    { name: "Touhid Bhuiyan", aff: 2, orcid: "0000-0002-6747-0846" },
    { name: "Tanjina Noushin", aff: 3 },
  ],
  affiliations: [
    "Southeast University, Bangladesh",
    "School of Information Technology, Washington University of Science and Technology",
    "School of Business, Washington University of Science and Technology",
  ],
  year: "2026",
  links: {
    kaggle: "https://doi.org/10.34740/KAGGLE/DSV/16153864", // permanent DOI cited in the paper's Data Availability section
    doi: "10.34740/KAGGLE/DSV/16153864",
    drive: "https://drive.google.com/file/d/1OhmyKxcqPe6FMafaNCIP1Pb4VP97VvIR/view?usp=drive_link", // mirror
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
  { id: "paper", label: "Paper" },
  { id: "code", label: "Code" },
  { id: "get", label: "Get the data" },
];
