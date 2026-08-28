using UnityEngine;

[RequireComponent(typeof(Collider))]
public class StoryTrigger : MonoBehaviour
{
    public StoryEventManager eventManager;
    public StoryEvent storyEvent;
    public bool triggerOnce = true;

    private bool used;

    private void Reset()
    {
        GetComponent<Collider>().isTrigger = true;
    }

    private void OnTriggerEnter(Collider other)
    {
        if (used && triggerOnce) return;
        if (!other.CompareTag("Player")) return;

        if (eventManager == null)
        {
            Debug.LogError("Assign StoryEventManager in the Inspector.");
            return;
        }

        used = true;
        eventManager.RaiseEvent(storyEvent, transform.position);
    }
}
