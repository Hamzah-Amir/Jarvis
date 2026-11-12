import os
from datetime import datetime
import subprocess
import webbrowser

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

def search_web(query: str) ->str:
    """Open a Google search for the query in the user's web browser.
    Only use this when the user explicitly asks to search the web, google something,
    or open results in the browser. You cannot read the results, so never use this
    to answer questions yourself."""
    """Search on the default browser"""
    webbrowser.open(url=f"https://www.google.com/search?q={query}", new=0)
    return f"Searched for {query}"
