import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { Why } from "@/components/Why";
import { Dataset } from "@/components/Dataset";
import { Species } from "@/components/Species";
import { Nutrition } from "@/components/Nutrition";
import { Validation } from "@/components/Validation";
import { PaperViewer } from "@/components/PaperViewer";
import { CodeSection } from "@/components/CodeSection";
import { GetData } from "@/components/GetData";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <Why />
        <Dataset />
        <Species />
        <Nutrition />
        <Validation />
        <PaperViewer />
        <CodeSection />
        <GetData />
      </main>
      <Footer />
    </>
  );
}
