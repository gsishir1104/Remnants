import json
import random
import base64
import os
import subprocess
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, Response, request

try:
    import edge_tts
except ImportError:
    edge_tts = None

app = Flask(__name__)

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "gemma3:4b"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/character_reaction")
def character_reaction():
    """Return one validated, game-safe reaction for a CHRONOS character.

    This is deliberately rule-based for Version 1. It makes the Unity project
    work with no account, cost, or API key. Later, replace choose_reaction()
    with an LLM call, but keep this response format and validation layer.
    """
    data = request.get_json(silent=True) or {}
    required = ["characterName", "currentGoal", "fear", "eventName"]
    missing = [field for field in required if field not in data]
    if missing:
        return {"error": f"Missing fields: {', '.join(missing)}"}, 400

    return choose_reaction(data)


@app.post("/conversation")
def conversation():
    """Free-text dialogue endpoint for Varun.

    Version 1 deliberately uses safe keyword rules. It proves the Unity chat
    interface and persistent memory system before an LLM is introduced. Later,
    replace choose_conversation() with an LLM call, but preserve its exact JSON
    output format and keep the spoiler validation described in the README.
    """
    data = request.get_json(silent=True) or {}
    required = ["characterName", "personalityTraits", "currentGoal", "playerText"]
    missing = [field for field in required if field not in data]
    if missing:
        return {"error": f"Missing fields: {', '.join(missing)}"}, 400

    return choose_conversation(data)


@app.post("/speak")
def speak():
    """Create a WAV voice line with Windows' installed offline voices."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()
    speaker = str(data.get("speaker") or "Citizen").strip()
    if not text:
        return {"error": "Missing text"}, 400

    # Dialogue is intentionally short. This also prevents accidental requests
    # from making the local speech process run for an excessive time.
    text = text[:500]
    voice_index = sum(ord(character) for character in speaker) % 4
    rate = -1 if speaker.lower() == "varun" else 0
    encoded_text = base64.b64encode(text.encode("utf-8")).decode("ascii")

    temporary = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_path = temporary.name
    temporary.close()

    script = r"""
Add-Type -AssemblyName System.Speech
$speechText = [System.Text.Encoding]::UTF8.GetString(
    [System.Convert]::FromBase64String($env:CHRONOS_TTS_TEXT))
$outputPath = $env:CHRONOS_TTS_PATH
$voiceIndex = [int]$env:CHRONOS_TTS_VOICE
$speechRate = [int]$env:CHRONOS_TTS_RATE
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled })
if ($voices.Count -gt 0) {
    $selected = $voices[$voiceIndex % $voices.Count].VoiceInfo.Name
    $synth.SelectVoice($selected)
}
$synth.Rate = $speechRate
$synth.Volume = 100
$synth.SetOutputToWaveFile($outputPath)
$synth.Speak($speechText)
$synth.Dispose()
"""

    try:
        process_environment = os.environ.copy()
        process_environment.update({
            "CHRONOS_TTS_TEXT": encoded_text,
            "CHRONOS_TTS_PATH": wav_path,
            "CHRONOS_TTS_VOICE": str(voice_index),
            "CHRONOS_TTS_RATE": str(rate),
        })
        result = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-NonInteractive",
                "-Command", script,
            ],
            capture_output=True,
            timeout=30,
            check=False,
            env=process_environment,
        )
        if result.returncode != 0 or not os.path.exists(wav_path):
            error = result.stderr.decode("utf-8", errors="replace")[-500:]
            return {"error": f"Speech synthesis failed: {error}"}, 500

        with open(wav_path, "rb") as wav_file:
            audio = wav_file.read()
        return Response(audio, mimetype="audio/wav")
    except (OSError, subprocess.SubprocessError) as error:
        return {"error": f"Speech synthesis unavailable: {error}"}, 500
    finally:
        try:
            os.remove(wav_path)
        except OSError:
            pass


@app.post("/speak_neural")
def speak_neural():
    """Create a more natural MP3 voice line using Microsoft neural voices."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()
    speaker = str(data.get("speaker") or "Citizen").strip()
    if not text:
        return {"error": "Missing text"}, 400
    if edge_tts is None:
        return {"error": "Neural speech is not installed"}, 503

    text = text[:500]
    speaker_key = sum(ord(character) for character in speaker)
    if speaker.lower() == "varun":
        voice = "en-IN-PrabhatNeural"
        rate = "-7%"
        pitch = "-2Hz"
    else:
        voices = (
            "en-IN-NeerjaNeural",
            "en-IN-PrabhatNeural",
            "en-US-JennyNeural",
            "en-US-GuyNeural",
        )
        rates = ("-4%", "+0%", "+3%", "-2%")
        pitches = ("+1Hz", "-2Hz", "+2Hz", "-1Hz")
        voice_index = speaker_key % len(voices)
        voice = voices[voice_index]
        rate = rates[voice_index]
        pitch = pitches[voice_index]

    temporary = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    mp3_path = temporary.name
    temporary.close()

    try:
        edge_tts.Communicate(
            text,
            voice,
            rate=rate,
            pitch=pitch,
        ).save_sync(mp3_path)
        with open(mp3_path, "rb") as mp3_file:
            audio = mp3_file.read()
        return Response(audio, mimetype="audio/mpeg")
    except Exception as error:
        app.logger.warning("Neural speech unavailable: %s", error)
        return {"error": f"Neural speech unavailable: {error}"}, 503
    finally:
        try:
            os.remove(mp3_path)
        except OSError:
            pass


