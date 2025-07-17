import os
import fitz  # PyMuPDF
import numpy as np
import openai
import pickle
import time
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# ----- PDF TEXT EXTRACTION -----
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text("text") for page in doc)

# Set the OpenAI API key for authentication
openai.api_key = openai_api_key

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# ----- EMBEDDINGS -----
def create_embeddings_batch(text_list, model="text-embedding-ada-002"):
    response = openai.Embedding.create(model=model, input=text_list)
    return [item["embedding"] for item in response["data"]]

def cosine_similarity(vec1, vec2):
    v1, v2 = np.array(vec1), np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# ----- SEMANTIC SEARCH -----
def semantic_search(query, text_chunks, embeddings, k=5, threshold=0.7):
    query_emb = create_embeddings_batch([query])[0]
    scores = [(idx, cosine_similarity(query_emb, emb)) for idx, emb in enumerate(embeddings)]
    top_k = sorted(scores, key=lambda x: x[1], reverse=True)[:k]
    return [text_chunks[idx] for idx, score in top_k if score >= threshold]

# ----- KNOWLEDGE BASE -----
knowledge_base = {
    "How do I deal with anxiety?": "Try deep breathing or journaling to slow your thoughts.",
    "How do I overcome procrastination?": "Start with 5 minutes—momentum builds from small steps.",
    "What is the purpose of life?": "Purpose is personal—explore what brings you peace and energy."
}

def search_knowledge_base(query):
    for q, a in knowledge_base.items():
        if q.lower() in query.lower():
            return a
    return "I'm not sure I have the answer, but I can help you explore it."

# ----- EMOTIONAL CHECK -----
def is_problematic_query(message):
    keywords = [
        "depress", "anxious", "stress", "sad", "unhappy", "hopeless", 
        "lost", "angry", "empty", "tired", "overwhelmed", "fear", "lonely", 
        "burnout", "panic", "worthless", "pointless", "no purpose", "give up"
    ]
    return any(kw in message.lower() for kw in keywords)

def generate_effect_explanation(msg, prev_queries):
    msg = msg.lower()
    if "depressed" in msg or "not happy" in msg:
        return "Feeling depressed can be draining. You’re not alone—small steps can help ease the weight."
    elif "anxious" in msg:
        return "Anxiety often makes your mind race. Breathing deeply and grounding can calm that storm."
    elif "sad" in msg:
        return "Sadness is heavy but temporary. Talking helps—and you’re doing that already."
    if msg in ["hi", "hey", "hello", ""] or len(msg.strip()) < 5:
        if prev_queries and any(q.lower() in ["hi", "hey", "hello", ""] for q in prev_queries[-2:]):
            return "Hey, still keeping it light? I’m here if anything’s on your mind!"
        return "Just a quick hello? That’s cool. Let me know if you want to go deeper."
    return "Everyone’s path is different, but one step at a time makes a difference."

# ----- DAILY TASK -----
def generate_daily_task(user_message, prev_queries=None, model="gpt-4-turbo"):
    today = datetime.now().strftime("%B %d, %Y")
    prev_queries = prev_queries or []
    # Build conversation history for context
    history = "\n".join(f"User: {q}" for q in prev_queries[-5:])  # last 5 messages
    prompt = (
        f"You’re a caring, friendly wellness coach. Today is {today}.\n"
        f"Here is the recent conversation:\n{history}\n"
        f"Now, the user says: \"{user_message}\".\n"
        "Suggest one actionable, encouraging self-care task for today, based on the conversation. "
        "Keep it short, specific, and uplifting, like something you'd say to a friend."
    )
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You’re a warm, supportive coach suggesting daily self-improvement tasks."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# ----- QUOTES -----
emotion_quote_map = {
    "depression": "Even the darkest nights fade. Keep going—you’ve got this.",
    "anxiety": "Breathe. One moment at a time is enough.",
    "fatigue": "Rest isn’t quitting—it’s how you come back stronger.",
    "loss": "Lost doesn’t mean gone forever. You’ll find your path again.",
    "anger": "Peace comes from pause. You’re stronger than the storm.",
    "hopelessness": "Hope is quiet, but always present. Hold on.",
    "fear": "Fear fades when faced. Step forward bravely.",
    "stress": "You’re doing your best. Let that be enough today.",
    "emptiness": "You’re not empty. You’re healing and unfolding.",
    "neutral": "Every small step today plants seeds for growth tomorrow."
}

