import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os
import uvicorn
import requests
import datetime
from dateutil import parser as date_parser
from dateparser.search import search_dates
import re

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://git-repo-status.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],    
)

# Serve static frontend from 'dist'
dist_path = os.path.join(os.path.dirname(__file__), "dist")
app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

@app.get("/")
def serve_index():
    index_file = os.path.join(dist_path, "index.html")
    return FileResponse(index_file)


class Query(BaseModel):
    message: str


def extract_date_range(user_message: str):
    now = datetime.datetime.now()
    found_dates = search_dates(user_message, settings={"RELATIVE_BASE": now})

    if found_dates:
        text, dt = found_dates[0]
        year = dt.year
        if "last year" in user_message.lower():
            return datetime.date(year - 1, 1, 1), datetime.date(year - 1, 12, 31)
        elif "this year" in user_message.lower():
            return datetime.date(year, 1, 1), datetime.date(year, 12, 31)
        else:
            return dt.date(), dt.date()
    return now.date() - datetime.timedelta(days=7), now.date()


def count_open_github_bugs():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/search/issues?q=repo:{GITHUB_OWNER}/{GITHUB_REPO}+is:issue+is:open+label:bug"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return None, f"GitHub API error: {res.status_code}"
    return res.json().get("total_count", 0), None


def count_commits_between(from_date, to_date):
    since = datetime.datetime.combine(from_date, datetime.time.min).isoformat() + "Z"
    until = datetime.datetime.combine(to_date, datetime.time.max).isoformat() + "Z"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits"
        f"?since={since}&until={until}&per_page=100"
    )
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return None, f"GitHub API error: {res.status_code}"
    return len(res.json()), None


def get_merged_prs(from_date, to_date):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/pulls?state=closed&per_page=100"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return []
    all_prs = res.json()
    return [
        pr
        for pr in all_prs
        if pr.get("merged_at")
        and from_date <= date_parser.parse(pr["merged_at"]).date() <= to_date
    ]


def get_open_pull_requests():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/pulls?state=open&per_page=50"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return []
    prs = res.json()
    return [
        {
            "number": pr["number"],
            "title": pr["title"],
            "user": pr["user"]["login"],
            "created_at": pr["created_at"],
        }
        for pr in prs
    ]


def is_commit_sha(message: str):
    return re.search(r"\b[0-9a-f]{7,40}\b", message.lower())


def get_latest_commits(limit=5):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?per_page={limit}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return None, f"GitHub API error: {res.status_code}"
    return res.json(), None


@app.post("/query")
async def get_response(query: Query):
    user_input = query.message.strip()
    lowered = user_input.lower()

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        if lowered in [
            "what is the date",
            "what is the current date",
            "give me current date",
            "what is the time",
            "what is the current time",
            "give me current time",
            "current date",
            "current time",
        ]:
            now = datetime.datetime.now()
            formatted = now.strftime("%Y-%m-%d %H:%M:%S")
            return {"response": f"Current date and time is: {formatted}"}

        if "commit" in lowered and (
            "yesterday" in lowered
            or "last" in lowered
            or re.search(r"\d{4}-\d{2}-\d{2}", lowered)
        ):
            from_date, to_date = extract_date_range(user_input)
            count, error = count_commits_between(from_date, to_date)
            if error:
                return {"response": f"Error fetching commits: {error}"}
            return {
                "response": f"There were **{count}** commits between **{from_date}** and **{to_date}** in the `{GITHUB_REPO}` repository."
            }

        sha_match = is_commit_sha(user_input)
        if sha_match:
            commit_sha = sha_match.group(0)
            commit_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits/{commit_sha}"
            commit_res = requests.get(commit_url, headers=headers)
            if commit_res.status_code != 200:
                return {"response": f"Could not find commit `{commit_sha}`."}
            commit_data = commit_res.json()
            author = (
                commit_data.get("commit", {}).get("author", {}).get("name", "Unknown")
            )
            date = (
                commit_data.get("commit", {}).get("author", {}).get("date", "Unknown")
            )
            message = commit_data.get("commit", {}).get("message", "No commit message")
            return {
                "response": f"Commit `{commit_sha}` by **{author}** on {date}:\n> {message}"
            }

        if "latest commit" in lowered or "recent commit" in lowered:
            commits, error = get_latest_commits()
            if error:
                return {"response": error}
            if not commits:
                return {"response": "No commits found."}
            lines = []
            for idx, c in enumerate(commits, 1):
                sha = c['sha'][:7]
                author = c['commit']['author']['name']
                date = c['commit']['author']['date'][:10]
                message = c['commit']['message'].splitlines()[0]
                lines.append(
                    f"{idx}. {message}\n"
                    f"   • Commit: `{sha}`\n"
                    f"   • Author: {author}\n"
                    f"   • Date: {date}"
                )
            pretty_output = f"Latest Commits in `{GITHUB_REPO}`:\n\n" + "\n\n".join(lines)
            return {"response": pretty_output}

        if any(k in lowered for k in ["deploy", "release", "feature"]):
            from_date, to_date = extract_date_range(user_input)
            prs = get_merged_prs(from_date, to_date)
            if not prs:
                return {
                    "response": f"No deployments found between **{from_date}** and **{to_date}** in the `{GITHUB_REPO}` repository."
                }
            summary = "\n".join(
                [
                    f"- PR #{pr['number']}: {pr['title']} by {pr['user']['login']}"
                    for pr in prs
                ]
            )
            prompt = f"The user asked: {query.message}\n\nBetween {from_date} and {to_date}, the following pull requests were merged:\n\n{summary}\n\nSummarize from user perspective."
            response = model.generate_content(prompt)
            return {"response": response.text}

        if "open pull" in lowered:
            prs = get_open_pull_requests()
            if not prs:
                return {"response": "No open pull requests."}
            lines = "\n".join(
                [
                    f"- #{p['number']} by {p['user']} on {p['created_at'][:10]}"
                    for p in prs
                ]
            )
            return {"response": f"Open pull requests:\n{lines}"}

        if "bug" in lowered and ("how many" in lowered or "count" in lowered):
            count, error = count_open_github_bugs()
            if error:
                return {"response": f"Error: {error}"}
            return {"response": f"There are **{count}** open bugs in `{GITHUB_REPO}`."}

        response = model.generate_content(user_input)
        return {"response": response.text}

    except Exception as e:
        return {"error": str(e)}
