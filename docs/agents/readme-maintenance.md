# Maintaining the README

`README.md` must let a new developer **understand, run and use** the code base without asking anyone.

Required sections (keep them): what it is · architecture overview · repo layout · prerequisites · run backend / worker / app · configuration table (every env var) · API reference (every endpoint, example) · how to test · data sources & licences · decisions pointer · known limitations / not-yet-verified list · first-real-run checklist.

Update rule — in the **same change** as the code:
- new/changed env var → configuration table and `.env.example`
- new/changed endpoint or JSON field → API reference (and Android client if it consumes it)
- new command, dependency, service → run/prerequisite sections
- new source / licence → data sources
- verified a previously unverified thing → move it off the limitations list; found a new gap → add it

Before finishing a task: re-read the README diff; run each command you documented (or say you couldn't). Don't duplicate ADR reasoning in the README — link to it.
