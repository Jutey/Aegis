import openai
import random
import os
from dotenv import load_dotenv
from memory import recall, remember

# Load API keys
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def get_ai_response(user_input):
    memory = recall(user_input)  # Check previous interactions

    witty_responses = [
        'Oh, you again? What do you need this time?',
        'Let me think... Nope, still smarter than you! Just kidding. Here\'s your answer:',
        'Do I look like Google? Oh wait, I kinda am. Anyway, here\'s what I found:',
    ]
    
    prompt = f"
    You are a witty AI assistant with memory. Respond with humor and personality.
    User: {user_input}
    {f'Previous context: {memory}' if memory else ''}
    AI:
    "

    response = openai.ChatCompletion.create(
        model='gpt-4-turbo',
        messages=[{'role': 'system', 'content': 'You are a smart assistant with a sharp wit.'},
                  {'role': 'user', 'content': prompt}]
    )

    reply = response['choices'][0]['message']['content']
    final_response = random.choice(witty_responses) + ' ' + reply
    
    remember(user_input, reply)
    return final_response
