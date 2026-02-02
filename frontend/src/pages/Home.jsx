import Navbar from "../components/Layout/Navbar";
import Hero from "../components/Layout/Hero";
import Features from "../components/Layout/Features";
import CTA from "../components/Layout/CTA";
import Footer from "../components/Layout/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <Hero />
      <Features />
      <CTA />
      <Footer />
    </>
  );
}
