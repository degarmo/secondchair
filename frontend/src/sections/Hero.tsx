import { ArrowDown, MapPin } from "lucide-react";

import ParallaxLayer from "../components/ParallaxLayer";
import { HERO } from "../content";
import styles from "./Hero.module.css";

export default function Hero() {
  return (
    <section id="hero" className="section">
      <ParallaxLayer speed={0.18} className={styles.backdrop} />

      <div className="container">
        <div className={styles.content}>
          <h1 className={styles.name}>{HERO.name}</h1>
          <p className={styles.positioning}>{HERO.positioning}</p>
          <p className={styles.supporting}>{HERO.supporting}</p>
          <p className={styles.location}>
            <MapPin size={14} aria-hidden="true" />
            {HERO.location}
          </p>

          <div className={styles.actions}>
            <a className={styles.primary} href={HERO.primaryCta.href}>
              {HERO.primaryCta.label}
              <ArrowDown size={16} aria-hidden="true" />
            </a>
            <a className={styles.secondary} href={HERO.secondaryCta.href}>
              {HERO.secondaryCta.label}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
