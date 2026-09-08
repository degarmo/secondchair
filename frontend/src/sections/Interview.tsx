import AgentChat from "../components/AgentChat";
import ParallaxLayer from "../components/ParallaxLayer";
import { INTERVIEW } from "../content";
import styles from "./Interview.module.css";

export default function Interview() {
  return (
    <section id="interview" className="section">
      <ParallaxLayer speed={0.05} className={styles.backdrop} />

      <div className="container">
        <span className="eyebrow">{INTERVIEW.eyebrow}</span>
        <h2 className="section-title">{INTERVIEW.title}</h2>
        <p className={styles.intro}>{INTERVIEW.intro}</p>

        <AgentChat starters={INTERVIEW.starters} />
      </div>
    </section>
  );
}