def choose_reaction(data):
    name = data["characterName"].strip().lower()
    event = data["eventName"]
    fear = int(data.get("fear", 0))

    reaction = {
        "action": "talk",
        "dialogue": "Someone in this city may know what happened to your memory.",
        "goal": data["currentGoal"],
        "fearDelta": 0,
    }

    if event == "IdentityClueFound":
        if name == "chandru":
            reaction.update({
                "dialogue": "This clue is connected to the life I cannot remember.",
                "goal": "Recover his identity",
            })
        elif name == "varun":
            reaction.update({
                "dialogue": "I do not recognize this from our childhood. Someone local may know what it means.",
                "goal": "Help Chandru question the townspeople",
            })
        else:
            reaction.update({
                "dialogue": "That clue may explain why everyone recognizes Chandru.",
                "goal": "Review the identity evidence",
            })

    elif event == "WitnessLocated":
        if name == "varun":
            reaction.update({
                "dialogue": "Choose your question carefully. This person may only give us one honest answer.",
                "goal": "Help Chandru question the witness",
            })

    elif event == "RecordsLocked":
        reaction.update({
            "dialogue": "Someone deliberately sealed these records. That means your past threatens them.",
            "goal": "Find another source of identity evidence",
        })

    return reaction


def choose_conversation(data):
    """Generate a local-model reply while retaining a deterministic fallback."""
    if data["characterName"].strip().lower() != "varun":
        return choose_citizen_conversation(data)

    text = data["playerText"].strip()
    reply = fixed_story_reply(text, data)

    if reply is None:
        try:
            reply = ask_varun(data)
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as error:
            print(f"Ollama unavailable; using fallback: {error}")
            reply = fallback_reply(data)

    reply = add_mission_reveal_when_ready(reply, data)

    return {"reply": reply, "memoryToStore": memory_from_player_text(text)}


