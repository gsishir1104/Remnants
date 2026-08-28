using System.Collections.Generic;
using UnityEngine;

public class CharacterState : MonoBehaviour
{
    public CharacterProfile profile;
    [Tooltip("Turn this on for Chandru. Player-controlled characters remember events but do not receive AI movement or dialogue commands.")]
    public bool isPlayerControlled;

    [Header("Runtime state - visible while the game is playing")]
    [Range(0, 100)] public int fear;
    [Range(0, 100)] public int trust;
    public string currentGoal;
    public string currentAction = "idle";
    [TextArea(3, 8)] public string memorySummary;

    private readonly List<string> memories = new List<string>();

    public IReadOnlyList<string> Memories => memories;

    private void Awake()
    {
        if (profile == null)
        {
            Debug.LogError($"{name} needs a CharacterProfile.");
            enabled = false;
            return;
        }

        fear = profile.startingFear;
        trust = profile.startingTrust;
        currentGoal = profile.startingGoal;
        RefreshMemorySummary();
    }

    public void Remember(string memory)
    {
        if (memories.Contains(memory)) return;
        memories.Add(memory);
        RefreshMemorySummary();
    }

    public void ChangeFear(int amount)
    {
        fear = Mathf.Clamp(fear + amount, 0, 100);
    }

    public void SetGoal(string goal)
    {
        currentGoal = goal;
    }

    private void RefreshMemorySummary()
    {
        memorySummary = memories.Count == 0 ? "No story events remembered yet." : string.Join("\n", memories);
    }
}
