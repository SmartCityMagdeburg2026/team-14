from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI(title="MD-Hackathon Dashboard")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# ---------------------------------------------------------------------------
# Dummy data
# ---------------------------------------------------------------------------
DUMMY_DATA = {
    "title": "MD-Hackathon Dashboard",
    "stats": [
        {"label": "Total Projects", "value": 42, "icon": "📁"},
        {"label": "Active Users", "value": 128, "icon": "👥"},
        {"label": "Tasks Completed", "value": 317, "icon": "✅"},
        {"label": "Uptime", "value": "99.9 %", "icon": "⚡"},
    ],
    "recent_activity": [
        {"user": "Alice", "action": "Submitted proposal", "time": "2 min ago"},
        {"user": "Bob", "action": "Updated dataset", "time": "15 min ago"},
        {"user": "Carol", "action": "Opened issue #84", "time": "1 hr ago"},
        {"user": "Dave", "action": "Merged pull request", "time": "3 hr ago"},
        {"user": "Eve", "action": "Deployed to staging", "time": "5 hr ago"},
    ],
    "projects": [
        {"name": "Alpha", "status": "Active", "progress": 75},
        {"name": "Beta", "status": "Active", "progress": 50},
        {"name": "Gamma", "status": "Paused", "progress": 30},
        {"name": "Delta", "status": "Completed", "progress": 100},
    ],
}


@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=DUMMY_DATA,
    )