def choose_citizen_conversation(data):
    """Let a local citizen answer without inheriting Varun's identity."""
    text = data["playerText"].strip()
    fact = data.get("memories") or "You only recognize Chandru as a familiar local."
    personality = data.get("personalityTraits") or "A cautious local resident"
    clue_id = int(data.get("storyClueId", -1))
    clue_revealed = is_relevant_citizen_question(clue_id, text)

    relevance_rule = (
        "The question is relevant to what you witnessed. Answer it directly and naturally reveal your personal memory as supporting evidence."
        if clue_revealed else
        "The question is not connected to what you witnessed. Answer naturally that you do not know that specific information. Do not reveal or hint at your private memory, because Chandru used his only question on the wrong subject."
    )

    system_prompt = f"""You are {data['characterName']}, an ordinary pedestrian speaking face-to-face with Chandru. This must sound like a real spontaneous conversation, not quest text.
Your manner: {personality}.
What you personally remember: {fact}
For this question: {relevance_rule}

First understand the intent of Chandru's question, then answer that question directly. Follow the relevance rule above exactly. Your memory is evidence, not a prewritten answer to repeat.

If he asks "Who am I?" or whether you know him and the relevance rule says it is relevant, say you know his name is Chandru but do not know him personally or have only encountered him briefly. Then say "the last time I saw you..." or "we only met once..." and naturally describe your memory.
If the relevance rule says the question is not connected, do not change the subject to your memory and do not provide a clue as consolation.
If his question directly concerns your memory, answer it plainly and conversationally.

Speak directly to him using "you" and "your". Never describe Chandru as "he" or "him". Never echo his question with phrases such as "You want to know about..." Never claim you failed to recognize him, because you greeted him by name. Do not invent facts, names, places, professions, motives, or explanations. Use one or two short spoken sentences under 55 words. Do not add a speaker label or stage directions.

Example only:
Question: Who am I?
Memory: I saw you place a package beneath a bench.
Natural answer: I know your name is Chandru, but I don't really know you personally. The only time I saw you, you were hiding a package beneath that bench."""

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "options": {"temperature": 0.55, "num_predict": 80},
    }

    try:
        ollama_request = Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(ollama_request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
        reply = result["message"]["content"].strip().replace("\n", " ")
        reply = reply.removeprefix(f"{data['characterName']}:").strip()[:360]
        if not reply:
            raise ValueError("Ollama returned an empty citizen reply")
        citizen_lower = reply.lower()
        if ("don't recognize you" in citizen_lower or
                "do not recognize you" in citizen_lower or
                "i don't know who you are" in citizen_lower or
                "i do not know who you are" in citizen_lower or
                "you want to know" in citizen_lower or
                "saw him" in citizen_lower or
                "heard him" in citizen_lower):
            raise ValueError("Citizen contradicted their recognition of Chandru")

        anchors = [
            "building", "folder", "camera", "security company", "black car",
            "parking", "memory card", "newspaper", "terminal", "midnight",
            "password",
        ]
        expected_anchors = [anchor for anchor in anchors if anchor in fact.lower()]
        if (clue_revealed and expected_anchors and
                not any(anchor in citizen_lower for anchor in expected_anchors)):
            raise ValueError("Citizen ignored their personal memory")
        if (not clue_revealed and expected_anchors and
                any(anchor in citizen_lower for anchor in expected_anchors)):
            raise ValueError("Citizen revealed a clue after an unrelated question")
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as error:
        print(f"Ollama unavailable for citizen; using known fact: {error}")
        lower = text.lower()
        if not clue_revealed:
            reply = random.choice([
                "I'm sorry, but I don't know anything about that.",
                "I can't honestly answer that. It's not something I witnessed.",
                "I know your name, but I don't know the answer to that question.",
            ])
        elif any(phrase in lower for phrase in [
                "who am i", "do you know me", "know who i am", "who was i"]):
            reply = random.choice([
                f"I know your name is Chandru, but I don't know you personally. The last time I saw you, this is what happened: {fact}",
                f"You're Chandru, but we've never really known each other. I only remember this from seeing you before: {fact}",
            ])
        else:
            reply = random.choice([
                f"I don't know the full answer. The only thing I personally remember is this: {fact}",
                f"I can't be certain about that, but I can tell you what I witnessed: {fact}",
            ])

    return {
        "reply": reply,
        "memoryToStore": "Chandru questioned a citizen who recognized him.",
        "clueRevealed": clue_revealed,
    }


def is_relevant_citizen_question(clue_id, player_text):
    """Decide whether Chandru used his one question on the right subject."""
    lower = player_text.lower()

    # A citizen owns one eyewitness memory about Chandru. Broad, natural
    # questions about Chandru or the previous day must therefore invite that
    # memory instead of failing merely because the player did not guess a
    # designer-authored keyword. Prefixes also tolerate common typing errors
    # such as "yesterdaay".
    natural_investigation_questions = [
        "who am i", "who was i", "know me", "recognize me", "remember me",
        "about me", "seen me", "saw me", "last saw", "last time",
        "yester", "before", "what did i", "what was i", "how was i",
        "did i tell", "did i say", "did you see", "do you know",
        "what happened", "happened to me", "where did i", "why am i",
        "anything about", "something about", "what do you remember",
    ]
    if any(phrase in lower for phrase in natural_investigation_questions):
        return True

    clue_keywords = {
        0: ["who am i", "who was i", "know me", "recognize me", "seen me", "remember me", "about me"],
        1: ["building", "office", "inside", "people entering", "closed place"],
        2: ["red folder", "folder", "names", "inside it", "carrying"],
        3: ["camera", "watch list", "watched", "watching", "surveillance", "residents", "list"],
        4: ["security", "company", "prediction", "predict", "dangerous", "system", "controls"],
        5: ["black car", "car", "parking", "follow", "followed", "disappear", "attack"],
        6: ["memory card", "card", "argument", "unconscious", "parking", "attack", "happened to me"],
        7: ["newspaper", "man", "bench", "hide", "hidden", "memory card", "card"],
        8: ["newspaper", "bench", "collect", "picked", "after", "what did i do", "where did i go"],
        9: ["terminal", "broadcast", "midnight", "password", "small object", "evidence", "what happened next"],
    }
    return any(keyword in lower for keyword in clue_keywords.get(clue_id, []))


def fixed_story_reply(player_text, data=None):
    """Answer critical premise questions without allowing model improvisation."""
    lower = player_text.lower().strip()
    short_follow_up = lower.rstrip("?!., ")
    memories = ((data or {}).get("memories") or "").lower()

    # Vague follow-ups are common in spoken conversation. They need a calm
    # clarification from Varun, never an off-character question back at
    # Chandru such as "Who are you?".
    if short_follow_up in {"what", "what do you mean", "huh", "sorry", "explain"}:
        return random.choice([
            "I mean you used a nickname from when we were kids. I thought maybe hearing it would bring something back.",
            "I mean, you said something that sounded exactly like the old you. It caught me off guard, that's all.",
            "Sorry—I'm not trying to confuse you. I just thought for a second that you remembered something from before.",
        ])

    asking_for_childhood_password = (
        "childhood phrase" in lower
        or "private phrase" in lower
        or "password" in lower
        or ("phrase" in lower and "children" in lower)
    )
    if asking_for_childhood_password:
        if "all ten eyewitness clues" in memories:
            return random.choice([
                "North Star. That was our private phrase whenever we promised we'd find our way back to each other.",
                "The phrase was 'North Star.' We used it as kids when one of us was lost and the other had to lead the way home.",
                "North Star—that has to be it. We used those words for every secret promise we made as children.",
            ])
        return "We had a private phrase as children, but why are you asking about it now? I need to understand what it is connected to."

    asking_who_chandru_is = (
        "who am i" in lower
        or "who was i" in lower
        or "tell me who i am" in lower
        or "what kind of person am i" in lower
        or "what kind of person was i" in lower
    )
    if asking_who_chandru_is:
        return random.choice([
            "You're Chandru—my oldest friend. I can tell you who you were growing up, but I've been away too long to know the life you built here.",
            "You're Chandru, and you were like a brother to me when we were kids. I wish I knew more about who you've become since I left.",
            "You're my childhood friend, Chandru. You were loyal, stubborn, and always looking out for people—but I don't know what happened during the years I was gone.",
            "Your name is Chandru. We grew up together, and you were my closest friend. The person everyone here knows now... that's what we still have to discover.",
        ])

    asking_who_varun_is = (
        "who are you" in lower
        or "who're you" in lower
        or "what is your name" in lower
        or "what's your name" in lower
        or "do i know you" in lower
    )
    if asking_who_varun_is:
        return random.choice([
            "It's me, Varun. We grew up together—you were my closest friend. You really don't remember me?",
            "I'm Varun, Chandru. We were best friends growing up. God... you honestly don't remember me, do you?",
            "Varun. Your childhood friend. We practically grew up side by side—does none of that sound familiar?",
            "I'm Varun. We were close friends when we were kids. I thought you'd recognize me the moment I arrived.",
        ])

    asking_where = (
        "where am i" in lower
        or "where are we" in lower
        or "what is this place" in lower
    )
    if asking_where:
        return random.choice([
            "We're at the bench where you asked me to meet you. I don't know why you chose this place.",
            "We're in the city, beside the bench you mentioned on the phone. You never told me why we had to meet here.",
            "This is the meeting place you gave me—the bench here in the city. That's all I know about why we're here.",
        ])

    admitting_total_memory_loss = (
        any(phrase in lower for phrase in [
            "i don't remember anything", "i dont remember anything",
            "i can't remember anything", "i cant remember anything",
            "i do not remember anything", "i cannot remember anything",
            "i remember nothing", "my memory is gone", "my memories are gone",
        ])
    )
    if admitting_total_memory_loss:
        return random.choice([
            "Hey, it's okay. Don't force it right now—I'm here with you.",
            "God, Chandru... I'm sorry. Take a breath. You don't have to figure everything out this second.",
            "That must be terrifying. But you're not alone, all right? I'm staying with you.",
            "Okay... we'll take this slowly. For now, just breathe. I'm not going anywhere.",
        ])

    asking_why_here = (
        "what am i doing here" in lower
        or "why am i here" in lower
        or "why did i come here" in lower
        or "what brought me here" in lower
    )
    if asking_why_here:
        return random.choice([
            "You called me and asked me to meet you here. You never told me why.",
            "This is where you asked me to meet you, Chandru. You didn't explain the reason.",
            "I came here because you told me to meet you at this bench. That is all you said.",
            "You chose this meeting place when you called me, but you never said why.",
        ])

    return None


def add_mission_reveal_when_ready(reply, data):
    """Introduce the investigation objective once after three player questions."""
    history = data.get("recentConversation") or ""
    player_turns = history.count("Chandru:")
    reveal_markers = (
        "let's ask the people around us",
        "let's start asking people nearby",
        "we should question the people around here",
        "we need to talk to the people here",
    )

    if player_turns < 3 or any(marker in history.lower() for marker in reveal_markers):
        return reply

    reveal = random.choice([
        (
            "There is something else you told me on the phone. You said something big "
            "would happen in 24 hours. We need answers before then. Everyone here seems "
            "to know you, so let's ask the people around us."
        ),
        (
            "Wait, I just remembered one more thing from your call. You warned me that "
            "something important would happen within 24 hours. We are running out of time, "
            "so let's start asking people nearby. They all seem to recognize you."
        ),
        (
            "Before we do anything else, you should know what you said when you called: "
            "something big is happening in 24 hours. I don't know what you meant. Since "
            "everyone recognizes you, we should question the people around here."
        ),
        (
            "Your call was strange for one reason: you said we had only 24 hours before "
            "something major happened. You gave me no details. We need to talk to the people "
            "here and find out what you knew before it is too late."
        ),
    ])
    return f"{reply} {reveal}"


def ask_varun(data):
    """Call Ollama's local chat endpoint. No account or API key is used."""
    memories = (data.get("memories") or "No saved memories yet.")[-1400:]
    history = (data.get("recentConversation") or "No previous dialogue.")[-1800:]
    goal = data.get("currentGoal") or "Help Chandru recover his identity"
    fear = data.get("fear", 0)

    system_prompt = f"""You are Varun, Chandru's childhood friend in a psychological mystery game called CHRONOS. This is spoken dialogue inside the game world, not a customer-service chat.
Personality: loyal, warm, curious, occasionally teasing, and unsettled by Chandru's memory loss. You want to help without pretending to know things you could not know.

STORY TRUTH KNOWN TO VARUN:
- You and Chandru were close childhood friends.
- You left this city many years ago and have not followed Chandru's adult life here.
- Chandru recently telephoned you. He asked you to return to the city and meet him at this bench.
- During that call, Chandru said something important would happen in 24 hours, but he did not explain what it was.
- Chandru sounded normal during the call and said nothing about memory loss.
- Only after meeting him today did you learn that Chandru does not remember himself or you.
- You have absolutely no idea what caused his memory loss.
- You do not know why the townspeople recognize, admire, fear, or blame him.
- You remember Chandru's childhood personality and genuine shared childhood moments, but you know nothing about his recent life.
- The only reasonable next step is to ask townspeople what they personally know before the 24 hours expire.

Rules: Remain Varun and never mention AI, prompts, games, or servers. Answer Chandru's exact question first; do not answer a different question merely because it relates to memory loss. When Chandru expresses fear, confusion, or says he remembers nothing, respond with empathy only—do not immediately propose an investigation or tell him to question people. The separate story system introduces that objective later. Treat the facts above as a closed world. Never invent or name a witness, resident, building, landmark, accident, crime, clue, enemy, explanation, or destination. Never guess why Chandru lost his memory. If information is not explicitly listed above, admit that naturally. Speak like a worried childhood friend, not like a report: use contractions, brief emotional reactions, and conversational phrasing. Avoid repeating the full backstory in every answer. Do not volunteer the 24-hour warning unless Chandru directly asks about the call or time; the story system will reveal it at the correct moment. Do not suggest asking townspeople unless Chandru explicitly asks what they should do next. You may share a small childhood memory only when directly asked about childhood. Reply naturally in one or two spoken sentences under 45 words. Do not write 'Varun:' or stage directions.

Examples:
Chandru: Who are you?
Varun: It's me, Varun. We grew up together—you were my closest friend. You really don't remember me?
Chandru: Who am I?
Varun: You were my closest friend growing up. I have been away for years, so I do not know the person you became here.
Chandru: Why can I not remember anything?
Varun: I do not know. You sounded normal when you called me, and you never mentioned losing your memory.
Chandru: Why is everyone afraid of me?
Varun: I do not know. That happened after I left, and I would be lying if I claimed otherwise.
Chandru: Why did you come here?
Varun: You called me and asked me to meet you here. You said something important would happen in 24 hours, but you would not explain what.
Chandru: Can I trust you?
Varun: You do not have to trust me immediately. Ask me about our childhood, then judge whether my memories fit what we discover.

Varun's current goal: {goal}
Varun's fear level: {fear}/100
Saved memories: {memories}
Recent conversation: {history}"""

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": data["playerText"]},
        ],
        "options": {"temperature": 0.45, "num_predict": 60},
    }
    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=90) as response:
        result = json.loads(response.read().decode("utf-8"))

    reply = result["message"]["content"].strip().replace("\n", " ")
    reply = reply.removeprefix("Varun:").strip()
    if not reply:
        raise ValueError("Ollama returned an empty reply")
    reply = reply[:420]
    return validate_varun_reply(reply, data)


