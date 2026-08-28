using TMPro;
using UnityEngine;

public class NarrativeUI : MonoBehaviour
{
    public static NarrativeUI Instance { get; private set; }
    public TMP_Text dialogueText;

    private void Awake()
    {
        Instance = this;
    }

    public void Show(string message)
    {
        Debug.Log(message);
        if (dialogueText != null) dialogueText.text = message;
    }
}
