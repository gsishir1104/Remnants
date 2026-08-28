using UnityEngine;

/// <summary>
/// Moves a pedestrian or vehicle through a repeating list of scene waypoints.
/// Use separate waypoint lists for sidewalks and roads.
/// </summary>
public class WaypointLoopMover : MonoBehaviour
{
    public Transform[] waypoints;
    [Min(0.1f)] public float speed = 2f;
    [Min(0.1f)] public float turnSpeed = 8f;
    [Min(0.05f)] public float arrivalDistance = 0.25f;
    [Tooltip("Use different values on duplicates so they spread around the route.")]
    public int startingWaypoint;

    private int targetIndex;

    private void Start()
    {
        if (waypoints != null && waypoints.Length > 0)
            targetIndex = Mathf.Abs(startingWaypoint) % waypoints.Length;
    }

    private void Update()
    {
        if (waypoints == null || waypoints.Length < 2 || waypoints[targetIndex] == null)
            return;

        Vector3 target = waypoints[targetIndex].position;
        Vector3 direction = target - transform.position;
        direction.y = 0f;

        if (direction.sqrMagnitude <= arrivalDistance * arrivalDistance)
        {
            targetIndex = (targetIndex + 1) % waypoints.Length;
            return;
        }

        Quaternion desiredRotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
        transform.rotation = Quaternion.Slerp(transform.rotation, desiredRotation, turnSpeed * Time.deltaTime);
        transform.position += transform.forward * speed * Time.deltaTime;
    }
}
