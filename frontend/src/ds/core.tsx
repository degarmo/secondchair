import { useState, type CSSProperties, type ReactNode } from "react";

import { Icon, type IconName } from "./Icon";

/*
 * Core primitives from the DeGarmo design system export
 * (components/core/*.jsx). Styling stays inline and token-driven exactly as
 * the export has it, so a regenerated export can be diffed against this file.
 */

// --- Button ---------------------------------------------------------------

const BUTTON_SIZES = {
  sm: { padding: "7px 13px", fontSize: "var(--step--1)", icon: 14, gap: "var(--space-2)" },
  md: { padding: "12px 20px", fontSize: "var(--step-0)", icon: 16, gap: "var(--space-2)" },
  lg: { padding: "16px 28px", fontSize: "var(--step-1)", icon: 18, gap: "var(--space-3)" },
} as const;

interface ButtonProps {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  size?: keyof typeof BUTTON_SIZES;
  icon?: IconName;
  iconSide?: "left" | "right";
  href?: string;
  disabled?: boolean;
  fullWidth?: boolean;
  type?: "button" | "submit";
  onClick?: () => void;
  className?: string;
  style?: CSSProperties;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  iconSide = "right",
  href,
  disabled = false,
  fullWidth = false,
  type = "button",
  onClick,
  className = "",
  style,
}: ButtonProps) {
  const [hover, setHover] = useState(false);
  const [press, setPress] = useState(false);
  const s = BUTTON_SIZES[size] ?? BUTTON_SIZES.md;

  const skins: Record<string, CSSProperties> = {
    primary: {
      background: hover && !disabled ? "var(--accent-hover)" : "var(--accent)",
      color: "var(--text-on-accent)",
      border: "1px solid transparent",
      boxShadow: hover && !disabled ? "var(--shadow-2)" : "var(--shadow-1)",
    },
    secondary: {
      background: hover && !disabled ? "var(--accent-wash)" : "transparent",
      color: "var(--text-strong)",
      border: `1px solid ${
        hover && !disabled ? "var(--border-accent)" : "var(--border-strong)"
      }`,
      boxShadow: "none",
    },
    ghost: {
      background: "transparent",
      color: hover && !disabled ? "var(--accent-hover)" : "var(--text-accent)",
      border: "1px solid transparent",
      boxShadow: "none",
      padding: 0,
    },
  };

  const composed: CSSProperties = {
    display: fullWidth ? "flex" : "inline-flex",
    width: fullWidth ? "100%" : undefined,
    alignItems: "center",
    justifyContent: "center",
    gap: s.gap,
    padding: s.padding,
    fontFamily: "var(--font-display)",
    fontWeight: "var(--weight-medium)" as CSSProperties["fontWeight"],
    fontSize: s.fontSize,
    lineHeight: 1.1,
    letterSpacing: "-0.01em",
    borderRadius: "var(--radius-sm)",
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.45 : 1,
    textDecoration: "none",
    transform:
      press && !disabled
        ? "scale(var(--press-scale))"
        : hover && !disabled
          ? "var(--lift-hover)"
          : "none",
    transition:
      "background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out), box-shadow var(--dur-base) var(--ease-out)",
    ...skins[variant],
    ...style,
  };

  const glyph = icon ? <Icon name={icon} size={s.icon} strokeWidth={1.9} /> : null;
  const content = (
    <>
      {iconSide === "left" ? glyph : null}
      <span>{children}</span>
      {iconSide === "right" ? glyph : null}
    </>
  );

  const handlers = {
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => {
      setHover(false);
      setPress(false);
    },
    onMouseDown: () => setPress(true),
    onMouseUp: () => setPress(false),
  };

  if (href && !disabled) {
    return (
      <a
        className={`btn btn--${variant} ${className}`.trim()}
        href={href}
        style={composed}
        onClick={onClick}
        {...handlers}
      >
        {content}
      </a>
    );
  }

  return (
    <button
      className={`btn btn--${variant} ${className}`.trim()}
      type={type}
      disabled={disabled}
      style={composed}
      onClick={onClick}
      {...handlers}
    >
      {content}
    </button>
  );
}

// --- IconButton -----------------------------------------------------------

const ICON_BUTTON_SIZES = { sm: 30, md: 38, lg: 44 } as const;

interface IconButtonProps {
  icon: IconName;
  label: string;
  variant?: "primary" | "secondary" | "ghost";
  size?: keyof typeof ICON_BUTTON_SIZES;
  disabled?: boolean;
  type?: "button" | "submit";
  pressed?: boolean;
  onClick?: () => void;
  className?: string;
  style?: CSSProperties;
}

