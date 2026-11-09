# SkillGraph - AI Career Intelligence Platform

## Run
Backend:
  cd backend && pip install -r requirements.txt
  export ANTHROPIC_API_KEY=sk-ant-...   # optional; without it the assistant uses a rule-based explanation
  uvicorn main:app --reload
Frontend (new terminal):
  cd frontend && npm install && npm run dev   -> http://localhost:5173

## What is implemented
- Auth (JWT), profile in SQLite
- Resume upload (PDF/txt) -> skill extraction + alias/fuzzy normalization
- Evidence-based confidence (projects, certs, GitHub, assessment score)
- Readiness score and gap priority = importance x gap x demand x (1 + 0.25 x downstream gaps unlocked)
- Skill graph (React Flow), multi-role career paths, phased roadmap, project recommendations
- What-if simulator, Claude-powered explanations/assistant (engine.explain)
Data lives in backend/engine.py (SKILLS, ROLES, PROJECTS); extend those to grow the knowledge base.
