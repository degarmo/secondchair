import type { BuildStatus } from "./ds/core";
import type { IconName } from "./ds/Icon";
import type { NavLink } from "./ds/site";

/*
 * Every fact here is copied from backend/kb/KNOWLEDGE_BASE.md. When the
 * knowledge base changes, change this file in the same commit so the static
 * page and the interview agent never disagree.
 *
 * Section structure and headline copy follow the Claude Design export
 * (Cory DeGarmo.dc.html).
 */

export const CONTACT = {
  email: "degarmo@gmail.com",
  linkedin: "https://www.linkedin.com/in/cory-degarmo/",
  github: "https://github.com/degarmo",
  githubHandle: "degarmo",
} as const;

export const NAV_LINKS: readonly NavLink[] = [
  { label: "About", href: "#about" },
  { label: "Track record", href: "#track" },
  { label: "Builds", href: "#builds" },
];

export const HERO = {
  name: "Cory DeGarmo",
  location: "Cedarburg, WI · Hybrid Milwaukee or remote",
  positioning: "Healthcare IT lead. Ships AI that actually gets used.",
  subline:
    "12 years running clinical systems across 100+ hospitals. Now building AI tools for real businesses.",
  primaryLabel: "Interview me now",
  primaryHref: "#interview",
  secondaryLabel: "See what I've built",
  secondaryHref: "#builds",
} as const;

export const ABOUT = {
  index: "02",
  eyebrow: "About",
  title: "Three things worth knowing.",
  blocks: [
    {
      icon: "map-pin" as IconName,
      label: "Where I'm from",
      text: "Cedarburg, Wisconsin, about 20 miles north of Milwaukee. Open to hybrid in the Milwaukee area or fully remote.",
    },
    {
      icon: "heart-pulse" as IconName,
      label: "What I do",
      text: "Subject matter expert for Merge Hemodynamics at Ascension, across roughly 20 hospital systems. HL7 and Mirth integration work is day-to-day, not a separate team.",
    },
    {
      icon: "wrench" as IconName,
      label: "How I work",
      text: "I learn by building, and I care about grounding. Everything below is deployed or in beta, not a mockup.",
    },
  ],
} as const;

export const TRACK = {
  index: "03",
  eyebrow: "Track record",
  title: "Twelve years in clinical systems.",
  roles: [
    {
      role: "Sr. Cardiology PACS Administrator",
      employer: "Ascension Technologies",
      dates: "Oct 2022 – present",
      bullets: [
        "Subject matter expert for Merge Hemodynamics; runs every Merge Hemo implementation",
        "HL7 and Mirth integration work as part of the day-to-day",
        "Roughly 20 hospital systems; team also supports GE Muse and Epiphany on the EKG side",
      ],
      last: false,
    },
    {
      role: "Senior Technologist, Advanced Hemodynamics",
      employer: "Merge Healthcare / IBM Watson Health",
      dates: "2018 – Jan 2022",
      bullets: [
        "Supported over 100 hospitals on the vendor side",
        "Implementations of new hemodynamic systems and upgrades into existing hospitals",
        "Heavy SQL database work, HL7, DICOM",
      ],
      last: true,
    },
  ],
} as const;

export interface Build {
  name: string;
  summary: string;
  stack: readonly string[];
  status: BuildStatus;
}

export const BUILDS = {
  index: "04",
  eyebrow: "Builds",
  title: "Things that are actually running.",
  sub: "Deployed and live first. Nothing here is a slide.",
  items: [
    {
      name: "Coral",
      summary:
        "AI phone assistant. Forward a call, Coral answers, takes the message, emails it to you.",
      stack: ["Twilio", "ElevenLabs", "Django"],
      status: "deployed",
    },
    {
      name: "Owens quote automation",
      summary:
        "Reads incoming print-shop RFQ emails, corresponds with the buyer and drafts a quote. Nothing goes out until a human approves it.",
      stack: ["Django", "Claude API"],
      status: "deployed",
    },
    {
      name: "This interview agent",
      summary:
        "The thing at the bottom of the page. Grounded on one knowledge base, rate limited, and every question logged.",
      stack: ["Django", "DRF", "React", "Claude"],
      status: "live",
    },
    {
      name: "Hark",
      summary:
        "iOS app that preserves a loved one's wisdom under a cite-or-refuse rule — preservation, not impersonation.",
      stack: ["SwiftUI", "Django", "Celery", "Postgres"],
      status: "beta",
    },
    {
      name: "CaseClosure",
      summary:
        "Memorial and investigative platform for unsolved cases. Murder-board canvas, invite-only registration, read-only law enforcement access.",
      stack: ["Django", "React", "Celery"],
      status: "active",
    },
    {
      name: "Docket",
      summary:
        "Monday.com-style project management for my own businesses: boards, custom columns, kanban and timeline views, automations.",
      stack: ["Django", "React"],
      status: "active",
    },
    {
      name: "VibeDeck",
      summary: "Mac and iOS prompt launcher — StreamDeck for AI prompts. iCloud sync, global hotkey.",
      stack: ["Swift", "iCloud sync"],
      status: "beta",
    },
  ] satisfies readonly Build[],
} as const;

export const INTERVIEW = {
  index: "05",
  eyebrow: "Interview me",
  title: "Ask me anything you'd ask in a screen.",
  sub: "This agent is trained on my background. It'll tell you what I've done, what I haven't, and where to find me.",
  note: "Compensation questions go to a human. Email me.",
  prompts: [
    "What have you actually shipped with AI?",
    "Tell me about your healthcare IT background",
    "Why are you leaving Ascension?",
    "Do you have a degree?",
  ],
  greeting:
    "Ask away. I answer from a knowledge base I wrote, and I'll say so when something isn't in it.",
} as const;

export const FOOTER_NOTE =
  "Built with Django, React, and Claude. Deployed on Render.";
