using System.Collections;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public class VarunConversationUI : MonoBehaviour
{
    [Header("Scene references")]
    public CharacterState varun;
    public TMP_InputField playerInput;
    public TMP_Text chatLog;
    public Button sendButton;

    [Header("Local Flask server")]
    public string serverUrl = "http://127.0.0.1:5000/conversation";

    [TextArea(2, 8)] public string recentConversation;

    private void Awake()
    {
        if (sendButton != null) sendButton.onClick.AddListener(SendMessage);
    }

    public void SendMessage()
    {
        if (varun == null || playerInput == null) return;

        string text = playerInput.text.Trim();
        if (string.IsNullOrEmpty(text)) return;

        AppendToLog($"Chandru: {text}");
        playerInput.text = "";
        StartCoroutine(RequestReply(text));
    }

    private IEnumerator RequestReply(string playerText)
    {
        ConversationRequest payload = new ConversationRequest
        {
            characterName = varun.profile.characterName,
            personalityTraits = varun.profile.personalityTraits,
            currentGoal = varun.currentGoal,
            fear = varun.fear,
            memories = string.Join(" | ", varun.Memories),
            recentConversation = recentConversation,
            playerText = playerText
        };

        string json = JsonUtility.ToJson(payload);
        using UnityWebRequest request = new UnityWebRequest(serverUrl, "POST");
        request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            AppendToLog("Varun: I cannot think straight right now. Try again in a moment.");
            Debug.LogError(request.error);
            yield break;
        }

        ConversationResponse response = JsonUtility.FromJson<ConversationResponse>(request.downloadHandler.text);
        if (response == null || string.IsNullOrWhiteSpace(response.reply))
        {
            AppendToLog("Varun: I am not sure what to say.");
            yield break;
        }

        AppendToLog($"Varun: {response.reply}");
        if (!string.IsNullOrWhiteSpace(response.memoryToStore))
            varun.Remember(response.memoryToStore);
    }

    private void AppendToLog(string line)
    {
        recentConversation = string.IsNullOrWhiteSpace(recentConversation)
            ? line
            : recentConversation + "\n" + line;

        // Keep only the most recent conversation so requests stay small.
        string[] lines = recentConversation.Split('\n');
        if (lines.Length > 8)
            recentConversation = string.Join("\n", lines, lines.Length - 8, 8);

        if (chatLog != null) chatLog.text = recentConversation;
    }
}

[System.Serializable]
public class ConversationRequest
{
    public string characterName;
    public string personalityTraits;
    public string currentGoal;
    public int fear;
    public string memories;
    public string recentConversation;
    public string playerText;
}

[System.Serializable]
public class ConversationResponse
{
    public string reply;
    public string memoryToStore;
}
