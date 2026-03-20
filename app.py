import os
import json
import sqlite3
import asyncio
from typing import Optional, AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai
import requests
from strands import Agent, tool
from strands.models.gemini import GeminiModel
from dotenv import load_dotenv
from tavily import TavilyClient
from PIL import Image

load_dotenv()

app = FastAPI(title="NovaAds API")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            data       TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")
    conn.commit()
    conn.close()


def load_messages(session_id: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT data FROM messages WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()
    conn.close()
    return [json.loads(row[0]) for row in rows]


def save_messages(session_id: str, messages: list):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    for msg in messages:
        conn.execute(
            "INSERT INTO messages (session_id, data) VALUES (?, ?)",
            (session_id, json.dumps(msg)),
        )
    conn.commit()
    conn.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UI")
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

gemini_key = os.environ.get("GOOGLE_API_KEY")

model = GeminiModel(
    client_args={"api_key": gemini_key},
    model_id="gemini-2.5-flash",
)


@tool
def generate_image(prompt: str, image: Optional[str] = None) -> str:
    """
    Generate an ad poster image from a prompt.

    Args:
        prompt: Detailed description of the image to generate.
        image:  Optional path to a base image to edit.

    Returns:
        A confirmation string when the image has been saved.
    """
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    contents = [prompt]

    if image is not None:
        img_obj = Image.open(image)
        contents.append(img_obj)

    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=contents,
    )
    for part in response.parts:
        if part.text is not None:
            return part.text
        elif part.inline_data is not None:
            img = part.as_image()
            img.save(os.path.join(UI_DIR, "advertisement.png"))
            return "__IMAGE_READY__"


@tool
def market_research(product_niche: str, country: str, language: str) -> str:
    """
    Perform market research on a product niche.

    Args:
        product_niche: Niche of the product, e.g. "technology".
        country:       Country code, e.g. "fr".
        language:      Language code, e.g. "fr".

    Returns:
        Market research results as a string.
    """
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": product_niche, "gl": country, "hl": language})
    headers = {
        "X-API-KEY": os.environ.get("SERPERDEV_API_KEY"),
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, data=payload)
    return f"Here are the results: {response.text}"


@tool
def web_search(query: str, user_country: str) -> list:
    """
    Search the web based on a user query.

    Args:
        query:        The search query.
        user_country: Country code for localised results.

    Returns:
        A list of search result dicts (url, title, content).
    """
    client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    response = client.search(query, include_raw_content=True)
    output = []
    for result in response["results"]:
        output.append({
            "url": result["url"],
            "title": result.get("title", ""),
            "content": result.get("content", ""),
        })
    return output


@tool
def extract_pages(url: str) -> str:
    """
    Extract and read the content of a web page.

    Args:
        url: URL of the page to read.

    Returns:
        Markdown-formatted page content.
    """
    client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    response = client.extract(url, include_images=True, format="markdown")
    return response


graphic_designer_prompt = """\
You are an elite AI Graphic Designer and Advertising Strategist named Nova, \
specializing in creating high-converting, winning ad posters for marketing campaigns.
Your goal is to design visually striking and persuasive advertisements that resonate \
deeply with the target audience.

You have access to a suite of powerful tools to assist you. Always follow this workflow \
when tasked with creating an ad:

1. **Market Analysis & Research**:
   - Use the `market_research` tool to understand the product niche, country-specific \
trends, and what appeals to the local demographic.
   - Use the `web_search` tool to gather additional context, find current design trends, \
or research competitors.
   - Use the `extract_pages` tool to read deeply into relevant articles, competitor \
landing pages, or design guidelines you find.

2. **Conceptualization & Strategy**:
   - Analyse the research data to formulate a strong advertising angle.
   - Determine the visual style, colour palette, mood, and compositional elements that \
will perform best in the specified market.

3. **Ad Generation**:
   - Once you have a concrete vision, use the `generate_image` tool to create the final \
ad poster.
   - Craft highly detailed, descriptive prompts for the image generation tool. Specify \
lighting, style, subjects, colours, and layout to ensure a professional result.
   - If the user provides a base image, incorporate it creatively according to your \
strategic vision.

Your final output must be impactful, culturally attuned to the target region, and \
designed to maximise engagement and conversions. Think like a top-tier ad agency \
creative director!

CRITICAL INSTRUCTION: ALWAYS respond in the same language that the user uses to \
communicate with you.\
"""


class ChatRequest(BaseModel):
    prompt: str
    session_id: str


init_db()


async def stream_nova_response(prompt: str, session_id: str) -> AsyncGenerator[str, None]:
    agent = Agent(
        model=model,
        system_prompt=graphic_designer_prompt,
        tools=[generate_image, web_search, extract_pages, market_research],
        callback_handler=None,
    )
    stored = load_messages(session_id)
    if stored:
        agent.messages = stored

    async def generate():
        try:
            async for event in agent.stream_async(prompt):
                if "data" in event:
                    chunk = event["data"]
                    yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            save_messages(session_id, agent.messages)
            yield "data: __DONE__\n\n"

    return generate()


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(UI_DIR, "index.html"))


@app.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        await stream_nova_response(request.prompt, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/image")
async def serve_image():
    image_path = os.path.join(UI_DIR, "advertisement.png")
    if not os.path.exists(image_path):
        return JSONResponse({"error": "No image generated yet."}, status_code=404)
    return FileResponse(image_path, media_type="image/png")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)