def precompute_label_embeddings():
    return {label: create_embeddings_batch([label])[0] for label in emotion_quote_map}

def get_dynamic_motivational_quote(user_message, label_embeddings):
    user_emb = create_embeddings_batch([user_message])[0]
    best_label, _ = max(label_embeddings.items(), key=lambda x: cosine_similarity(user_emb, x[1]))
    if cosine_similarity(user_emb, label_embeddings[best_label]) < 0.7:
        return emotion_quote_map["neutral"]
    return emotion_quote_map[best_label]

# ----- HANDLE VAGUE MESSAGES -----
def handle_vague_message(user_message, prev_queries, mode="coach"):
    second_time = len(prev_queries) >= 2 and all(
        q.lower().strip() in ["hi", "hey", "hello", ""] for q in prev_queries[-2:]
    )
    casual = [
        "Hey there! 😊 Just dropping in? What’s on your mind today?",
        "Hi hi! 🌟 You in the mood to chat or just passing by?",
        "Yo! 😄 Feeling chill today or got something on your mind?",
        "Welcome back! Let’s talk when you’re ready. 💬"
    ]
    reflective = [
        "You’ve kept it light a few times—anything bubbling under the surface?",
        "Keeping it short again? 😄 No pressure, but I’m here if you want to open up.",
        "Still no details? Totally fine—just know I’ve got your back whenever you're ready.",
        "Sometimes a ‘hello’ carries a lot—want to talk about anything specific?"
    ]
    chosen = random.choice(reflective if second_time else casual)
    return f"👋 {chosen}" if mode == "friend" else f"🧠 {chosen}"

