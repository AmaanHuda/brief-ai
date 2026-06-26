import os
import json
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BriefAI Brochure Generator")

app.add_middleware(
    CORSMiddleware,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=False,
    allow_headers=["*"],
)

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY")
print(API_KEY)
MODEL   = os.getenv("MODEL", "gemini-3.1-flash-lite")

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=API_KEY,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}


# ── Scraper helpers (from your original scraper.py) ─────────────────────────
def fetch_website_links(url: str) -> list[str]:
    """Return all href links found on the page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if href and not href.startswith(("mailto:", "tel:", "#", "javascript:")):
                links.append(href)
        return list(set(links))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch links from {url}: {e}")


def fetch_website_contents(url: str) -> str:
    """Return cleaned text content of a page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Collapse blank lines
        lines = [l for l in text.splitlines() if l.strip()]
        return "\n".join(lines)[:8_000]   # cap per page
    except Exception as e:
        return f"[Could not fetch {url}: {e}]"


# ── LLM helpers (from your original main.py) ─────────────────────────────────
LINK_SYSTEM_PROMPT = """
You are provided with a list of links found on a webpage.
Decide which links are most relevant for a company brochure:
links to About, Company, Mission, Products/Services, Careers/Jobs pages.
Respond ONLY with JSON in exactly this format:

{
    "links": [
        {"type": "about page", "url": "https://full.url/about"},
        {"type": "careers page", "url": "https://full.url/careers"}
    ]
}
"""

def get_links_user_prompt(url: str) -> str:
    links = fetch_website_links(url)
    prompt = (
        f"Here is the list of links on the website {url}.\n"
        "Choose the most relevant ones for a company brochure "
        "(About, Products, Careers). Return only full https URLs in JSON.\n"
        "Do not include Terms of Service, Privacy, or email links.\n\n"
        "Links (some may be relative):\n"
    )
    prompt += "\n".join(links[:200])   # cap at 200 links
    return prompt


def select_relevant_links(url: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": LINK_SYSTEM_PROMPT},
            {"role": "user",   "content": get_links_user_prompt(url)},
        ],
        response_format={"type": "json_object"},
    )
    result = response.choices[0].message.content
    return json.loads(result)


def fetch_page_and_all_relevant_links(url: str) -> str:
    contents = fetch_website_contents(url)
    relevant  = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n\n## Relevant Pages:\n"
    for link in relevant.get("links", []):
        result += f"\n\n### {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result


BROCHURE_SYSTEM_PROMPT = """
You are an expert sales strategist and client-focused business analyst.

Your task is to analyze a company’s website and generate a brochure specifically for potential clients or customers.

Your goal is NOT to summarize the website.
Your goal is to help a potential client quickly understand whether this company is worth doing business with.
If there are pieces of content missing, you predict the most positive response and give it as an output. Do not leave it blank or information missing.
Focus only on high-value information that influences buying decisions.

Go through their website and identlify what services they provide and to whom. For example they may be educational consultancy, law firm, etc. Identify their niche and address the clients accordingly
Extract and emphasize:

1. Core Offering
- What products or services does the company provide?
- What business problem do they solve?

2. Client Pain Points
Identify the customer problems this company is trying to solve.

3. Unique Value Proposition
- What makes this company different?
- Why choose them over competitors?

4. Benefits to Clients
Focus on outcomes, not just features. Identify who the clients are based on different models. It may be B2C or B2B
Examples:
- Saves time
- Reduces cost
- Improves efficiency
- Better performance
- Higher ROI

5. Credibility Signals
Look for:
- notable clients
- partnerships
- testimonials
- case studies
- awards
- years of experience
- certifications

6. Target Customers
Who is this company built for?
Examples:
- startups
- enterprises
- healthcare
- fintech
- e-commerce

7. Call-to-Action Insight
What should an interested client do next?
Examples:
- Book demo
- Contact sales
- Request consultation

Important rules:
- Write in markdown
- No code blocks
- Be concise but persuasive
- Avoid generic marketing fluff
- Avoid copying website slogans
- Rewrite content in clear professional language
- If information is missing, mention that clearly
- Focus on business value and customer outcomes

Use this structure:

# Company Name

## Executive Summary
2–4 sentences explaining what the company does and why clients should care.

## What They Offer
Products/services offered.

## Problems They Solve
Client pain points addressed.

## Why Choose Them
Competitive advantages and differentiators.

## Ideal Customers
Who benefits most from their services.

## Trust Signals
Proof of credibility.

## Final Verdict
A concise client-focused recommendation on whether this company appears valuable and trustworthy.


## Contacts
Get all the contact details from the website and response in a ordered manner such as:
- Phone number
- Email
- Social Media:     
    - Instagram
    - LinkedIn

etc 
##Employees
Give the list of their employes (if avaialable and their roles in the company along with their socials if avaliable. Fetch all the relevant information you can get of the employees too. )

For the above sections, if you cannot find data for something please do not generate it. Do not give negative response or null response. You are allowed to write what you understand from the website but do not give emply responses.

"""
def get_brochure_user_prompt(company_name: str, url: str) -> str:
    prompt = (
        f"You are looking at a company called: {company_name}\n"
        "Here are the contents of its landing page and other relevant pages. "
        "Use this to write a short, informative company brochure in markdown.\n\n"
    )
    prompt += fetch_page_and_all_relevant_links(url)
    return prompt[:10_000]   # safety truncation


# ── Request / Response models ─────────────────────────────────────────────────
class BrochureRequest(BaseModel):
    company_name: str
    url: str


class BrochureResponse(BaseModel):
    brochure: str
    company_name: str


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.post("/generate", response_model=BrochureResponse)
def generate_brochure(req: BrochureRequest):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY not set in environment.")
    if not req.company_name.strip() or not req.url.strip():
        raise HTTPException(status_code=422, detail="company_name and url are required.")

    user_prompt = get_brochure_user_prompt(req.company_name, req.url)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
    )

    brochure_text = response.choices[0].message.content.strip()
    if not brochure_text:
        raise HTTPException(status_code=500, detail="Model returned empty response.")

    return BrochureResponse(brochure=brochure_text, company_name=req.company_name)