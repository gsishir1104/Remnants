using UnityEngine;

[CreateAssetMenu(fileName = "CharacterProfile", menuName = "CHRONOS/Character Profile")]
public class CharacterProfile : ScriptableObject
{
    public string characterName;
    [TextArea(2, 5)] public string personalityTraits;
    [TextArea(2, 5)] public string startingGoal;
    [Range(0, 100)] public int startingFear = 10;
    [Range(0, 100)] public int startingTrust = 50;
}
