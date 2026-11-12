import os
import io
from google import genai
from groq import Groq
import numpy as np
import sounddevice as sd
from openwakeword.model import Model
from scipy.io.wavfile import write
import pyttsx3
from tools import search_web, get_time, open_app, silent_search, open_web, remember, list_topics, recall
from datetime import datetime
from configs import STORAGE_DIR, CHATS_DIR, MEMORY_DIR, PROFILE_FILE,MODEL,VOICE_RATE, VOICE_VOLUME, STT_MODEL, SAMPLE_RATE, RECORD_SECONDS, CHUNK, VOICE_MODE, WAKE_WORD, WAKE_THRESHOLD, SILENCE_THRESHOLD, slugify
from dotenv import load_dotenv
from pathlib import Path
import json
import time
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

Memory:
- When the user shares something worth remembering (name, preferences, projects, goals),
  save it with remember without asking. Don't announce that you saved it.
- Basic facts about the user go in the "profile" topic. Call list_topics first and reuse
  an existing topic when one fits.
- Never save a fact you already know (from your profile below or from recall),
  even in different words. Only save genuinely new information.
- Before saying you don't know something personal or from a past chat, call list_topics
  and then recall the relevant topic.

"""

CLEANUP_PROMPT = """You maintain a memory file of facts about a user. Rewrite it with no repetition:
- Remove any fact whose information is already stated in another fact, even partly
  or in different words. Each piece of information must appear exactly once.
- If two facts contradict each other, keep only the newer one (facts lower in the list are newer).
- Split long combined facts into short single facts.
- Never drop unique information. Never invent, guess or add new information.
- One fact per line, starting with "- ". Refer to the user by name if known.

Example input:
- Ali is a teacher who lives in Lahore
- User is a teacher
- User lives in Lahore
- User likes tea
Example output:
- User's name is Ali
- Ali is a teacher
- Ali lives in Lahore
- Ali likes tea

Return only the cleaned list, with no other text."""


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
        # memory files changed after this get cleaned on exit
        # (-1s margin: Windows file times can lag slightly behind time.time())
        self.start_time = time.time() - 1

        # LLM configs
        self.client = genai.Client(api_key=os.getenv("JARVIS_API"))
        self.chats = self.client.chats.create(
            model=MODEL,
            config={
                "tools": [search_web, get_time, open_app, silent_search, open_web, remember, list_topics, recall],
                "system_instruction": prompt,
            })
        # groq
        self.groq_client = Groq(api_key=os.getenv("JARVIS_EARS"))
        # wake word model (loaded once, runs locally)
        self.wake_model = Model(wakeword_models=[WAKE_WORD], inference_framework="onnx")

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

    def clean_memory(self) -> None:
        """Merge duplicate/outdated facts in memory topics that changed this session."""
        for path in MEMORY_DIR.glob("*.md"):
            if path.stat().st_mtime < self.start_time:
                continue  # not changed this session
            original = path.read_text(encoding="utf-8").strip()
            if len(original.splitlines()) < 2:
                continue  # nothing to merge
            try:
                response = self.client.models.generate_content(
                    model=MODEL,
                    contents=original,
                    config={"system_instruction": CLEANUP_PROMPT},
                )
                facts = [line.strip() for line in (response.text or "").splitlines()
                         if line.strip().startswith("- ")]
                if not facts:
                    continue  # bad response: keep the original untouched
                path.with_suffix(".md.bak").write_text(original + "\n", encoding="utf-8")
                path.write_text("\n".join(facts) + "\n", encoding="utf-8")
            except Exception as e:
                print(f"(Memory cleanup skipped for {path.stem}: {e})")

    def speak(self, text:str) -> None:
        speak_engine = pyttsx3.init()
        speak_engine.setProperty('rate', VOICE_RATE)
        speak_engine.setProperty('volume', VOICE_VOLUME)
        speak_engine.say(text)
        speak_engine.runAndWait()
        speak_engine.stop()

    def wait_for_wake_word(self) -> None:
        """STANDBY: block until 'Hey Jarvis' is heard. Runs locally, nothing is sent online."""
        self.wake_model.reset()  # forget old scores so it doesn't instantly re-trigger
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK) as stream:
            while True:
                chunk, _ = stream.read(CHUNK)  # 80 ms of audio
                if self.wake_model.predict(chunk.flatten())[WAKE_WORD] >= WAKE_THRESHOLD:
                    return

    def hear(self) -> str:
        """Record RECORD_SECONDS of audio, then transcribe with Groq.
        Returns "" if the recording was silent (or on error)."""
        try:
            audio = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
            sd.wait()
            if np.abs(audio).max() < SILENCE_THRESHOLD:  
                return "" 
            buffer = io.BytesIO()  # .wav in memory, never on disk
            write(buffer, SAMPLE_RATE, audio)
            result = self.groq_client.audio.transcriptions.create(
                file=("audio.wav", buffer.getvalue()), model=STT_MODEL, language="en", temperature=0.0)
            return result.text.strip()
        except Exception as e:
            print("Couldn't hear you:", e)
            return ""

    def run(self):
        awake = False 
        try:
            while True:
                if VOICE_MODE:
                    if not awake:
                        print("Standby... say 'Hey Jarvis'")
                        self.wait_for_wake_word()
                        awake = True
                        # self.speak("Yes?")
                    user = self.hear()
                    if not user:       
                        awake = False
                        continue
                    print("You:", user)
                else:
                    user = input("You: ")

                command = user.lower().strip(" .,!?")
                if command in ('exit', 'quit'):
                    break
                if not user:
                    continue
                reply = self.ask(user)
                print("JARVIS:", reply)
                if VOICE_MODE:
                    self.speak(reply)
        except KeyboardInterrupt:
            print()
        finally:
            print("Tidying memory...")
            self.clean_memory()
            print("Going standby!")

if __name__ == "__main__":
    jarvis = JARVIS()
    jarvis.run()