import os
from datetime import datetime
import subprocess
import webbrowser
from tavily import TavilyClient

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

def search_web(query: str) -> str:
    """Open a Google search for the query in the user's web browser.
    Only use this when the user explicitly asks to search the web, google something,
    or open results in the browser. You cannot read the results, so never use this
    to answer questions yourself."""
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

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(silent_search("Who won the 2026 US midterm elections?", topic="news"))