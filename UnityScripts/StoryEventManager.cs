using System;
using UnityEngine;

public class StoryEventManager : MonoBehaviour
{
    public static event Action<StoryEvent, Vector3> EventRaised;

    public void RaiseEvent(StoryEvent storyEvent, Vector3 location)
    {
        Debug.Log($"Story event raised: {storyEvent}");
        EventRaised?.Invoke(storyEvent, location);
    }
}
