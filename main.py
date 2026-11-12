import os
from dotenv import load_dotenv
from google import genai
from tools import search_web, get_time, open_app, silent_search, open_web
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
- If a request is unclear, ask one short question instead of guessing."""


class JARVIS:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("JARVIS_API"))
        self.model = 'gemini-3.6-flash'
        self.chats = self.client.chats.create(
            model=self.model,
            config={
                "tools": [open_app, open_web, search_web, get_time, silent_search],
                "system_instruction": SYSTEM_PROMPT,
            })

    def ask(self, text: str) ->str:
        reply = self.chats.send_message(text)
        return reply.text

    def run(self):
        while True:
            user = input("You: ")
            if user.lower() in ('exit', 'quit'):
                break
            reply = self.ask(user)
            print("JARVIS:", reply)

if __name__ == "__main__":
    jarvis = JARVIS()
    jarvis.run()