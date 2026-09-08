import { Github, Linkedin, Mail } from "lucide-react";

import { CONTACT } from "../content";
import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        <p className={styles.note}>
          Built with Django, React, and the Claude API. The agent above is part
          of the work sample.
        </p>

        <ul className={styles.links}>
          <li>
            <a href={`mailto:${CONTACT.email}`}>
              <Mail size={16} aria-hidden="true" />
              {CONTACT.email}
            </a>
          </li>
          <li>
            <a href={CONTACT.linkedin} target="_blank" rel="noreferrer">
              <Linkedin size={16} aria-hidden="true" />
              LinkedIn
            </a>
          </li>
          <li>
            <a href={CONTACT.github} target="_blank" rel="noreferrer">
              <Github size={16} aria-hidden="true" />
              {CONTACT.githubHandle}
            </a>
          </li>
        </ul>
      </div>
    </footer>
  );
}
