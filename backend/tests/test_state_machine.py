"""Tests for the status state machine."""
import pytest
from app.state_machine import validate_transition, InvalidTransitionError, VALID_TRANSITIONS


class TestValidTransitions:
    """Verify every allowed transition passes validation."""

    @pytest.mark.parametrize("current,target", [
        ("created", "picked_up"),
        ("picked_up", "in_transit"),
        ("in_transit", "delivered"),
        ("created", "failed"),
        ("picked_up", "failed"),
        ("in_transit", "failed"),
    ])
    def test_valid_transition(self, current, target):
        """Should not raise for allowed transitions."""
        validate_transition(current, target)


class TestInvalidTransitions:
    """Verify disallowed transitions raise InvalidTransitionError."""

    @pytest.mark.parametrize("current,target", [
        # skipping steps
        ("created", "in_transit"),
        ("created", "delivered"),
        ("picked_up", "delivered"),
        # going backwards
        ("picked_up", "created"),
        ("in_transit", "picked_up"),
        ("delivered", "in_transit"),
        # terminal states
        ("delivered", "failed"),
        ("delivered", "created"),
        ("failed", "created"),
        ("failed", "picked_up"),
    ])
    def test_invalid_transition(self, current, target):
        """Should raise InvalidTransitionError."""
        with pytest.raises(InvalidTransitionError) as exc_info:
            validate_transition(current, target)
        assert current in str(exc_info.value)
        assert target in str(exc_info.value)

    def test_error_message_lists_allowed(self):
        """Error message should tell the user what transitions ARE allowed."""
        with pytest.raises(InvalidTransitionError) as exc_info:
            validate_transition("created", "delivered")
        msg = str(exc_info.value)
        assert "picked_up" in msg
        assert "failed" in msg

    def test_terminal_state_message(self):
        """Terminal state error should say 'none (terminal state)'."""
        with pytest.raises(InvalidTransitionError) as exc_info:
            validate_transition("delivered", "failed")
        assert "terminal" in str(exc_info.value).lower()


class TestUnknownStatuses:
    """Verify unknown statuses raise ValueError."""

    def test_unknown_current(self):
        with pytest.raises(ValueError, match="Unknown current status"):
            validate_transition("unknown", "picked_up")

    def test_unknown_target(self):
        with pytest.raises(ValueError, match="Unknown target status"):
            validate_transition("created", "unknown")
