using UnityEngine;

[RequireComponent(typeof(CharacterState))]
public class NPCBrain : MonoBehaviour
{
    public float movementSpeed = 2f;

    private CharacterState state;
    private Vector3 destination;
    private bool isMoving;

    private void Awake()
    {
        state = GetComponent<CharacterState>();
    }

    private void Update()
    {
        if (!isMoving) return;

        Vector3 flatDestination = new Vector3(destination.x, transform.position.y, destination.z);
        transform.position = Vector3.MoveTowards(transform.position, flatDestination, movementSpeed * Time.deltaTime);
        transform.LookAt(flatDestination);

        if (Vector3.Distance(transform.position, flatDestination) < 0.05f)
        {
            isMoving = false;
            state.currentAction = "idle";
        }
    }

    public void ApplyReaction(AIReaction reaction, Vector3 eventPosition)
    {
        state.SetGoal(reaction.goal);
        state.ChangeFear(reaction.fearDelta);
        state.currentAction = reaction.action;

        NarrativeUI.Instance?.Show($"{state.profile.characterName}: {reaction.dialogue}");

        if (reaction.action == "investigate")
        {
            destination = eventPosition;
            isMoving = true;
        }
    }
}

[System.Serializable]
public class AIReaction
{
    public string action;
    public string dialogue;
    public string goal;
    public int fearDelta;
}
