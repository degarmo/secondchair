import ParallaxLayer from "../components/ParallaxLayer";
import { ABOUT } from "../content";
import styles from "./About.module.css";

export default function About() {
  return (
    <section id="about" className="section">
      <ParallaxLayer speed={0.09} className={styles.backdrop} />

      <div className="container">
        <span className="eyebrow">{ABOUT.eyebrow}</span>
        <h2 className="section-title">{ABOUT.title}</h2>
        <div className="prose">
          {ABOUT.paragraphs.map((paragraph) => (
            <p key={paragraph.slice(0, 32)}>{paragraph}</p>
          ))}
        </div>
      </div>
    </section>
  );
}