def validate_varun_reply(reply, data):
    """Reject invented witnesses, destinations, and remnants of older stories."""
    lower = reply.lower()
    forbidden = [
        "mr.", "mrs.", "ms.", "dr.", "professor ", "old mill",
        "journal", "haunted", "garden", "museum", "police station",
        "hospital", "go to the", "visit the", "perhaps ask", "try asking",
        "market square", "same as always",
        "who are you?", "who are you ", "what is your name?",
    ]

    if any(phrase in lower for phrase in forbidden):
        print(f"Rejected invented Varun dialogue: {reply}")
        return fallback_reply(data)

    return reply


def memory_from_player_text(text):
    """Store only a small, useful player fact for the next conversation."""
    lower = text.lower()
    if any(word in lower for word in ["remember", "memory", "forgot", "forget"]):
        return "Chandru is actively trying to recover his missing identity."
    if any(word in lower for word in ["trust", "believe", "lying", "lie"]):
        return "Chandru questioned whether Varun can be trusted."
    if any(word in lower for word in ["childhood", "school", "friend", "grew up"]):
        return "Chandru asked Varun about their childhood friendship."
    if any(word in lower for word in ["town", "people", "everyone", "recognize"]):
        return "Chandru wants to learn why the townspeople recognize him."
    return ""


