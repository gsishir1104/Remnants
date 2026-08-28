using UnityEngine;

/// <summary>
/// First-person mouse look. Attach this to the Main Camera. The camera must
/// be somewhere under the playable character in the Hierarchy.
/// </summary>
public class FirstPersonHeadCamera : MonoBehaviour
{
    [Header("Character to turn")]
    public Transform playerBody;

    [Header("Look settings")]
    [Range(0.1f, 10f)] public float sensitivity = 1.5f;
    public float minPitch = -75f;
    public float maxPitch = 75f;

    private float pitch;
    private bool cursorLocked = true;

    private void Awake()
    {
        // Find the actual player root, even if the camera is inside the
        // visible character model. This keeps camera rotation and WASD
        // movement on the same object.
        CharacterController controller = GetComponentInParent<CharacterController>();
        if (controller != null)
            playerBody = controller.transform;
    }

    private void Start()
    {
        LockCursor(true);
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape)) LockCursor(false);
        if (Input.GetMouseButtonDown(0)) LockCursor(true);
        if (!cursorLocked || playerBody == null) return;

        float mouseX = Input.GetAxis("Mouse X") * sensitivity;
        float mouseY = Input.GetAxis("Mouse Y") * sensitivity;

        playerBody.Rotate(Vector3.up * mouseX);
        pitch = Mathf.Clamp(pitch - mouseY, minPitch, maxPitch);
        transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
    }

    private void LockCursor(bool shouldLock)
    {
        cursorLocked = shouldLock;
        Cursor.lockState = shouldLock ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible = !shouldLock;
    }
}
