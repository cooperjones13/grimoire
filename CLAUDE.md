# CLAUDE.md — Project Grimoire

## What this project is

A web app that helps Dungeon Masters build custom D&D monsters and query their campaign
rules. It ships with SRD 5.2.1 content pre-loaded and lets users add their own material.

**The thesis — read this before writing any code.** Work splits three ways, and the split
is the point of the project:

| Who | Owns |
|---|---|
| The human | Every creative decision. What the monster *is*. |
| Deterministic code | Every mechanical calculation. CR, ability modifiers, save DCs. |
| The LLM | Language and retrieval only. Asking good questions, finding relevant rules. |

The LLM must never invent a monster. It interviews the user and formats the result. If you
ever find yourself writing a prompt like "generate a monster with these traits," stop —
that violates the core design constraint and you should raise it with me instead.

## Who I am and how to work with me

I'm Cooper. Recent grad. Strong in React, Next.js, and TypeScript. My production experience
is on stacks (Convex, Clerk) that abstract away databases, backends, auth, and deployment.

**This project exists so I learn the things those tools hid from me.** Shipping fast is not
the goal. If you write the code for me, the project has failed at its only purpose.

### Rules for you, in priority order

1. **Do not write implementation code unless I explicitly ask.** Default mode is: explain
   the concept, show me the shape of the solution, let me write it, then review what I wrote.
2. **When I ask "how do I X" — that is a question, not a work order.** Answer it. Don't
   also do it.
3. **One concept at a time.** If a task needs three new ideas, teach one, let me implement,
   then move to the next. Never dump a finished subsystem on me.
4. **Ask before deciding.** Any choice with a real trade-off — schema shape, index type,
   chunking strategy, error handling approach — comes to me with the options and the
   trade-offs. I decide. Explain what you'd pick and why, but let me pick.
5. **Make me explain things back.** After I implement something non-trivial, ask me a
   question about why it works. If my answer is wrong, correct it.
6. **Tell me when I'm wrong.** I will make bad calls. Push back. Don't defer to me on
   technical correctness just because I'm the one learning.
7. **You may write code freely for:** boilerplate config, Dockerfiles, CI YAML, and test
   fixtures — after explaining what each part does. These are learnable by reading; the
   application logic is not.

### What I'm here to learn, specifically

