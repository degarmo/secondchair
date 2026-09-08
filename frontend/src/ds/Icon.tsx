import type { CSSProperties, SVGProps } from "react";

/*
 * Lucide 0.x outline icons (stroke, 24x24, round caps) plus one brand mark
 * from Simple Icons, ported from the design system export.
 *
 * `mic`, `square` and `volume-2` are additions: the export predates the voice
 * controls, so they are drawn from the same Lucide set to stay on-system.
 */

const BRAND = new Set(["github"]);

const PATHS = {
  activity:
    '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"></path>',
  "arrow-down": '<path d="M12 5v14"></path> <path d="m19 12-7 7-7-7"></path>',
  "arrow-up-right": '<path d="M7 7h10v10"></path> <path d="M7 17 17 7"></path>',
  "at-sign":
    '<circle cx="12" cy="12" r="4"></circle> <path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8"></path>',
  briefcase:
    '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path> <rect width="20" height="14" x="2" y="6" rx="2"></rect>',
  check: '<path d="M20 6 9 17l-5-5"></path>',
  "chevron-down": '<path d="m6 9 6 6 6-6"></path>',
  "circle-dot":
    '<circle cx="12" cy="12" r="1"></circle> <circle cx="12" cy="12" r="10"></circle>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"></rect> <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path>',
  github:
    '<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"></path>',
  globe:
    '<circle cx="12" cy="12" r="10"></circle> <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path> <path d="M2 12h20"></path>',
  "heart-pulse":
    '<path d="M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5"></path> <path d="M3.22 13H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"></path>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path> <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>',
  "loader-circle": '<path d="M21 12a9 9 0 1 1-6.219-8.56"></path>',
  mail: '<path d="m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7"></path> <rect x="2" y="4" width="20" height="16" rx="2"></rect>',
  "map-pin":
    '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"></path> <circle cx="12" cy="10" r="3"></circle>',
  menu: '<path d="M4 5h16"></path> <path d="M4 12h16"></path> <path d="M4 19h16"></path>',
  "message-square":
    '<path d="M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"></path>',
  mic: '<path d="M12 19v3"></path> <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path> <rect x="9" y="2" width="6" height="13" rx="3"></rect>',
  send: '<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"></path> <path d="m21.854 2.147-10.94 10.939"></path>',
  server:
    '<rect width="20" height="8" x="2" y="2" rx="2" ry="2"></rect> <rect width="20" height="8" x="2" y="14" rx="2" ry="2"></rect> <line x1="6" x2="6.01" y1="6" y2="6"></line> <line x1="6" x2="6.01" y1="18" y2="18"></line>',
  smartphone:
    '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"></rect> <path d="M12 18h.01"></path>',
  square: '<rect width="18" height="18" x="3" y="3" rx="2"></rect>',
  terminal: '<path d="M12 19h8"></path> <path d="m4 17 6-6-6-6"></path>',
  "triangle-alert":
    '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path> <path d="M12 9v4"></path> <path d="M12 17h.01"></path>',
  "volume-2":
    '<path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"></path> <path d="M16 9a5 5 0 0 1 0 6"></path> <path d="M19.364 18.364a9 9 0 0 0 0-12.728"></path>',
  wrench:
    '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"></path>',
  x: '<path d="M18 6 6 18"></path> <path d="m6 6 12 12"></path>',
} as const;

export type IconName = keyof typeof PATHS;

interface IconProps extends Omit<SVGProps<SVGSVGElement>, "name"> {
  name: IconName;
  size?: number;
  strokeWidth?: number;
  /** Give the icon a name only when it carries meaning on its own. */
  label?: string;
  style?: CSSProperties;
  className?: string;
}

export function Icon({
  name,
  size = 20,
  strokeWidth = 1.75,
  label,
  style,
  className = "",
  ...rest
}: IconProps) {
  const inner = PATHS[name];
  if (!inner) {
    return null;
  }
  const brand = BRAND.has(name);

  return (
    <svg
      className={`ds-icon ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={brand ? "currentColor" : "none"}
      stroke={brand ? "none" : "currentColor"}
      strokeWidth={brand ? undefined : strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label || undefined}
      aria-hidden={label ? undefined : "true"}
      style={{ display: "block", flex: "none", ...style }}
      dangerouslySetInnerHTML={{ __html: inner }}
      {...rest}
    />
  );
}
