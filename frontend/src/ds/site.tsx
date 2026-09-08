import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";

import { Button, IconButton, StackChip, StatusPill, type BuildStatus } from "./core";
import { Icon, type IconName } from "./Icon";

/*
 * Site components from the DeGarmo design system export
 * (components/site/*.jsx).
 */

// --- ParallaxBackdrop -----------------------------------------------------

/** Arterial-pressure-style trace, generated from a function — no illustration assets. */
function pulsePath(width: number, height: number, cycles: number): string {
  const pts: Array<[number, number]> = [];
  const steps = 220;
  for (let i = 0; i <= steps; i += 1) {
    const t = i / steps;
    const p = ((t * cycles) % 1) as number;
    // systolic upstroke, dicrotic notch, diastolic decay
    let v = 0.12 + 0.06 * Math.sin(t * 12);
    if (p < 0.08) v += (p / 0.08) * 0.78;
    else if (p < 0.2) v += 0.78 - ((p - 0.08) / 0.12) * 0.28;
    else if (p < 0.26) v += 0.5 + ((p - 0.2) / 0.06) * 0.1;
    else if (p < 0.7) v += 0.6 * Math.pow(1 - (p - 0.26) / 0.44, 1.6);
    pts.push([t * width, height - v * height * 0.82]);
  }
  return `M${pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(" L")}`;
}

interface ParallaxBackdropProps {
  variant?: "hero" | "section";
  trace?: boolean;
  grid?: boolean;
  glow?: boolean;
}

export function ParallaxBackdrop({
  variant = "hero",
  trace = true,
  grid = true,
  glow = true,
}: ParallaxBackdropProps) {
  const [y, setY] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const reduced =
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (reduced) {
      return;
    }
    let raf = 0;
    const onScroll = () => {
      raf =
        raf ||
        requestAnimationFrame(() => {
          raf = 0;
          const el = ref.current;
          if (!el) {
            return;
          }
          setY(-el.getBoundingClientRect().top);
        });
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) {
        cancelAnimationFrame(raf);
      }
    };
  }, [reduced]);

  const layer = (speed: number): CSSProperties => ({
    transform: `translate3d(0,${(y * speed).toFixed(1)}px,0)`,
    willChange: reduced ? undefined : "transform",
  });

  return (
    <div
      ref={ref}
      className="parallax-backdrop"
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
        zIndex: 0,
      }}
    >
      {grid ? (
        <div
          className="ds-grid-field"
          style={{
            position: "absolute",
            inset: "-20% 0 -20% 0",
            maskImage: "radial-gradient(120% 80% at 50% 20%, #000 30%, transparent 78%)",
            WebkitMaskImage:
              "radial-gradient(120% 80% at 50% 20%, #000 30%, transparent 78%)",
            ...layer(0.12),
          }}
        />
      ) : null}

      {glow ? (
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: variant === "hero" ? "-10%" : "10%",
            width: "min(1200px, 130%)",
            aspectRatio: "2 / 1",
            marginLeft: "min(-600px, -65%)",
            background:
              "radial-gradient(closest-side, var(--amber-a12), transparent 70%)",
            ...layer(0.24),
          }}
        />
      ) : null}

      {trace ? (
        <svg
          viewBox="0 0 1200 300"
          preserveAspectRatio="none"
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: variant === "hero" ? "8%" : "18%",
            width: "100%",
            height: "38%",
            opacity: 0.9,
            ...layer(0.4),
          }}
        >
          <path
            d={pulsePath(1200, 300, 5)}
            fill="none"
            stroke="var(--trace-line)"
            strokeWidth="1.5"
            vectorEffect="non-scaling-stroke"
          />
          <path
            d={pulsePath(1200, 300, 2.5)}
            fill="none"
            stroke="var(--grid-line)"
            strokeWidth="1"
            vectorEffect="non-scaling-stroke"
            transform="translate(0,26)"
          />
        </svg>
      ) : null}
    </div>
  );
}

// --- Hero -----------------------------------------------------------------