# ----- MAIN RESPONSE -----
def generate_response(user_message, text_chunks, embeddings, label_embeddings, prev_queries, mode="coach"):
    # Check for greetings, farewells, and short polite messages
    simple_message_responses = {
        "greeting": [
            "hi", "hello", "hey", "hola", "bonjour", "ciao", "namaste", "wassup", "what's up", "howdy", "greetings", "peace", "shalom", "salaam",
            "hiya", "hello there", "hey there", "hi there", "yo", "yo!", "yo yo", "yo yo yo", "sup", "sup?", "hey?", "hi?", "hello?", "hey!", "hi!", "hello!"
        ],
        "farewell": [
            "bye", "goodbye", "see you", "see ya", "later", "catch you later", "take care", "farewell", "adios", "cheers", "peace out", "see you soon", "see you later",
            "bye!", "goodbye!", "bye?", "goodbye?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?",
            "ttyl", "talk to you later", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?", "see you?",
            "just wanted to say bye", "just wanted to say goodbye", "just wanted to say see you", "just wanted to say see you later", "just wanted to say see you soon",
            "just wanted to say take care", "just wanted to say farewell", "just wanted to say adios", "just wanted to say cheers", "just wanted to say peace out",
            "just wanted to say catch you later", "just wanted to say talk to you later", "just wanted to say ttyl"
        ],
        "thanks": [
            "thank you", "thanks", "thanks!", "thank you!", "appreciate it", "much appreciated", "gracias", "merci", "danke", "arigato", "obrigado", "ta", "cheerio",
            "just wanted to say thanks", "just wanted to say thank you"
        ],
        "polite": [
            "alright", "ok", "okay", "cool", "sure", "yep", "yup", "no problem", "np", "roger", "copy that", "affirmative",
            "sounds good", "sounds great", "sounds awesome", "awesome", "great", "nice", "sweet", "lovely", "brilliant", "fantastic",
            "wonderful", "super", "superb", "excellent", "perfect", "fine", "alrighty", "righto"
        ],
        "time": [
            "morning", "evening", "afternoon", "good night", "night", "gn", "good morning", "good afternoon", "good evening",
            "just checking in", "just saying hi", "just saying hello", "just wanted to check in", "just wanted to say goodnight",
            "just wanted to say good morning", "just wanted to say good afternoon", "just wanted to say good evening", "just wanted to say gn", "just wanted to say night", "just wanted to say good night"
        ]
    }

    user_msg = user_message.strip().lower()
    # Flatten all phrases for quick lookup
    all_simple_phrases = set(sum(simple_message_responses.values(), []))
    if user_msg in all_simple_phrases or len(user_msg) < 5:
        if any(phrase in user_msg for phrase in simple_message_responses["farewell"]):
            return random.choice([
                "Goodbye! Take care! 😊",
                "See you soon! Stay well! 👋",
                "Bye! Wishing you a great day!"
            ])
        elif any(phrase in user_msg for phrase in simple_message_responses["thanks"]):
            return random.choice([
                "You're welcome! 😊",
                "Happy to help!",
                "Anytime! Let me know if you need anything else."
            ])
        else:
            return random.choice([
                "Hello! How can I help you today?",
                "Hey there! 😊 What's on your mind?",
                "Hi! Ready to chat whenever you are."
            ])

    pdf_results = semantic_search(user_message, text_chunks, embeddings, k=3, threshold=0.7)
    today = datetime.now().strftime("%B %d, %Y")
    history = "\n".join(f"User: {q}" for q in prev_queries[-5:])
    semantic_context = "\n---\n".join(pdf_results) if pdf_results else ""
    mode_label = "Coach" if mode == "coach" else "Friend"
    prompt = (
        f"You are a highly empathetic, supportive, and practical chatbot. Today is {today}.\n"
        f"Here is the recent conversation (for context, do not repeat):\n{history}\n"
        f"Relevant supporting material from a book or resource (use only if helpful, do not copy verbatim):\n{semantic_context}\n"
        f"Now, the user says: \"{user_message}\".\n"
        f"Your task is to provide a response that is empathetic, specific, and actionable.\n"
        f"Blend your answer with insights from the supporting material if relevant, but always prioritize clarity and user understanding.\n"
        f"Avoid generic, vague, or repetitive statements.\n"
        f"Do not copy large blocks of text from the context.\n"
        f"If you provide a motivational quote, practical suggestion, daily task, or follow-up question, use the following format for {mode_label} mode:\n"
        f"If Coach mode, use this format:\n"
        f"**[Coach Mode] Your Plan:**\n\n1. **What’s going on:** <summary/explanation>\n\n2. **Try this:** <practical suggestion>\n\n3. **Motivation:** \"<motivational quote>\"\n\n4. **Today’s Task:** <short daily task>\n"
        f"If Friend mode, use this format:\n"
        f"💬 Here's what I’ve got for you:\n- **Feels like:** <summary/explanation>\n- **You could try:** <practical suggestion>\n- **Here’s a thought:** \"<motivational quote>\"\n- **Wanna try this today?** <short daily task>\n"
        f"You may skip any section if it is not relevant, and you may reply with just a supportive message if that's most appropriate.\n"
        f"Use your judgment to decide what is most helpful and natural for the user's message, always feel the emotion.\n"
        f"Make your response a bit more detailed and thoughtful, offering extra context, encouragement, or explanation as appropriate."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a friendly, supportive chatbot."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    ).choices[0].message.content.strip()
    return response

# ----- MAIN DRIVER -----
if __name__ == "__main__":
    start_time = time.time()
    pdf_path = r"C:\Users\belal\OneDrive\Desktop\G-Flex-Project\chat\The_Apple_and_The_Stone (10) (1) (2).pdf"
    cache_path = "pdf_embeddings.pkl"

    print("[1] Extracting PDF text...")
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)

    print("[2] Loading or computing PDF embeddings...")
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            embeddings = pickle.load(f)
    else:
        embeddings = create_embeddings_batch(chunks)
        with open(cache_path, "wb") as f:
            pickle.dump(embeddings, f)

    print("[3] Precomputing emotion label embeddings...")
    label_embeddings = precompute_label_embeddings()

    prev_queries = []
    print("\nWelcome to your friendly chatbot! 😊")
    # Mode selection at the start
    mode = None
    while mode not in ["coach", "friend"]:
        print("Choose your mode:")
        print("  1. Coach Mode (supportive, structured guidance)")
        print("  2. Friend Mode (casual, friendly chat)")
        mode_input = input("Enter 1 for Coach or 2 for Friend: ").strip()
        if mode_input == "1":
            mode = "coach"
        elif mode_input == "2":
            mode = "friend"
        else:
            print("Invalid input. Please enter 1 or 2.")

    print(f"\nYou are now chatting in {'Coach' if mode == 'coach' else 'Friend'} Mode! Type your message (or 'exit' to quit).")

    while True:
        query = input("\nYour message: ").strip()
        if query.lower() == "exit":
            print("Thanks for chatting! Take care! 😄")
            break

        prev_queries.append(query)

        print("\n--- Response ---")
        print(generate_response(query, chunks, embeddings, label_embeddings, prev_queries, mode=mode))

    print(f"\n✅ Done in {round(time.time() - start_time, 2)} seconds.")