export function IconButton({
  icon,
  label,
  variant = "secondary",
  size = "md",
  disabled = false,
  type = "button",
  pressed,
  onClick,
  className = "",
  style,
}: IconButtonProps) {
  const [hover, setHover] = useState(false);
  const box = ICON_BUTTON_SIZES[size] ?? ICON_BUTTON_SIZES.md;

  const skins: Record<string, CSSProperties> = {
    primary: {
      background: hover && !disabled ? "var(--accent-hover)" : "var(--accent)",
      color: "var(--text-on-accent)",
      border: "1px solid transparent",
    },
    secondary: {
      background: hover && !disabled ? "var(--accent-wash)" : "transparent",
      color: "var(--text-strong)",
      border: `1px solid ${
        hover && !disabled ? "var(--border-accent)" : "var(--border-subtle)"
      }`,
    },
    ghost: {
      background: "transparent",
      color: hover && !disabled ? "var(--text-strong)" : "var(--text-muted)",
      border: "1px solid transparent",
    },
  };

  return (
    <button
      className={`icon-button ${className}`.trim()}
      type={type}
      aria-label={label}
      aria-pressed={pressed}
      title={label}
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: box,
        height: box,
        minWidth: box,
        borderRadius: "var(--radius-sm)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.4 : 1,
        transition:
          "background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out)",
        ...skins[variant],
        ...style,
      }}
    >
      <Icon name={icon} size={size === "sm" ? 15 : 18} strokeWidth={1.9} />
    </button>
  );
}

// --- SectionHeading -------------------------------------------------------

interface SectionHeadingProps {
  index?: string;
  eyebrow?: string;
  title: string;
  sub?: string;
  align?: "left" | "center";
  className?: string;
  style?: CSSProperties;
}

export function SectionHeading({
  index,
  eyebrow,
  title,
  sub,
  align = "left",
  className = "",
  style,
}: SectionHeadingProps) {
  return (
    <header
      className={`section-heading ${className}`.trim()}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-4)",
        textAlign: align,
        alignItems: align === "center" ? "center" : "stretch",
        maxWidth: align === "center" ? "var(--measure-prose)" : undefined,
        marginInline: align === "center" ? "auto" : undefined,
        ...style,
      }}
    >
      {eyebrow || index ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
            color: "var(--text-faint)",
          }}
        >
          {index ? (
            <span
              style={{
                font: "var(--text-eyebrow)",
                letterSpacing: "var(--tracking-meta)",
                color: "var(--text-accent)",
              }}
            >
              {index}
            </span>
          ) : null}
          {eyebrow ? <span className="ds-eyebrow">{eyebrow}</span> : null}
          <span style={{ flex: 1, height: 1, background: "var(--border-hairline)" }} />
        </div>
      ) : null}

      <h2
        style={{
          font: "var(--text-h2)",
          letterSpacing: "var(--tracking-heading)",
          maxWidth: "22ch",
          marginInline: align === "center" ? "auto" : undefined,
        }}
      >
        {title}
      </h2>

      {sub ? (
        <p
          style={{
            font: "var(--text-lead)",
            color: "var(--text-muted)",
            maxWidth: "var(--measure-prose)",
            marginInline: align === "center" ? "auto" : undefined,
          }}
        >
          {sub}
        </p>
      ) : null}
    </header>
  );
}

// --- StackChip ------------------------------------------------------------

export function StackChip({ children }: { children: ReactNode }) {
  return (
    <span
      className="stack-chip"
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "3px 7px",
        font: "var(--text-data)",
        color: "var(--text-muted)",
        background: "var(--surface-inset)",
        border: "1px solid var(--border-hairline)",
        borderRadius: "var(--radius-xs)",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </span>
  );
}

// --- StatusPill -----------------------------------------------------------

const STATUS = {
  deployed: {
    label: "Deployed",
    fg: "var(--status-deployed)",
    bg: "var(--status-deployed-bg)",
    pulse: false,
  },
  live: {
    label: "Live",
    fg: "var(--status-live)",
    bg: "var(--status-live-bg)",
    pulse: true,
  },
  beta: {
    label: "TestFlight",
    fg: "var(--status-beta)",
    bg: "var(--status-beta-bg)",
    pulse: false,
  },
  active: {
    label: "Active",
    fg: "var(--status-active)",
    bg: "var(--status-active-bg)",
    pulse: false,
  },
} as const;

export type BuildStatus = keyof typeof STATUS;

export function StatusPill({ status = "active" }: { status?: BuildStatus }) {
  const s = STATUS[status] ?? STATUS.active;
  return (
    <span
      className={`status-pill status-pill--${status}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-2)",
        padding: "4px 9px 4px 8px",
        background: s.bg,
        color: s.fg,
        border: "1px solid currentColor",
        borderRadius: "var(--radius-pill)",
        font: "var(--text-eyebrow)",
        letterSpacing: "var(--tracking-meta)",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
      }}
    >
      <span
        style={{
          width: 5,
          height: 5,
          borderRadius: "50%",
          background: "currentColor",
          animation: s.pulse ? "ds-pulse 2.4s var(--ease-in-out) infinite" : undefined,
        }}
      />
      {s.label}
    </span>
  );
}
