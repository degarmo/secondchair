import InterviewAgent from "./components/InterviewAgent";
import {
  ABOUT,
  BUILDS,
  CONTACT,
  FOOTER_NOTE,
  HERO,
  INTERVIEW,
  NAV_LINKS,
  TRACK,
} from "./content";
import { SectionHeading } from "./ds/core";
import {
  AboutBlock,
  Footer,
  Hero,
  Nav,
  ParallaxBackdrop,
  ProjectCard,
  TimelineNode,
} from "./ds/site";

/*
 * Page composition follows the Claude Design export's Page.jsx / Sections.jsx.
 * All copy comes from content.ts, which mirrors the knowledge base.
 */

export default function App() {
  return (
    <div style={{ background: "var(--bg-page)", minHeight: "100vh" }}>
      <a className="ds-skip-link" href="#interview">
        Skip to the interview agent
      </a>

      <Nav
        name={HERO.name}
        links={NAV_LINKS}
        ctaLabel="Interview me"
        ctaHref="#interview"
      />

      <Hero {...HERO} />

      <main>
        <section id="about" style={{ paddingBlock: "var(--section-y)" }}>
          <div
            className="ds-container"
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-12)",
            }}
          >
            <SectionHeading
              index={ABOUT.index}
              eyebrow={ABOUT.eyebrow}
              title={ABOUT.title}
            />
            <div
              style={{
                display: "grid",
                gap: "var(--space-8)",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              }}
            >
              {ABOUT.blocks.map((b) => (
                <AboutBlock key={b.label} icon={b.icon} label={b.label}>
                  {b.text}
                </AboutBlock>
              ))}
            </div>
          </div>
        </section>

        <section
          id="track"
          style={{
            position: "relative",
            overflow: "hidden",
            paddingBlock: "var(--section-y)",
          }}
        >
          <ParallaxBackdrop variant="section" />
          <div
            className="ds-container"
            style={{
              position: "relative",
              zIndex: 1,
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-12)",
            }}
          >
            <SectionHeading
              index={TRACK.index}
              eyebrow={TRACK.eyebrow}
              title={TRACK.title}
            />
            <ol style={{ margin: 0, padding: 0 }}>
              {TRACK.roles.map((r) => (
                <TimelineNode
                  key={r.employer}
                  role={r.role}
                  employer={r.employer}
                  dates={r.dates}
                  bullets={r.bullets}
                  last={r.last}
                />
              ))}
            </ol>
          </div>
        </section>

        <section id="builds" style={{ paddingBlock: "var(--section-y)" }}>
          <div
            className="ds-container"
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-12)",
            }}
          >
            <SectionHeading
              index={BUILDS.index}
              eyebrow={BUILDS.eyebrow}
              title={BUILDS.title}
              sub={BUILDS.sub}
            />
            <div
              style={{
                display: "grid",
                gap: "var(--space-5)",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              }}
            >
              {BUILDS.items.map((b) => (
                <ProjectCard
                  key={b.name}
                  name={b.name}
                  summary={b.summary}
                  stack={b.stack}
                  status={b.status}
                />
              ))}
            </div>
          </div>
        </section>

        <section
          id="interview"
          style={{
            position: "relative",
            overflow: "hidden",
            paddingBlock: "var(--section-y)",
            background: "var(--bg-sunken)",
            borderTop: "1px solid var(--border-hairline)",
          }}
        >
          <ParallaxBackdrop variant="section" />
          <div
            className="ds-container"
            style={{
              position: "relative",
              zIndex: 1,
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-12)",
            }}
          >
            <SectionHeading
              index={INTERVIEW.index}
              eyebrow={INTERVIEW.eyebrow}
              title={INTERVIEW.title}
              sub={INTERVIEW.sub}
              align="center"
            />
            <InterviewAgent />
          </div>
        </section>
      </main>

      <Footer
        email={CONTACT.email}
        linkedin={CONTACT.linkedin}
        github={CONTACT.github}
        githubHandle={CONTACT.githubHandle}
        note={FOOTER_NOTE}
      />
    </div>
  );
}
