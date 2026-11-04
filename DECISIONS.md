# Decision Log

Each entry documents a decision: what was decided, why, and which alternative was rejected. Entries are never deleted or overwritten. If a decision changes later, the old entry stays and gets a note "superseded by 00X".

## 001 · 2026-11-04 · Development only in WSL 2 (Ubuntu)

**Decision:** Development takes place exclusively in WSL 2 (Ubuntu), not mixed with Windows.
**Reasoning:** Same environment as on servers; Docker runs without detours.
**Rejected alternative:** Native Windows development.

## 002 · 2026-11-04 · uv and pyproject.toml instead of requirements.txt

**Decision:** Dependency and project management with uv and pyproject.toml.
**Reasoning:** Reproducible installation with a single command.
**Rejected alternative:** pip with requirements.txt.

## 003 · 2026-11-04 · Fictional company "Gastgeber Cloud"

**Decision:** The project is based on the fictional company "Gastgeber Cloud" (hotel and restaurant software).
**Reasoning:** Domain knowledge from more than 10 years in hospitality and food service enables realistic customer data, tickets, and processes – without any real company data.
**Rejected alternative:** A real company or a public dataset.

## 004 · 2026-11-04 · Repository language is English

**Decision:** All repository content (code, docs, issues, commits, user interface) is in English. Explanations to Jule in English by default; in German when she asks.
**Reasoning:** English is the working language in most software teams and makes the project readable for international collaborators. Explanations stay flexible so that understanding always comes first.
**Rejected alternative:** A bilingual setup (German and English) – more maintenance, no real benefit.

## 005 · 2026-11-04 · OpenAI as LLM provider

**Decision:** OpenAI is used as the LLM provider.
**Reasoning:** An API key is already available.
**Rejected alternative:** Anthropic.

## 006 · 2026-11-04 · Repo public from the start

**Decision:** The GitHub repo is created public from the start.
**Reasoning:** A traceable development history through the commit log. The project contains only fictional data and no secrets, so there is no risk.
**Rejected alternative:** Start private and open it up at the end.

## 007 · 2026-11-04 · Project name customer-success-copilot

**Decision:** The project name describes the function (customer-success-copilot).
**Reasoning:** Gastgeber Cloud remains the fictional company within the data.
**Rejected alternative:** Name the project after the fictional company.
