import ParallaxLayer from "../components/ParallaxLayer";
import { BUILDS, type BuildStatus } from "../content";
import styles from "./Builds.module.css";

const STATUS_CLASS: Record<BuildStatus, string> = {
  Deployed: styles.deployed,
  Beta: styles.beta,
  Active: styles.active,
};

export default function Builds() {
  return (
    <section id="builds" className="section">
      <ParallaxLayer speed={0.06} className={styles.backdrop} />

      <div className="container">
        <span className="eyebrow">Builds</span>
        <h2 className="section-title">Shipped, not mocked up.</h2>

        <ul className={styles.grid}>
          {BUILDS.map((build) => (
            <li key={build.name} className={styles.card}>
              <div className={styles.cardHead}>
                <h3 className={styles.name}>{build.name}</h3>
                <span className={`${styles.status} ${STATUS_CLASS[build.status]}`}>
                  {build.status}
                </span>
              </div>
              <p className={styles.what}>{build.what}</p>
              <ul className={styles.stack}>
                {build.stack.map((tag) => (
                  <li key={tag}>{tag}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
