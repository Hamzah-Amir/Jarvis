import os
from datetime import datetime
import subprocess
import webbrowser
from tavily import TavilyClient
from configs import MEMORY_DIR, slugify

def get_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%A, %d %B %Y, %I:%M %p")

def open_app(name:str) -> str:
    """Open an application on windows (example notepad, excel, or any)"""
    try:
        os.startfile(name)
        return f"Opened app {name}"
    except OSError:
        return f"Cannot find the app: '{name}'"

def open_web(url: str) -> str:
    """Open a website in the user's default web browser.

    Use this when the user wants to open or go to a specific website,
    e.g. "open youtube", "go to github.com", "open my gmail".
    Convert site names to full URLs yourself, e.g. "youtube" -> "https://www.youtube.com".

    Do NOT use this to search for something. Use search_web for that.

    Args:
        url: The website URL, e.g. "https://www.youtube.com".
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        if webbrowser.open(url):
            return f"Opened {url} in the browser."
        return f"Could not open {url}: no browser found."
    except Exception as e:
        return f"Could not open {url}: {e}"

def search_web(query: str) -> str:
    """Open a Google search for the query in the user's web browser.
    Only use this when the user explicitly asks to search the web, google something,
    or open results in the browser. You cannot read the results, so never use this
    to answer questions yourself. Do NOT use this to open a website; use open_web for that."""
    webbrowser.open(url=f"https://www.google.com/search?q={query}", new=0)
    return f"Searched for {query}"

def silent_search(query: str, topic: str = "general") -> str:
    """Search the internet silently and return the results as text, without opening a browser.

    Use this when the question needs current or real-time information you may not know:
    news, sports scores and results, recent events, weather, prices, release dates,
    or anything that happened after your training data.

    Do NOT use this for general knowledge you already know (history, science, definitions).
    Do NOT use this when the user wants the browser opened. Use search_web for that.

    Args:
        query: A short, specific search query, e.g. "Pakistan vs Iran U17 AFC qualifier result".
        topic: "news" for recent events, sports, politics; "general" for everything else.

    Returns:
        A short answer followed by sources (title, URL, date, content).
    """
    try:
        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_KEY"))
        response = tavily_client.search(
            query, topic=topic, search_depth="basic", max_results=3, include_answer=True
        )

        parts = []
        if response.get("answer"):
            parts.append(f"Answer: {response['answer']}")

        for i, r in enumerate(response.get("results", []), start=1):
            source = f"Source {i}: {r.get('title', '')}\nURL: {r.get('url', '')}"
            if r.get("published_date"):
                source += f"\nDate: {r['published_date']}"
            source += f"\n{r.get('content', '')}"
            parts.append(source)

        if not parts:
            return "No results found."
        return "\n\n".join(parts)
    except Exception as e:
        return f"Search failed: {e}"

def list_topics() -> str:
    """List the names of all saved memory topics (e.g. "profile, preferences, jarvis-project").

    Call this BEFORE remember or recall, so you reuse an existing topic name
    instead of creating a new one with a slightly different name.
    """
    topics = [file.stem for file in MEMORY_DIR.glob("*.md")]
    if not topics:
        return "No topics yet."
    return ", ".join(topics)

def remember(topic: str, fact: str) -> str:
    """Save one important fact about the user to long-term memory.

    Use this when the user shares something worth remembering in future chats:
    personal info, preferences, ongoing projects, goals, people they mention, or when
    they say "remember that...". Do NOT save small talk, one-off questions or temporary details.

    Call list_topics first and reuse an existing topic if one fits.

    Args:
        topic: Short topic name, e.g. "profile" (name, studies, basics about the user),
            "preferences", "jarvis-project". Create a new topic only if none fits.
        fact: One short, self-contained fact that makes sense on its own later,
            e.g. "User's name is Hamza" or "Prefers Chrome as main browser".
    """
    try:
        topic = slugify(topic)
        path = MEMORY_DIR / f"{topic}.md"

        if path.exists():
            content = path.read_text(encoding="utf-8")
            if f"- {fact}" in content:
                return "Already saved." 
            
        with open(path, 'a', encoding='utf-8') as memory:
            memory.write(f"- {fact}\n")
        all_facts = path.read_text(encoding="utf-8").strip()
        return f"Saved to {topic}. This topic now contains:\n{all_facts}"
    except Exception as e:
        return f"Could not save memory: {e}"

def recall(topic:str) -> str:
    """Read everything saved in long-term memory about a topic.

    Use this when answering needs something you may have learned in a past chat:
    the user's personal info, preferences, projects, people they mentioned,
    or when they ask "do you remember...". Check memory before saying you don't know.

    Call list_topics first to see which topics exist, and pass an exact topic name.

    Args:
        topic: An existing topic name from list_topics, e.g. "profile", "preferences".
    """
    try:
        topic = slugify(topic)
        path = MEMORY_DIR / f"{topic}.md"
        if path.exists():
            content = path.read_text(encoding='utf-8').strip()
            return f"Memory of {topic}:\n{content}"
        return f"Nothing saved about {topic} in the memory"
    
    except Exception as e:
        return f"Could not read memory: {e}"

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(silent_search("Who won the 2026 US midterm elections?", topic="news"))