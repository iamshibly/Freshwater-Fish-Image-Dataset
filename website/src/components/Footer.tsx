import { site } from "@/data/site";

export function Footer() {
  return (
    <footer className="border-t border-line bg-deep/60">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-5 py-10 text-sm text-mist md:flex-row md:items-start md:justify-between">
        <div className="max-w-md">
          <div className="font-display text-lg text-foam">{site.name}</div>
          <p className="mt-1">
            {site.tagline}. For academic and research use — check the licence/permission statement in the dataset archive before commercial use.
          </p>

          <div className="mt-6 inline-flex flex-col rounded-xl border border-teal/20 bg-teal/5 px-4 py-3">
            <span className="text-xs font-semibold uppercase tracking-widest text-teal">
              Website developed by
            </span>
            <a
              href="https://github.com/iamshibly"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 text-base font-semibold text-foam transition-colors hover:text-teal"
            >
              Md. Zubayer Ahmad Shibly
            </a>
            <span className="mt-0.5 text-sm text-mist">Southeast University Graduate</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-x-6 gap-y-2 md:pt-2">
          <a className="hover:text-white" href={site.links.kaggle} target="_blank" rel="noopener noreferrer">Dataset (Kaggle DOI)</a>
          <a className="hover:text-white" href={site.links.github} target="_blank" rel="noopener noreferrer">GitHub</a>
          <a className="hover:text-white" href={`${site.links.github}/issues`} target="_blank" rel="noopener noreferrer">Questions / issues</a>
        </div>
      </div>

      <div className="border-t border-line px-5 py-6">
        <div className="mx-auto max-w-5xl text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-teal">Acknowledgement</p>
          <p className="mt-3 text-sm leading-7 text-mist">
            The authors thank{" "}
            <strong className="rounded-md bg-teal/10 px-1.5 py-0.5 font-semibold text-teal">
              Umme Salma Hasan
            </strong>
            , M.Sc. in Food and Nutrition (Inspiron Fitness &amp; Diet Consultancy Center),
            who compiled and reviewed the species-level nutritional metadata.
          </p>
          <p className="mt-3 text-xs leading-6 text-mist/75">
            {site.conferenceFull}, {site.venue}, {site.dates}.
          </p>
        </div>
      </div>
    </footer>
  );
}
