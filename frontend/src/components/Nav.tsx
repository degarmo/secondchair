import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

import { NAV_LINKS } from "../content";
import styles from "./Nav.module.css";

export default function Nav() {
  const [visible, setVisible] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  // The nav stays out of the way until the hero has scrolled past.
  useEffect(() => {
    const hero = document.getElementById("hero");
    if (!hero) {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => setVisible(!entry.isIntersecting),
      { threshold: 0.35 },
    );

    observer.observe(hero);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [menuOpen]);

  // A hidden nav must not be reachable by keyboard.
  const hidden = !visible && !menuOpen;

  return (
    <header
      className={`${styles.nav} ${visible || menuOpen ? styles.shown : ""}`}
      inert={hidden ? true : undefined}
    >
      <div className={styles.inner}>
        <a className={styles.wordmark} href="#hero">
          Cory DeGarmo
        </a>

        <nav aria-label="Sections">
          <ul className={styles.links}>
            {NAV_LINKS.map((link) => (
              <li key={link.id}>
                <a className={styles.link} href={`#${link.id}`}>
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <button
          type="button"
          className={styles.menuButton}
          aria-expanded={menuOpen}
          aria-controls="nav-menu"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <div
        id="nav-menu"
        className={`${styles.menu} ${menuOpen ? styles.menuOpen : ""}`}
        hidden={!menuOpen}
      >
        <ul>
          {NAV_LINKS.map((link) => (
            <li key={link.id}>
              <a href={`#${link.id}`} onClick={() => setMenuOpen(false)}>
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </header>
  );
}
