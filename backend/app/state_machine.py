"""Shipment status state machine.

Lifecycle: created -> picked_up -> in_transit -> delivered
`failed` is allowed from any non-delivered status.
`delivered` and `failed` are terminal states.
"""

VALID_STATUSES = {"created", "picked_up", "in_transit", "delivered", "failed"}

VALID_TRANSITIONS: dict[str, set[str]] = {
    "created":    {"picked_up", "failed"},
    "picked_up":  {"in_transit", "failed"},
    "in_transit": {"delivered", "failed"},
    "delivered":  set(),
    "failed":     set(),
}


class InvalidTransitionError(Exception):
    """Raised when a status transition is not allowed."""

    def __init__(self, current: str, target: str):
        self.current = current
        self.target = target
        allowed = VALID_TRANSITIONS.get(current, set())
        super().__init__(
            f"Cannot transition from '{current}' to '{target}'. "
            f"Allowed transitions from '{current}': {sorted(allowed) or 'none (terminal state)'}."
        )


def validate_transition(current: str, target: str) -> None:
    """Validate that transitioning from current to target is allowed.

    Raises:
        InvalidTransitionError: if the transition is not allowed.
        ValueError: if either status is not a recognised status.
    """
    if current not in VALID_STATUSES:
        raise ValueError(f"Unknown current status: '{current}'")
    if target not in VALID_STATUSES:
        raise ValueError(f"Unknown target status: '{target}'")
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target)
