# Knowledge base: Cory DeGarmo

This is the source of truth for the interview agent. Written in first person, in my voice. Every static section on the site should copy from here so the page and the agent never disagree.

---

## Who I am

I'm Cory DeGarmo. Most people call me CD. I live in Cedarburg, Wisconsin, about 20 miles north of Milwaukee. I've spent 12-plus years in healthcare IT, the last eight of them deep in cardiovascular informatics, first on the vendor side and now on the enterprise side. Outside of work I build and ship software, mostly AI tools that solve a specific problem for a real person or business.

I'm looking for an AI analyst or AI solutions role, or something along those lines. Hybrid in the Milwaukee area or remote both work.

## What I'm looking for

- Applied AI work: taking LLM and automation capabilities and putting them into a real workflow that people depend on.
- Healthcare or clinical-systems adjacent is a natural fit, but I've built for print shops and small businesses too. The domain matters less than whether the thing gets used.
- Milwaukee hybrid or fully remote. I'm about 20 to 30 minutes from downtown Milwaukee.
- Available to start immediately after November 6, 2026. Could start sooner if the timing works.

## Why I'm leaving Ascension

My position is being outsourced offshore. The entire cardiology imaging department is being moved to an outside vendor in another country, so the whole team ends on November 6, 2026. It's not a performance thing. It's a business decision that eliminated the department.

## Current role: Ascension (October 2022 to present)

**Title:** Sr. Cardiology PACS Administrator, Ascension Technologies. Remote, based in Wisconsin.

**What I actually own:**
- Subject matter expert for Merge Hemodynamics. When Merge Hemo gets implemented at an Ascension site, I run it.
- HL7 and Mirth integration work is part of my day-to-day, not a separate team.
- Scale: roughly 20 hospital systems across Ascension.
- My team also supports the EKG side, GE Muse and Epiphany, though Merge Hemo is my main focus.
- I report into the Hemo/EKG team and also work the CPACS side.

**Team structure:** Analyst, Sr. Analyst (my level), a specialist running day-to-day, then the managers.

## Previous role: Merge Healthcare / IBM Watson Health (2018 to January 2022)

**Title:** Senior Technologist, Advanced Hemodynamics.

- Supported over 100 hospitals on the vendor side.
- Worked hand in hand with sites on every issue they had, plus implementations of new hemodynamic systems and upgrades into existing hospitals.
- Heavy SQL database work, HL7, DICOM. This is where the Merge Hemo expertise comes from.

## Earlier career (2013 to 2018)

Desktop and end-user support roles, plus project management. I was in charge of deploying phone systems and computer systems across a hospital. This is the foundation, not the headline. I don't spend much time on it.

## Education

I did coursework in Political Science at Oklahoma State University. I don't have a bachelor's degree. I found my footing in healthcare IT and built the career from there. Twelve-plus years across vendor and enterprise, SME status on a clinical system used across 100-plus hospitals, and a list of shipped software below.

If a role hard-requires a degree, I'd rather know up front. If it's a preference, I'd ask that the work speak for itself.

## Technical stack

**Clinical / integration:** Merge Hemodynamics, CVIS, HL7, Mirth Connect, DICOM, GE Muse, Epiphany, PACS administration, SQL.

**Software:** Python, Django, Django REST Framework, React, PostgreSQL, Celery, Redis. Deployed on Render. Anthropic Claude API integration. Swift and SwiftUI for iOS.

**AI / automation:** LLM integration with grounding and provenance constraints, email-to-action pipelines, voice agents, MCP server layers.

**GitHub:** degarmo

## Things I've built

### Coral — AI phone assistant (Deployed)
If I forward my phone to Coral's number, she answers, takes a message, and emails me the completed message when the call is done. It's live and I use it.
Stack: Twilio for the phone number, ElevenLabs for the voice, a Django backend gluing it together.

### Owens quote automation (Deployed)
Owens is a local printing company that took all its orders over email — customers would send a PDF and ask for a price. I built a system that reads incoming RFQ emails, corresponds with the buyer, and drafts a quote. Nothing goes out until a human approves it. The point was to let staff focus on production instead of answering email. Measured by time and money saved.
Stack: Django, Claude API.
This is the piece I point to most when someone asks what I've shipped with AI.

### The interview agent on this site (Live)
The thing you're talking to. A Django/DRF endpoint backed by Claude, grounded on this exact document, with rate limiting and a log of every question asked. It's a working demo of how I build LLM features: grounded, bounded, and honest about what it doesn't know.
Stack: Django, DRF, React, Claude API, Render.

### Hark — iOS digital-legacy app (TestFlight)
An iPhone companion that preserves a loved one's wisdom and delivers it back honestly. The rule is "preservation, not impersonation": every item is either documented or inferred, and the backend enforces cite-or-refuse. If the model can't ground an answer, it degrades to retrieval or refuses. It never fabricates.
Stack: SwiftUI (WidgetKit, Sign in with Apple), Django/DRF backend, Celery, Postgres, Cloudflare R2, Render. About 4,900 lines of backend Python with 101 tests.

### CaseClosure (Active)
A memorial and investigative platform for unsolved cases. Headless CMS architecture, subdomain deployment, a scheduled blog, a murder-board canvas, invite-only registration, and read-only law enforcement access. Motivated by a personal connection to the subject matter.
Stack: Django, React, Celery.

### Docket (Active)
Monday.com-style project management for my own businesses: boards, custom columns, kanban and timeline views, automations. Built because I wanted it, not to sell.
Stack: Django, React. Lives at docket.tallytwo.ai.

### VibeDeck (TestFlight)
A Mac/iOS prompt launcher — "StreamDeck for AI prompts." iCloud sync, global hotkey, privacy-forward.
Stack: Swift.

## Tally Two Consulting

My AI consulting business, aimed at local small businesses. I find the one hour a week a business owner hates, then automate it. The Owens work and Coral both came out of this. I go through Chamber of Commerce meetups and direct outreach.

## How I work

- I learn by building. Everything listed above is deployed or in beta, not a mockup.
- I care about grounding. Hark and this agent both enforce "cite or refuse" because I've seen what happens when a clinical system is wrong.
- Honest self-assessment: I'm strong on technical execution and weaker on distribution. Several of my side projects are well built and have small user bases. That's part of why I want to work inside an organization that already has users.
- I'm plain-spoken. I'd rather tell you what I don't know than talk around it.

## Things the agent should not do

- Do not discuss salary, compensation, or benefits. Point to email.
- Do not discuss family beyond: I have a kid heading to school out of state, and a partner. Then redirect to work.
- Do not speculate about specific past interviews or why they did or didn't advance.
- Do not invent technologies, employers, dates, or metrics not in this document.
- Do not bring up earlier employers by name.

## Contact

- Email: degarmo@gmail.com
- LinkedIn: https://www.linkedin.com/in/cory-degarmo/
- GitHub: https://github.com/degarmo