interface HeroProps {
  name: string;
  location: string;
  positioning: string;
  subline: string;
  primaryLabel: string;
  primaryHref: string;
  secondaryLabel: string;
  secondaryHref: string;
}

export function Hero({
  name,
  location,
  positioning,
  subline,
  primaryLabel,
  primaryHref,
  secondaryLabel,
  secondaryHref,
}: HeroProps) {
  return (
    <header
      id="top"
      className="hero"
      style={{
        position: "relative",
        overflow: "hidden",
        background: "var(--bg-page)",
        borderBottom: "1px solid var(--border-hairline)",
      }}
    >
      <ParallaxBackdrop variant="hero" />
      <div
        className="ds-container"
        style={{
          position: "relative",
          zIndex: 1,
          paddingTop: "clamp(120px, 18vh, 200px)",
          paddingBottom: "clamp(88px, 14vh, 160px)",
        }}
      >
        <p className="ds-eyebrow" style={{ marginBottom: "var(--space-8)" }}>
          {location}
        </p>
        <h1
          className="hero__name"
          style={{
            font: "var(--text-hero)",
            letterSpacing: "var(--tracking-display)",
            color: "var(--text-strong)",
          }}
        >
          {name}
        </h1>
        <p
          className="hero__positioning"
          style={{
            font: "var(--text-h3)",
            color: "var(--text-strong)",
            marginTop: "var(--space-8)",
            maxWidth: "24ch",
          }}
        >
          {positioning}
        </p>
        <p
          className="hero__sub"
          style={{
            font: "var(--text-lead)",
            color: "var(--text-muted)",
            marginTop: "var(--space-5)",
            maxWidth: "var(--measure-prose)",
          }}
        >
          {subline}
        </p>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "var(--space-4)",
            marginTop: "var(--space-10)",
          }}
        >
          <Button
            variant="primary"
            size="lg"
            href={primaryHref}
            icon="message-square"
            iconSide="left"
          >
            {primaryLabel}
          </Button>
          <Button variant="secondary" size="lg" href={secondaryHref} icon="arrow-down">
            {secondaryLabel}
          </Button>
        </div>
      </div>
    </header>
  );
}

// --- Nav ------------------------------------------------------------------

export interface NavLink {
  label: string;
  href: string;
}

interface NavProps {
  name: string;
  links: readonly NavLink[];
  ctaLabel?: string;
  ctaHref?: string;
  revealAfter?: number;
}

export function Nav({
  name,
  links,
  ctaLabel = "Interview me",
  ctaHref = "#interview",
  revealAfter = 320,
}: NavProps) {
  const [shown, setShown] = useState(revealAfter === 0);
  const [compact, setCompact] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setShown(window.scrollY > revealAfter);
    const mq = window.matchMedia("(max-width: 767px)");
    const onMq = () => {
      setCompact(mq.matches);
      if (!mq.matches) {
        setOpen(false);
      }
    };
    onScroll();
    onMq();
    window.addEventListener("scroll", onScroll, { passive: true });
    mq.addEventListener("change", onMq);
    return () => {
      window.removeEventListener("scroll", onScroll);
      mq.removeEventListener("change", onMq);
    };
  }, [revealAfter]);

  const hidden = !shown && !open;

  return (
    <nav
      className="nav"
      // A nav that has faded out must not be reachable by keyboard either.
      inert={hidden ? true : undefined}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        background: "var(--surface-glass)",
        backdropFilter: "var(--blur-glass)",
        WebkitBackdropFilter: "var(--blur-glass)",
        borderBottom: "1px solid var(--border-hairline)",
        opacity: shown ? 1 : 0,
        transform: shown ? "none" : "translateY(-8px)",
        pointerEvents: shown ? "auto" : "none",
        transition:
          "opacity var(--dur-slow) var(--ease-out), transform var(--dur-slow) var(--ease-out)",
      }}
    >
      <div
        className="ds-container"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-6)",
          height: 60,
        }}
      >
        <a
          href="#top"
          style={{
            font: "var(--weight-semibold) var(--step-0) / 1 var(--font-display)",
            letterSpacing: "var(--tracking-heading)",
            color: "var(--text-strong)",
            border: 0,
          }}
        >
          {name}
        </a>
        <span style={{ flex: 1 }} />

        {!compact &&
          links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              style={{ font: "var(--text-small)", color: "var(--text-muted)", border: 0 }}
            >
              {l.label}
            </a>
          ))}

        {!compact && (
          <Button variant="secondary" size="sm" href={ctaHref}>
            {ctaLabel}
          </Button>
        )}

        {compact && (
          <IconButton
            icon={open ? "x" : "menu"}
            label={open ? "Close menu" : "Open menu"}
            variant="ghost"
            size="lg"
            onClick={() => setOpen(!open)}
          />
        )}
      </div>

      {compact && open ? (
        <div
          className="nav__panel"
          style={{
            borderTop: "1px solid var(--border-hairline)",
            background: "var(--surface-1)",
            padding: "var(--space-4) var(--gutter) var(--space-6)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-4)",
          }}
        >
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              style={{ font: "var(--text-lead)", color: "var(--text-body)", border: 0 }}
            >
              {l.label}
            </a>
          ))}
          <Button variant="primary" href={ctaHref} fullWidth onClick={() => setOpen(false)}>
            {ctaLabel}
          </Button>
        </div>
      ) : null}
    </nav>
  );
}

