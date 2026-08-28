# CHRONOS AI Character Lab - Starter Kit

This starter kit builds a tiny Unity prototype where **you control Chandru** and
Varun responds differently to three story events. It uses a local Flask server as the initial
"character brain". The first version is deliberately rule-based so it works
without an API key. You can later replace the Python `choose_reaction` function
with a carefully validated LLM or RAG pipeline from your course.

## What you will build

1. The player walks to a journal.
2. Chandru remembers `JournalFound`; Varun receives a distinct goal.
3. Chandru walks to a strange sound.
4. Varun moves toward it while the player keeps control of Chandru.
5. Each reaction appears in a Unity text panel.

## Requirements

- Unity Hub and Unity 6, using a **Universal 3D (URP)** project.
- Python 3.11 or later.
- A code editor. Visual Studio Community is a good default on Windows.

## A. Create the Unity project

1. Open Unity Hub -> **New project** -> **Universal 3D**.
2. Name it `ChronosAICharacterLab`.
3. In the Unity Project window, make these folders:

```text
Assets/Scenes
Assets/Scripts/Characters
Assets/Scripts/Events
Assets/Scripts/UI
Assets/Scripts/Network
Assets/Data
```

4. Copy all files from this kit's `UnityScripts` folder into `Assets/Scripts`.
   Unity can keep the files together initially; you may organize them after the
   first successful run.
5. Save the current scene as `Assets/Scenes/CourtyardPrototype`.

## B. Set up a simple scene

1. Hierarchy -> right-click -> 3D Object -> **Plane**. Rename it `Ground`.
2. Hierarchy -> right-click -> 3D Object -> **Capsule**. Rename it `Chandru`.
   Set Tag to **Player**. Add a **Character Controller**, **Character State**,
   and **Simple Player Controller** component.
3. Drag Chandru's profile into his Character State profile field, then tick
   **Is Player Controlled**. Do **not** add `NPC Brain` to Chandru.
4. Create one more Capsule named `NPC_Varun`. Add these components to it:

```text
Character State
NPC Brain
```

5. Create an empty object called `GameSystems`. Add:

```text
Story Event Manager
AI Character Client
```

6. Create an empty object called `UI`. Add `Narrative UI`.
7. Create a Canvas: Hierarchy -> UI -> Canvas. Inside it create UI -> Text -
   TextMeshPro. Name it `DialogueText`. Set a large font size, position it at
   the bottom of the screen, then drag that TextMeshPro component into the
   `Dialogue Text` field on `Narrative UI`.

## C. Create the character profiles

1. In the Project window, right-click `Assets/Data` -> Create -> CHRONOS ->
   Character Profile.
2. Create `ChandruProfile`:

```text
Character Name: Chandru
Personality Traits: calm, analytical, guarded, loyal
Starting Goal: Protect the journal and understand its history
Starting Fear: 10
Starting Trust: 60
```

3. Create `VarunProfile`:

```text
Character Name: Varun
Personality Traits: adventurous, impulsive, humorous, curious
Starting Goal: Find an exciting thesis topic
Starting Fear: 5
Starting Trust: 55
```

4. Drag `ChandruProfile` into the Profile field on the playable `Chandru` object.
5. Drag `VarunProfile` into the Profile field on `NPC_Varun`.

## D. Create story-event objects

1. Create a Cube and name it `JournalPedestal`. Set scale to `(2, 2, 2)`.
2. Add the `Story Trigger` component. Its Box Collider must have **Is Trigger**
   checked. Assign:

```text
Event Manager: GameSystems
Story Event: JournalFound
Trigger Once: checked
```

3. Create another Cube named `StrangeSoundZone`. Make its collider a trigger.
   Add `Story Trigger` and assign:

```text
Event Manager: GameSystems
Story Event: StrangeSoundHeard
Trigger Once: checked
```

4. Optional: create `GateZone` in the same way and choose `GateLocked`.

## E. Run Version 1 without Python

1. Select `GameSystems`.
2. On `AI Character Client`, untick **Use Server**.
3. If Unity reports an input error, open Edit -> Project Settings -> Player and
   set **Active Input Handling** to **Both**, then restart Unity.
