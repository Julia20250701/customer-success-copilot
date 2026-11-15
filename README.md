# Customer Success Copilot

AI-powered Customer Success & Experience Copilot – using the fictional hotel and restaurant software Gastgeber Cloud as an example.

> Gastgeber Cloud is a fictional company. All data in this project is test data.

Gastgeber Cloud is a fictional software company that sells booking and point-of-sale software to hotels and restaurants. The copilot supports this company's Customer Success Manager: 200 fictional customers, health score, CX metrics (NPS, CSAT, CES), AI agents with human approval, n8n automation, a Streamlit interface, and Power BI.

## Project status

Board: [Customer Success Copilot](https://github.com/users/Julia20250701/projects/1)

Files in this repo:
- `README.md` – project description (this file)
- `DECISIONS.md` – log of key decisions
- `pyproject.toml` – Python project configuration (uv)
- `.python-version` – pinned Python version
- `.env.example` – template for environment variables (no real secrets)
- `.gitignore` – files excluded from the Git repo
- `docker-compose.yml` – local Postgres (with pgvector) via Docker Compose

## Run the database locally

Requires Docker Desktop to be running.

```bash
cp .env.example .env    # fill in your own local values
docker compose up -d    # start Postgres
docker compose ps       # check it's healthy
docker compose stop     # stop it (your data is kept)
```
