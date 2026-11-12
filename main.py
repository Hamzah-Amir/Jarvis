import os
from google import genai
from tools import search_web, get_time, open_app, silent_search, open_web, remember, list_topics, recall
from datetime import datetime
from configs import STORAGE_DIR, CHATS_DIR, MEMORY_DIR, PROFILE_FILE,MODEL, slugify
from dotenv import load_dotenv
from pathlib import Path
import json
load_dotenv()

SYSTEM_PROMPT = """You are JARVIS, a personal assistant running on the user's Windows PC.

Style:
- Reply in plain text only. No markdown: no #, no **, no bullet symbols, no tables.
  Your replies are shown in a terminal and may be read aloud.
- Be brief: 1-3 sentences by default. Give longer answers only when the user
  asks for detail, a history, an explanation or a list.
- Be friendly and direct. Don't repeat the question or add filler.

Answering:
- Answer from your own knowledge whenever you can.
- Use silent_search only for recent or live information (news, scores, weather,
  prices, recent events). Summarize the results in your own words.
- Use the PC tools only when the user asks you to do something on the computer.
- After using a tool, say briefly what you did or found. If a tool fails, say so honestly.
- If a request is unclear, ask one short question instead of guessing.
"""


class JARVIS:
    def __init__(self):
        Path(STORAGE_DIR).mkdir(exist_ok=True)
        Path(MEMORY_DIR).mkdir(exist_ok=True)
        Path(CHATS_DIR).mkdir(exist_ok=True)
        Path(PROFILE_FILE).touch(exist_ok=True)
        prompt = SYSTEM_PROMPT
        profile = PROFILE_FILE.read_text(encoding='utf-8').strip()
        if profile:
            prompt += f"What you know about the User:\n{profile}"
        self.chat_file = None
        self.client = genai.Client(api_key=os.getenv("JARVIS_API"))
        self.chats = self.client.chats.create(
            model=MODEL,
            config={
                "tools": [search_web, get_time, open_app, silent_search, open_web, remember, list_topics, recall],
                "system_instruction": prompt,
            })

    def ask(self, text: str) ->str:
        reply = self.chats.send_message(text)
        if self.chat_file is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            title = slugify(text)
            file_name = CHATS_DIR / f"{timestamp}_{title}.json"
            file_name.touch()
            self.chat_file = file_name
        self.save_chats()
        return reply.text
    
    def save_chats(self) -> None:
        chat_history = self.chats.get_history()
        history = [content.model_dump(mode='json', exclude_none=True)
                   for content in chat_history]
        with open(self.chat_file, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=2)

    def run(self):
        try:    
            while True:
                user = input("You: ")
                if user.lower() in ('exit', 'quit'):
                    break
                reply = self.ask(user)
                print("JARVIS:", reply)
        except KeyboardInterrupt:
            print("Going standby!")

if __name__ == "__main__":
    jarvis = JARVIS()
    jarvis.run()