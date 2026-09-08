import Nav from "./components/Nav";
import About from "./sections/About";
import Builds from "./sections/Builds";
import Footer from "./sections/Footer";
import Hero from "./sections/Hero";
import Interview from "./sections/Interview";
import Track from "./sections/Track";

export default function App() {
  return (
    <>
      <a className="skip-link" href="#interview">
        Skip to the interview agent
      </a>
      <Nav />
      <main>
        <Hero />
        <About />
        <Track />
        <Builds />
        <Interview />
      </main>
      <Footer />
    </>
  );
}
