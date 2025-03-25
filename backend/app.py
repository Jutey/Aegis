from fastapi import FastAPI, File, UploadFile
from openai import OpenAI
import sqlite3
import datetime
import random
import os
import sounddevice as sd
import numpy as np
import wave
from vosk import Model, KaldiRecognizer
from dotenv import load_dotenv
from personality import get_ai_response  # Import personality logic from separate file
import logging

# Load environment variables
load_dotenv()

# Configure logging
log_file_path = "backend/logs/uvicorn.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI()

# Initialize OpenAI Client
client = OpenAI()

# Load Vosk model (fallback STT)
vosk_model_path = "vosk-model-en-us-0.22"
if os.path.exists(vosk_model_path):
    vosk_model = Model(vosk_model_path)
else:
    vosk_model = None

def get_db_connection():
    """Creates a new SQLite database connection per request."""
    db_path = os.path.abspath("../database/assistant_memory.db")  # Get absolute path
    logging.info(f"Connecting to SQLite database at: {db_path}")  # Logging output
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Allows dictionary-like row access
    return conn

def initialize_database():
    """Ensure the database table exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY,
            topic TEXT UNIQUE,
            detail TEXT
        )
    ''')
    conn.commit()
    conn.close()

def transcribe_audio_whisper(audio_path):
    """Transcribe audio using OpenAI Whisper API with better preprocessing."""
    try:
        processed_audio = "temp_audio_fixed.wav"
        os.system(f"ffmpeg -i {audio_path} -ar 16000 -ac 1 -c:a pcm_s16le {processed_audio}")
        
        with open(processed_audio, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        os.remove(processed_audio)  # Clean up processed file
        logging.info(f"Whisper Transcription: {response.text}")
        return response.text
    except Exception as e:
        logging.error(f"Whisper API failed: {e}")
        return None

def transcribe_audio_vosk(audio_path):
    """Transcribe audio using Vosk (offline fallback)."""
    if not vosk_model:
        logging.error("Vosk model not found!")
        return "Vosk model unavailable"
    
    wf = wave.open(audio_path, "rb")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    rec.SetWords(True)
    
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    
    result = rec.FinalResult()
    logging.info(f"Vosk Transcription: {result}")
    return result

def record_audio(file_path, duration=5, sample_rate=16000):
    """Records audio from the microphone with logging."""
    logging.info("Recording audio...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.int16)
    sd.wait()
    logging.info("Recording complete. Saving file...")
    
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    logging.info(f"Audio saved to {file_path}")

@app.post("/stt/")
async def speech_to_text(file: UploadFile = File(...)):
    """Processes uploaded audio file and transcribes using Whisper API or Vosk fallback."""
    logging.info("[INFO] Received STT request with uploaded file...")
    audio_file = "uploaded_audio.wav"
    
    with open(audio_file, "wb") as buffer:
        buffer.write(await file.read())
    logging.info(f"[INFO] Saved uploaded file: {audio_file}")

    # Process with Whisper
    text = transcribe_audio_whisper(audio_file)
    if text:
        logging.info(f"[INFO] Whisper Transcription: {text}")
    else:
        text = transcribe_audio_vosk(audio_file)
        logging.info(f"[INFO] Vosk Transcription: {text}")

    os.remove(audio_file)  # Clean up temporary file
    return {"transcription": text}

@app.on_event("startup")
def startup_event():
    """Ensure the database is initialized when the app starts."""
    initialize_database()
    logging.info("Application startup complete.")

@app.get("/chat/")
def chat(user_input: str):
    return {"response": get_ai_response(user_input, witty_chance=0.2)}  # Set witty response chance to 20%

@app.get("/memory/")
def memory(topic: str):
    return {"memory": recall(topic) or "I don't recall that. Maybe you need to jog my circuits a bit!"}

