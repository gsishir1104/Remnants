using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class SimplePlayerController : MonoBehaviour
{
    public float moveSpeed = 4.5f;
    public float gravity = -20f;
    public Transform cameraTransform;

    private CharacterController controller;
    private float verticalVelocity;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();
        FindHeadCamera();
    }

    private void Update()
    {
        if (cameraTransform == null || !cameraTransform.gameObject.activeInHierarchy)
            FindHeadCamera();

        // Uses Unity's classic Horizontal/Vertical axes: WASD or arrow keys.
        float horizontal = Input.GetAxisRaw("Horizontal");
        float vertical = Input.GetAxisRaw("Vertical");

        // Use the active first-person head camera every frame. This means W
        // moves in the exact direction the player is looking, even if the
        // visual character's animated head is rotated independently.
        Vector3 forward = cameraTransform == null ? transform.forward : cameraTransform.forward;
        Vector3 right = cameraTransform == null ? transform.right : cameraTransform.right;
        forward.y = 0f;
        right.y = 0f;

        // The first-person camera script turns the player with the mouse.
        // Do not rotate the body here: A/D must strafe, and W/S must move
        // forward/backward relative to the direction the player is looking.
        Vector3 move = (forward.normalized * vertical + right.normalized * horizontal).normalized;

        if (controller.isGrounded && verticalVelocity < 0f)
            verticalVelocity = -2f;

        verticalVelocity += gravity * Time.deltaTime;
        Vector3 velocity = move * moveSpeed;
        velocity.y = verticalVelocity;
        controller.Move(velocity * Time.deltaTime);
    }

    private void FindHeadCamera()
    {
        if (Camera.main != null)
            cameraTransform = Camera.main.transform;
    }
}
