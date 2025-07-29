import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os
import uvicorn
import requests

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"message": "AG-UI Backend is Running ✅"}

@app.post("/query")
async def get_response(query: Query):
    try:
        user_input = query.message
        response = model.generate_content(user_input)
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}

@app.get("/github-status")
async def get_latest_github_status():
    try:
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs?per_page=1"
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            return {
                "error": f"Failed to fetch: {res.status_code}",
                "details": res.json()
            }

        run_data = res.json()
        runs = run_data.get("workflow_runs", [])
        if not runs:
            return {"status": "No workflow runs found."}

        latest_run = runs[0]
        return {
            "status": latest_run["conclusion"],
            "branch": latest_run["head_branch"],
            "updated_at": latest_run["updated_at"],
            "html_url": latest_run["html_url"]
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
