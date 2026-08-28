using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

public class AICharacterClient : MonoBehaviour
{
    [Tooltip("Use localhost while Flask runs on the same computer.")]
    public string serverUrl = "http://127.0.0.1:5000/character_reaction";
    public bool useServer = true;

    private void OnEnable()
    {
        StoryEventManager.EventRaised += OnStoryEvent;
    }

    private void OnDisable()
    {
        StoryEventManager.EventRaised -= OnStoryEvent;
    }

    private void OnStoryEvent(StoryEvent storyEvent, Vector3 eventPosition)
    {
        CharacterState[] characters = FindObjectsByType<CharacterState>(FindObjectsSortMode.None);
        foreach (CharacterState character in characters)
        {
            character.Remember(storyEvent.ToString());
            // Chandru is the playable character. He keeps memories, but the
            // player—not the AI server—chooses where he goes and what he does.
            if (character.isPlayerControlled) continue;
            if (useServer) StartCoroutine(RequestReaction(character, storyEvent, eventPosition));
            else ApplyFallback(character, storyEvent, eventPosition);
        }
    }

    private IEnumerator RequestReaction(CharacterState character, StoryEvent storyEvent, Vector3 eventPosition)
    {
        CharacterRequest payload = new CharacterRequest
        {
            characterName = character.profile.characterName,
            personalityTraits = character.profile.personalityTraits,
            currentGoal = character.currentGoal,
            fear = character.fear,
            trust = character.trust,
            memories = string.Join(" | ", character.Memories),
            eventName = storyEvent.ToString()
        };

        string json = JsonUtility.ToJson(payload);
        using UnityWebRequest request = new UnityWebRequest(serverUrl, "POST");
        request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogWarning($"AI server unavailable. Using fallback. {request.error}");
            ApplyFallback(character, storyEvent, eventPosition);
            yield break;
        }

        AIReaction reaction = JsonUtility.FromJson<AIReaction>(request.downloadHandler.text);
        NPCBrain brain = character.GetComponent<NPCBrain>();
        if (brain != null && reaction != null) brain.ApplyReaction(reaction, eventPosition);
    }

    private void ApplyFallback(CharacterState character, StoryEvent storyEvent, Vector3 eventPosition)
    {
        string name = character.profile.characterName.ToLowerInvariant();
        AIReaction reaction = new AIReaction { action = "talk", fearDelta = 0, goal = character.currentGoal };

        if (storyEvent == StoryEvent.IdentityClueFound && name == "chandru")
        {
            reaction.goal = "Recover his identity";
            reaction.dialogue = "This clue is connected to the life I cannot remember.";
        }
        else if (storyEvent == StoryEvent.IdentityClueFound && name == "varun")
        {
            reaction.goal = "Help Chandru question the townspeople";
            reaction.dialogue = "I do not recognize this from our childhood. Someone local may know what it means.";
        }
        else if (storyEvent == StoryEvent.WitnessLocated && name == "varun")
        {
            reaction.goal = "Help Chandru question the witness";
            reaction.dialogue = "Choose your question carefully. This person may only give us one honest answer.";
        }
        else
        {
            reaction.dialogue = "Someone in this city may know what happened to your memory.";
        }

        NPCBrain brain = character.GetComponent<NPCBrain>();
        if (brain != null) brain.ApplyReaction(reaction, eventPosition);
    }
}

[System.Serializable]
public class CharacterRequest
{
    public string characterName;
    public string personalityTraits;
    public string currentGoal;
    public int fear;
    public int trust;
    public string memories;
    public string eventName;
}
