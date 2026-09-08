import ParallaxLayer from "../components/ParallaxLayer";
import { TRACK } from "../content";
import styles from "./Track.module.css";

export default function Track() {
  return (
    <section id="track" className="section">
      <ParallaxLayer speed={0.07} className={styles.backdrop} />

      <div className="container">
        <span className="eyebrow">Track record</span>
        <h2 className="section-title">Eight years in cardiovascular informatics.</h2>

        <ol className={styles.timeline}>
          {TRACK.map((entry) => (
            <li key={entry.employer} className={styles.entry}>
              <div className={styles.period}>{entry.period}</div>
              <div className={styles.body}>
                <h3 className={styles.employer}>{entry.employer}</h3>
                <p className={styles.title}>{entry.title}</p>
                <p className={styles.summary}>{entry.summary}</p>
                <ul className={styles.points}>
                  {entry.points.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