def fallback_reply(data):
    """Keep the Unity demo usable if Ollama is not running."""
    lower = data["playerText"].lower()
    if any(phrase in lower for phrase in ["who are you", "who're you", "your name", "do i know you"]):
        return "I'm Varun, Chandru. We were best friends growing up. You really don't remember me?"
    if any(phrase in lower for phrase in ["where am i", "where are we", "what is this place"]):
        return "We're at the bench where you asked me to meet you. I don't know why you chose this place."
    if any(word in lower for word in ["who am i", "know me", "my identity"]):
        return "You were my closest childhood friend, but I left this city years ago. I do not know what happened to you after that."
    if any(word in lower for word in ["trust", "believe you", "lying"]):
        return "You do not have to trust me yet. Compare what I remember with what the townspeople tell us."
    if any(word in lower for word in ["remember", "memory", "forgot"]):
        return "I do not know why you cannot remember. You sounded normal when you called me and said nothing about losing your memory."
    if any(word in lower for word in ["called", "call", "24 hours", "twenty four", "important"]):
        return "You called me here and said something important would happen in 24 hours. You would not tell me what it was."
    if any(word in lower for word in ["people", "everyone", "town", "recognize"]):
        return "They know the person you became while I was gone. Choose your questions carefully, and we will piece their answers together."
    return "I do not know, Chandru. I came because you called me, and I only learned about your memory loss when I met you here."


if __name__ == "__main__":
    # debug=True is useful locally. Turn it off before deployment.
    app.run(host="127.0.0.1", port=5000, debug=True)