4. Press Play. Use **WASD** or arrow keys to move Chandru.
5. Walk Chandru into `JournalPedestal`, then into `StrangeSoundZone`.
6. Watch the DialogueText and NPC_Varun Inspector values. Varun should walk
   toward the sound. Chandru remains player-controlled, but his Inspector shows
   the memories he has collected.

If the trigger does not fire, confirm that the Player is tagged `Player`, each
event object has **Is Trigger** checked, and the Player has a Character
Controller or collider.

## F. Run the Python character brain

1. Open PowerShell in the kit's `PythonServer` folder.
2. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install Flask and run the server:

```powershell
pip install -r requirements.txt
python app.py
```

4. Keep that PowerShell window open. It should say it is serving on
   `http://127.0.0.1:5000`.
5. In Unity, select `GameSystems`, tick **Use Server**, and press Play.
6. Repeat the journal and sound events. Unity now sends event state to Flask
   and receives structured reactions as JSON.

## G. Safe LLM upgrade later

Do not put a provider API key in Unity. Keep it on the Python server. When
you add an LLM, make it return only this structure:

```json
{
  "action": "talk or investigate",
  "dialogue": "one short in-character sentence",
  "goal": "an allowed current goal",
  "fearDelta": 0
}
```

Validate the allowed action and story event before Unity applies a response.
The authored manuscript must remain the source of truth.

## H. Add free-text conversation with Varun

This is the first version of the feature you described: Chandru can type any
message, rather than selecting a dialogue option. Varun replies in character
and saves a useful memory from selected messages.

1. Keep `NPC_Varun` selected and make sure it has `Character State`, `NPC Brain`,
   and `VarunProfile` assigned.
2. In the Canvas, create a UI -> **Text - TextMeshPro** object named `ChatLog`.
   Place it on the left side of the screen and make it large enough for several
   lines of text.
3. In the Canvas, create UI -> **TextMeshPro - Input Field** named `PlayerInput`.
   Put it beneath `ChatLog`. Set its placeholder text to `Talk to Varun...`.
4. In the Canvas, create UI -> **Button - TextMeshPro** named `SendButton`. Set
   its text to `Send`.
5. Create an empty Canvas child named `VarunConversationSystem`. Add the
   `Varun Conversation UI` component.
6. Drag the scene objects into its Inspector fields:

```text
Varun: NPC_Varun (Character State component)
Player Input: PlayerInput (TMP Input Field component)
Chat Log: ChatLog (TMP Text component)
Send Button: SendButton (Button component)
```

7. Run the Flask server as described in section F, then press Play in Unity.
8. Type messages such as `What do you think about the journal?`, `Did you hear
   that sound?`, or `I am scared.` and click Send. Varun's response appears in
   the chat log. Select `NPC_Varun` during Play mode to see saved memories in
   Character State -> Memory Summary.

### What "memory" means here

- **Character profile:** permanent facts about Varun: adventurous, impulsive,
  humorous, curious.
- **Conversation context:** the last eight chat lines, sent with each message.
- **Persistent story memories:** important facts saved to `CharacterState` and
  visible in the Inspector, such as `Chandru considers the journal important.`

### Important truth about free text

The included local version recognizes a few meaningful topics and proves the
full Unity -> Flask -> memory -> Unity loop without an API key. For Varun to
answer every arbitrary message intelligently, the next step is connecting an
LLM to `choose_conversation()` on the Flask server. Do that only after this
version works. Keep the output limited to `reply` and `memoryToStore`, and add
rules that Varun must not reveal future chapters or invent story facts.

### Dialogue rule

Use the manuscript as the dialogue authority. Varun should be adventurous and
push toward investigation, but he must not know facts the group has not found.
The current event lines are adapted from Chapter 1:

```text
JournalFound: "I think we should go check the haunted house."
StrangeSoundHeard: "That noise is coming from the garden. Let us check it out."
```

## Portfolio milestone

Record a 2-3 minute video showing: the scene, event triggers, live NPC state
in the Inspector, the Flask request log, and two distinct character reactions.
