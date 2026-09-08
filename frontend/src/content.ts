/*
 * Every fact here is copied from backend/kb/KNOWLEDGE_BASE.md. When the
 * knowledge base changes, change this file in the same commit so the static
 * page and the interview agent never disagree.
 */

export const CONTACT = {
  email: "degarmo@gmail.com",
  linkedin: "https://www.linkedin.com/in/cory-degarmo/",
  github: "https://github.com/degarmo",
  githubHandle: "degarmo",
} as const;

export const NAV_LINKS = [
  { id: "hero", label: "Top" },
  { id: "about", label: "About" },
  { id: "track", label: "Track record" },
  { id: "builds", label: "Builds" },
  { id: "interview", label: "Interview me" },
] as const;

export const HERO = {
  name: "Cory DeGarmo",
  positioning: "Healthcare IT turned AI builder.",
  supporting:
    "Twelve-plus years in clinical systems, the last eight in cardiovascular informatics. Now I build applied AI that people actually use.",
  location: "Cedarburg, Wisconsin. Milwaukee hybrid or remote.",
  primaryCta: { label: "Interview me now", href: "#interview" },
  secondaryCta: { label: "See what I've built", href: "#builds" },
} as const;

export const ABOUT = {
  eyebrow: "About",
  title: "I learn by building.",
  paragraphs: [
    "I'm Cory DeGarmo. Most people call me CD. I live in Cedarburg, Wisconsin, about 20 miles north of Milwaukee. I've spent 12-plus years in healthcare IT, the last eight of them deep in cardiovascular informatics, first on the vendor side and now on the enterprise side.",
    "Outside of work I build and ship software, mostly AI tools that solve a specific problem for a real person or business. That work runs through Tally Two Consulting, my AI consulting business aimed at local small businesses: I find the one hour a week a business owner hates, then automate it.",
    "I'm looking for an AI analyst or AI solutions role, hybrid in the Milwaukee area or remote. I care about grounding, because I've seen what happens when a clinical system is wrong. And I'm plain-spoken: I'd rather tell you what I don't know than talk around it.",
  ],
} as const;

export type TrackEntry = {
  employer: string;
  title: string;
  period: string;
  summary: string;
  points: string[];
};

export const TRACK: TrackEntry[] = [
  {
    employer: "Ascension Technologies",
    title: "Sr. Cardiology PACS Administrator",
    period: "October 2022 - present",
    summary: "Remote, based in Wisconsin.",
    points: [
      "Subject matter expert for Merge Hemodynamics. When Merge Hemo gets implemented at an Ascension site, I run it.",
      "HL7 and Mirth integration work is part of my day-to-day, not a separate team.",
      "Scale: roughly 20 hospital systems across Ascension.",
      "My team also supports the EKG side, GE Muse and Epiphany, though Merge Hemo is my main focus.",
      "I report into the Hemo/EKG team and also work the CPACS side.",
    ],
  },
  {
    employer: "Merge Healthcare / IBM Watson Health",
    title: "Senior Technologist, Advanced Hemodynamics",
    period: "2018 - January 2022",
    summary: "Vendor side.",
    points: [
      "Supported over 100 hospitals on the vendor side.",
      "Worked hand in hand with sites on every issue they had, plus implementations of new hemodynamic systems and upgrades into existing hospitals.",
      "Heavy SQL database work, HL7, DICOM. This is where the Merge Hemo expertise comes from.",
    ],
  },
];

export type BuildStatus = "Deployed" | "Beta" | "Active";

export type Build = {
  name: string;
  what: string;
  stack: string[];
  status: BuildStatus;
};

export const BUILDS: Build[] = [
  {
    name: "Coral",
    what: "AI phone assistant: forward your phone, she answers, takes a message, and emails you the completed message when the call ends.",
    stack: ["Twilio", "ElevenLabs", "Django"],
    status: "Deployed",
  },
  {
    name: "Owens quote automation",
    what: "Reads incoming RFQ emails at a printing company, corresponds with the buyer, and drafts a quote. Nothing goes out until a human approves it.",
    stack: ["Django", "Claude API"],
    status: "Deployed",
  },
  {
    name: "Interview agent",
    what: "This site's agent. Grounded on one knowledge base, rate limited, and every question logged. Honest about what it doesn't know.",
    stack: ["Django", "DRF", "React", "Claude API", "Render"],
    status: "Deployed",
  },
  {
    name: "Hark",
    what: "iOS digital-legacy app. Preservation, not impersonation: the backend enforces cite-or-refuse and degrades to retrieval rather than fabricating.",
    stack: ["SwiftUI", "Django", "Celery", "Postgres", "Cloudflare R2"],
    status: "Beta",
  },
  {
    name: "CaseClosure",
    what: "Memorial and investigative platform for unsolved cases. Headless CMS, murder-board canvas, invite-only registration, read-only law enforcement access.",
    stack: ["Django", "React", "Celery"],
    status: "Active",
  },
  {
    name: "Docket",
    what: "Monday.com-style project management for my own businesses: boards, custom columns, kanban and timeline views, automations.",
    stack: ["Django", "React"],
    status: "Active",
  },
  {
    name: "VibeDeck",
    what: "A Mac and iOS prompt launcher, StreamDeck for AI prompts. iCloud sync, global hotkey, privacy-forward.",
    stack: ["Swift"],
    status: "Beta",
  },
];

export const INTERVIEW = {
  eyebrow: "Interview me",
  title: "Ask the agent.",
  intro:
    "This is an agent I built, grounded strictly in a knowledge base I wrote. It answers in my voice, and it says so when the knowledge base doesn't cover something. It will not talk about compensation.",
  starters: [
    "What have you actually shipped with AI?",
    "Tell me about your healthcare IT background",
    "Why are you leaving Ascension?",
    "Do you have a degree?",
  ],
} as const;
