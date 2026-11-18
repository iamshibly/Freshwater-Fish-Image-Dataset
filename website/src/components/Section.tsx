import { Reveal } from "./ui";

export function Section({
  id, eyebrow, title, intro, children, className = "",
}: { id: string; eyebrow: string; title: React.ReactNode; intro?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section id={id} className={`relative mx-auto max-w-6xl px-5 py-20 md:py-28 ${className}`}>
      <Reveal>
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="font-display mt-3 max-w-3xl text-3xl font-semibold leading-tight md:text-5xl">{title}</h2>
        {intro && <p className="mt-5 max-w-2xl text-base leading-relaxed text-mist md:text-lg">{intro}</p>}
      </Reveal>
      <div className="mt-12">{children}</div>
    </section>
  );
}
