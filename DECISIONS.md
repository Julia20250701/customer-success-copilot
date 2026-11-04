# Entscheidungsprotokoll

Jeder Eintrag dokumentiert eine Entscheidung: was entschieden wurde, warum, und welche Alternative verworfen wurde. Einträge werden nicht gelöscht oder überschrieben. Wird eine Entscheidung später geändert, bleibt der alte Eintrag stehen und bekommt den Vermerk „ersetzt durch 00X".

## 001 · 2026-11-04 · Entwicklung nur in WSL 2 (Ubuntu)

**Entscheidung:** Entwicklung ausschließlich in WSL 2 (Ubuntu), nicht gemischt mit Windows.
**Begründung:** Gleiche Umgebung wie auf Servern, Docker läuft ohne Umwege.
**Verworfene Alternative:** Native Windows-Entwicklung.

## 002 · 2026-11-04 · uv und pyproject.toml statt requirements.txt

**Entscheidung:** Abhängigkeits- und Projektverwaltung mit uv und pyproject.toml.
**Begründung:** Reproduzierbare Installation mit einem Befehl.
**Verworfene Alternative:** pip mit requirements.txt.

## 003 · 2026-11-04 · Fiktive Firma „Gastgeber Cloud"

**Entscheidung:** Das Projekt basiert auf der fiktiven Firma „Gastgeber Cloud" (Hotel- und Restaurant-Software).
**Begründung:** Realistische Kundendaten ohne echte Firmendaten; passt zu Jules Gastro-Erfahrung.
**Verworfene Alternative:** Echtes Unternehmen oder öffentlicher Datensatz.

## 004 · 2026-11-04 · Code und Kommentare auf Englisch, Erklärungen auf Deutsch

**Entscheidung:** Code und Kommentare werden auf Englisch geschrieben, Erklärungen an Jule auf Deutsch.
**Begründung:** Standard in Tech-Teams.
**Verworfene Alternative:** Alles auf Deutsch.

## 005 · 2026-11-04 · OpenAI als LLM-Anbieter

**Entscheidung:** OpenAI wird als LLM-Anbieter verwendet.
**Begründung:** API-Key ist bereits vorhanden.
**Verworfene Alternative:** Anthropic.

## 006 · 2026-11-04 · Repo von Anfang an öffentlich

**Entscheidung:** Das GitHub-Repo wird von Anfang an öffentlich angelegt.
**Begründung:** Recruiter sehen den Fortschritt über sieben Wochen; alle Daten sind fiktiv, daher kein Risiko.
**Verworfene Alternative:** Privat starten und am Ende veröffentlichen.