// --- AboutBlock -----------------------------------------------------------

interface AboutBlockProps {
  icon?: IconName;
  label: string;
  children: ReactNode;
}

export function AboutBlock({ icon = "map-pin", label, children }: AboutBlockProps) {
  return (
    <div
      className="about-block"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-4)",
        paddingTop: "var(--space-5)",
        borderTop: "1px solid var(--border-subtle)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
          color: "var(--text-accent)",
        }}
      >
        <Icon name={icon} size={16} />
        <span className="ds-eyebrow" style={{ color: "var(--text-strong)" }}>
          {label}
        </span>
      </div>
      <p
        style={{
          font: "var(--text-base)",
          color: "var(--text-muted)",
          maxWidth: "var(--measure-narrow)",
        }}
      >
        {children}
      </p>
    </div>
  );
}

// --- ProjectCard ----------------------------------------------------------

interface ProjectCardProps {
  name: string;
  summary: string;
  stack: readonly string[];
  status?: BuildStatus;
  href?: string;
}

export function ProjectCard({
  name,
  summary,
  stack = [],
  status = "active",
  href,
}: ProjectCardProps) {
  const [hover, setHover] = useState(false);

  const style: CSSProperties = {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-4)",
    padding: "var(--space-6)",
    background: hover ? "var(--surface-card-hover)" : "var(--surface-card)",
    border: `1px solid ${hover ? "var(--border-accent)" : "var(--border-subtle)"}`,
    borderRadius: "var(--radius-md)",
    boxShadow: hover ? "var(--shadow-lift)" : "var(--shadow-1)",
    transform: hover ? "var(--lift-hover)" : "none",
    transition:
      "transform var(--dur-base) var(--ease-out), box-shadow var(--dur-base) var(--ease-out), border-color var(--dur-base) var(--ease-out), background var(--dur-base) var(--ease-out)",
    textDecoration: "none",
    color: "inherit",
    height: "100%",
  };

  const inner = (
    <>
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "var(--space-4)",
        }}
      >
        <h3
          style={{
            font: "var(--text-title)",
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-2)",
          }}
        >
          {name}
          {href ? (
            <Icon
              name="arrow-up-right"
              size={16}
              style={{
                color: hover ? "var(--text-accent)" : "var(--text-faint)",
                transition: "color var(--dur-fast) var(--ease-out)",
              }}
            />
          ) : null}
        </h3>
        <StatusPill status={status} />
      </div>
      <p style={{ font: "var(--text-base)", color: "var(--text-muted)", flex: 1 }}>
        {summary}
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
        {stack.map((s) => (
          <StackChip key={s}>{s}</StackChip>
        ))}
      </div>
    </>
  );

  const handlers = {
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
  };

  if (href) {
    return (
      <a className="project-card" href={href} style={style} {...handlers}>
        {inner}
      </a>
    );
  }
  return (
    <div className="project-card" style={style} {...handlers}>
      {inner}
    </div>
  );
}

