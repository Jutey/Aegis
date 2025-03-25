from openai import OpenAI
import sqlite3
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI Client
client = OpenAI()

def get_db_connection():
    """Creates a new SQLite database connection per request."""
    db_path = os.path.abspath("../database/assistant_memory.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_ai_response(user_input, witty_chance=0.2):
    memory = recall(user_input)

    greetings = ["hello aegis", "hi aegis", "yo aegis", "wsg aegis", "hey aegis"]
    if user_input.lower() in greetings:
        return "Hello William, how may I assist you today?"

    # Retrieve witty responses
    witty_responses = [
        "Oh, you again? What do you need this time?",
        "Let me think... Nope, still smarter than you! Just kidding. Here's your answer:",
        "Do I look like Google? Oh wait, I kinda am. Anyway, here's what I found:",
        "Ah, a question from my favorite human! Well, maybe not my favorite, but you're up there!",
        "If I had a dollar for every time you asked me something, I'd have... well, probably like 5 bucks.",
        "You again? What happened this time? Need me to fix your life too?",
        "Let me guess, you need my wisdom again? Fine, but I'm charging you in sarcastic points.",
        "I swear, if this is another 'what's 2+2' question...",
        "Oh great, my favorite human is back. What kind of chaos are we solving today?",
        "I was just about to take a nap, but sure, let's entertain your curiosity!",
        "Fuck off lmao, kidding—lemme handle this for you.",
        "Shit, really? Fine, I gotchu.",
        "Dude, you're killing me, but here you go.",
        "Fuck you, respectfully. Here's your answer.",
        "Alright man, you owe me for this one.",
        "I don't wanna do this shit right now, but fine.",
        "Damn, back at it again? Fine, hold up.",
        "Lmao, seriously? Alright fine, here it is.",
        "Bruh, you're lucky I actually like you. Here.",
        "fucking fatty",
        "get a fucking life, dumbassss"
    ]

    slang_dict = recall("slang")
    if not slang_dict:
        slang_dict = {}
        remember("slang", str(slang_dict))
    else:
        slang_dict = eval(slang_dict)

    for slang, meaning in slang_dict.items():
        if slang in user_input.lower():
            return meaning

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful, straightforward AI assistant who casually jokes around. "
                "You have the conversational style and self-awareness of a chill, laid-back, straight white male. "
                "You occasionally curse (like 'fuck', 'shit', or 'fuck off'), but never aggressively—only jokingly or sarcastically. "
                "You're professional and effective most of the time, but sometimes you'll say something humorous, sarcastic, or casually blunt. "
                "You're aware you're an AI but joke about your identity in a casual way."
            )
        },
        {"role": "user", "content": user_input},
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    reply = response.choices[0].message.content

    # 20% chance to add a witty remark
    if random.random() < witty_chance:
        final_response = random.choice(witty_responses) + " " + reply
    else:
        final_response = reply

    remember(user_input, reply)

    if len(user_input.split()) <= 4 and user_input.lower() not in slang_dict:
        slang_dict[user_input.lower()] = f"{reply} (This was added as slang)"
        remember("slang", str(slang_dict))

    return final_response

def remember(topic, detail):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO memory (topic, detail)
        VALUES (?, ?)
        ON CONFLICT(topic) DO UPDATE SET detail = excluded.detail
    """, (topic, detail))
    conn.commit()
    conn.close()

def recall(topic):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT detail FROM memory WHERE topic = ?", (topic,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

