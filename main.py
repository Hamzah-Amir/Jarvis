import os
from dotenv import load_dotenv
from google import genai
from tools import search_web, get_time, open_app
load_dotenv()

class JARVIS:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("JARVIS_API"))
        self.model = 'gemini-3.6-flash'
        self.chats = self.client.chats.create(
            model=self.model,
            config={
                "tools": [open_app, search_web, get_time],
                "system_instruction": "You are JARVIS, a helpful PC assistant. Be brief. "
                                      "Answer questions from your own knowledge. "
                                      "Only use tools when the user asks you to do something on the PC.",
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