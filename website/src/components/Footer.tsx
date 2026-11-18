import { site } from "@/data/site";
export function Footer() {
  return (
    <footer className="border-t border-line bg-deep/60">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-10 text-sm text-mist md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-display text-lg text-foam">{site.name}</div>
          <p className="mt-1 max-w-md">{site.tagline}. For academic and research use — check the licence/permission statement in the dataset archive before commercial use.</p>
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <a className="hover:text-white" href={site.links.drive} target="_blank" rel="noopener noreferrer">Dataset</a>
          <a className="hover:text-white" href={site.links.github} target="_blank" rel="noopener noreferrer">GitHub</a>
          <a className="hover:text-white" href={`${site.links.github}/issues`} target="_blank" rel="noopener noreferrer">Questions / issues</a>
        </div>
      </div>
      <p className="border-t border-line px-5 py-4 text-center text-xs text-mist/70">
        Species nutritional values were reviewed by an independent nutrition professional. © {site.year} {site.name} authors.
      </p>
    </footer>
  );
}