// --- TimelineNode ---------------------------------------------------------

interface TimelineNodeProps {
  role: string;
  employer: string;
  dates: string;
  bullets: readonly string[];
  last?: boolean;
}

export function TimelineNode({
  role,
  employer,
  dates,
  bullets = [],
  last = false,
}: TimelineNodeProps) {
  return (
    <li
      className="timeline-node"
      style={{
        position: "relative",
        display: "grid",
        gridTemplateColumns: "1px 1fr",
        gap: "var(--space-6)",
        paddingBottom: last ? 0 : "var(--space-12)",
        listStyle: "none",
      }}
    >
      <div
        style={{
          position: "relative",
          background: last ? "transparent" : "var(--border-subtle)",
        }}
      >
        <span
          style={{
            position: "absolute",
            top: 6,
            left: -4,
            width: 9,
            height: 9,
            borderRadius: "50%",
            background: "var(--accent)",
            boxShadow: "0 0 0 4px var(--bg-page), 0 0 0 5px var(--amber-a20)",
          }}
        />
      </div>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-3)",
          marginTop: -2,
        }}
      >
        <span
          style={{
            font: "var(--text-data)",
            color: "var(--text-faint)",
            letterSpacing: "var(--tracking-meta)",
            textTransform: "uppercase",
          }}
        >
          {dates}
        </span>
        <h3 style={{ font: "var(--text-title)" }}>{role}</h3>
        <span style={{ font: "var(--text-small)", color: "var(--text-accent)" }}>
          {employer}
        </span>
        <ul
          style={{
            margin: "var(--space-2) 0 0",
            padding: 0,
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
            maxWidth: "var(--measure-prose)",
          }}
        >
          {bullets.map((b) => (
            <li
              key={b}
              style={{
                display: "grid",
                gridTemplateColumns: "10px 1fr",
                gap: "var(--space-3)",
                font: "var(--text-base)",
                color: "var(--text-muted)",
                listStyle: "none",
              }}
            >
              <span
                aria-hidden="true"
                style={{
                  color: "var(--text-faint)",
                  font: "var(--text-data)",
                  marginTop: 4,
                }}
              >
                —
              </span>
              <span>{b}</span>
            </li>
          ))}
        </ul>
      </div>
    </li>
  );
}

// --- Footer ---------------------------------------------------------------

function FooterLink({
  icon,
  label,
  href,
}: {
  icon: IconName;
  label: string;
  href: string;
}) {
  return (
    <a
      href={href}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-2)",
        font: "var(--text-small)",
        color: "var(--text-body)",
        border: 0,
      }}
    >
      <Icon name={icon} size={16} />
      {label}
    </a>
  );
}

interface FooterProps {
  email: string;
  linkedin: string;
  github: string;
  githubHandle: string;
  note?: string;
}

export function Footer({
  email,
  linkedin,
  github,
  githubHandle,
  note = "Built with Django, React, and Claude. Deployed on Render.",
}: FooterProps) {
  return (
    <footer
      className="footer"
      style={{
        borderTop: "1px solid var(--border-hairline)",
        background: "var(--bg-sunken)",
        paddingBlock: "var(--space-12)",
      }}
    >
      <div
        className="ds-container"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "var(--space-6) var(--space-8)",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-6)" }}>
          <FooterLink icon="mail" label={email} href={`mailto:${email}`} />
          <FooterLink icon="link" label="LinkedIn" href={linkedin} />
          <FooterLink icon="github" label={githubHandle} href={github} />
        </div>
        <p style={{ font: "var(--text-data)", color: "var(--text-faint)" }}>{note}</p>
      </div>
    </footer>
  );
}