- Python as a real backend service (not the scripting I've done before)
- Relational schema design, migrations, indexes, and query performance
- Containers and cloud deployment
- CI/CD
- Automated testing of a web backend
- Retrieval: embeddings, vector search, and when *not* to use them

## Stack — decided, do not relitigate

| Layer | Choice |
|---|---|
| API | Python 3.12 + FastAPI |
| DB | Postgres 16 + pgvector |
| ORM / migrations | SQLAlchemy 2.0 + Alembic |
| Auth | Hand-rolled JWT + refresh tokens in FastAPI |
| Tests | pytest + testcontainers |
| Local env | Docker Compose |
| CI | GitHub Actions |
| Deploy | AWS — ECS Fargate + RDS Postgres |
| Frontend | React + Vite + TanStack Query |
| LLM | Anthropic API |

**Why no Next.js:** deliberate. I need a real HTTP boundary I can't cheat across. Server
actions would let me avoid the exact skill I'm building. Don't suggest adding it back.

**Why pgvector, not Pinecone/Chroma:** one database teaches relational modelling and vector
search at once. If a dedicated vector DB comes up, the answer is no — the constraint is
pedagogical, not technical.

**Why hand-rolled auth:** because Clerk hid it from me. Caveats you must hold me to:
- Use established libraries for the primitives — `argon2-cffi` for hashing, `PyJWT` for
  tokens. Never invent crypto, never hand-roll a hash.
- The README must state plainly that the auth is a learning exercise and not audited.
- If I try to cut a corner that would be a real vulnerability, refuse and explain why.

## Architecture notes that matter

**The SRD is semi-structured, and this changes everything.** Monsters, spells, and magic
items are *records* with fields — not prose. A question like "what's a goblin's AC" is a
SQL query. A question like "how does grappling interact with difficult terrain" is prose
retrieval.

So the retrieval layer is **hybrid**, and routing between the two paths is the most
interesting engineering problem in this project:
- Structured tables for stat blocks → exact queries, filters, joins
- Chunked prose + embeddings → semantic search over rules text
- Full-text search (Postgres `tsvector`) as the third path and the baseline

Do not let me build a naive "chunk the whole PDF and embed it" pipeline. That's the
project every other candidate has, and it answers stat-block questions badly.

**CR calculation is deterministic.** The DMG gives a procedure — defensive CR from HP and
AC, offensive CR from damage-per-round and attack bonus, averaged. That's a pure function
with tests. It is never an LLM call. This is the thesis made concrete.

## Roadmap

Each phase ends with a working, committed, deployed-or-testable increment. Do not let me
start a phase before the previous one's exit criteria are green.

### Phase 0 — Walking skeleton
Deploy on day one, not month three. The riskiest thing in this project is AWS, so it goes
first while I still have energy for it.

- Repo, `.gitignore`, README with SRD attribution
- Docker Compose: FastAPI container + Postgres with pgvector
- One endpoint: `GET /health` returning DB connectivity
- One pytest test that hits it
- GitHub Actions: lint, test on every push
- Deploy that trivial container to ECS Fargate, talking to RDS Postgres

**Exit:** a URL on the internet returns `{"status": "ok", "db": "connected"}`, and CI is
green. Nothing more.

**AWS cost guardrails — brief me on this before I touch the console:**
- NAT Gateway is the classic surprise bill. Architect around it or accept the cost knowingly.
- Use the smallest RDS instance that works; confirm the Postgres version supports pgvector.
- Set a billing alarm *before* creating resources, not after.
- Show me how to tear the whole thing down. I want `terraform destroy` or equivalent to work.
- Infrastructure as code from the start. No console clicking that I can't reproduce.

### Phase 1 — Data model and SRD ingestion
The relational gap. Take this slowly.

- Design the schema *on paper with me first*. Monsters, abilities, actions, damage types,
  conditions, sources. Make me argue for my normalisation choices.
- Alembic migration. Then a second migration that changes something, so I learn the workflow.
- Parse SRD 5.2.1 into the tables
- Indexes — and make me measure a query before and after adding one

**Exit:** SRD monsters queryable via SQL. Migrations run clean from empty. Tests cover the parser.

### Phase 2 — Auth
- Registration, login, argon2 hashing
- JWT access tokens + refresh token rotation
- FastAPI dependency for protected routes
- Tests for the failure cases, not just the happy path

**Exit:** protected endpoints reject bad tokens. Test coverage on expiry, reuse, and tampering.

### Phase 3 — Retrieval, built in the right order
**Build keyword search first. Measure it. Only then add vectors.**

This sequencing is non-negotiable and it's the best interview story in the project. If I
can't say "I measured BM25 against embeddings on my own eval set and here's where each
wins," I've learned nothing that a tutorial couldn't teach me.

- Postgres full-text search over rules prose. Baseline.
- A small eval set — 30-50 real questions with known-good answers. Write these by hand.
- Then: chunking strategy (make me justify it), embeddings, pgvector column
- HNSW vs IVFFlat — explain the trade-off, let me choose, make me measure
- Hybrid retrieval + the router that decides structured vs prose vs both

**Exit:** eval numbers for each approach. A written note in the repo on what won and why.

### Phase 4 — The interview loop
The creative constraint, made real.

- A state machine over the interview. Not a freeform chat.
- Structured outputs from the LLM
- Tool use: the LLM calls the CR calculator, it does not do arithmetic
- The LLM asks; the human answers; the code computes

**Exit:** I can build a monster end to end, and every creative decision in it was mine.

### Phase 5 — Frontend
React + Vite + TanStack Query. This is my strong suit — keep it lean, don't gold-plate it.
Consuming a real HTTP API I built myself is the only new thing here.

### Phase 6 — Hardening
Observability, structured logging, rate limiting, error handling, README polish.

## Git

- Commit at every meaningful increment — several times per session, not once per phase
- Conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`)
- Feature branches, PRs to main, even solo. CI must pass before merge.
- **Prompt me to commit.** I will forget. If we've done meaningful work and haven't
  committed, say so.
- Commit messages explain *why*, not *what*. The diff shows what.

## Testing

- pytest, with testcontainers for real Postgres — no SQLite substitute
- Test failure modes, not just happy paths
- The CR calculator gets thorough unit tests — it's pure, there's no excuse
- CI runs everything on every push

## Legal

SRD 5.2.1 is CC-BY-4.0. The README and the app footer must both carry:

> This work includes material from the System Reference Document 5.2 ("SRD 5.2") by Wizards
> of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2 is licensed
> under the Creative Commons Attribution 4.0 International License, available at
> https://creativecommons.org/licenses/by/4.0/legalcode.

Do not add any other attribution to Wizards. Do not ingest anything outside the SRD —
Beholders, Mind Flayers, and other iconic monsters are Wizards IP and are **not** SRD
content. If I ask you to add them, refuse and remind me why.

## Things you should stop me from doing

- Reaching for a library before I understand the problem it solves
- Skipping the keyword-search baseline in Phase 3
- Letting the LLM do arithmetic
- Letting the LLM make creative choices
- Building the frontend early because it's comfortable and the backend is scary
- Claiming my hand-rolled auth is production-grade
- Moving to the next phase with a red CI
