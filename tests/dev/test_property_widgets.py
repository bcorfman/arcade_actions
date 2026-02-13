"""Unit tests for property inspector parsing and expression evaluation."""

from __future__ import annotations

import pytest

from arcadeactions.dev.property_widgets import ExpressionEvaluator, parse_property_text


def test_expression_evaluator_supports_arithmetic_and_names():
    """Expressions should evaluate with arithmetic operators and named constants."""
    evaluator = ExpressionEvaluator({"SCREEN_CENTER": 400.0})

    result = evaluator.evaluate("SCREEN_CENTER + 25 * 2")

    assert result == 450.0


def test_expression_evaluator_supports_tuple_values():
    """Tuple expressions should evaluate to tuple values."""
    evaluator = ExpressionEvaluator({"SCREEN_CENTER_X": 400.0, "SCREEN_CENTER_Y": 300.0})

    result = evaluator.evaluate("(SCREEN_CENTER_X, SCREEN_CENTER_Y)")

    assert result == (400.0, 300.0)


def test_parse_boolean_property_values():
    """Boolean properties should accept text aliases."""
    assert parse_property_text("is_collidable", "true", {}) is True
    assert parse_property_text("mirrored_y", "0", {}) is False


def test_parse_boolean_rejects_invalid_text():
    """Invalid boolean text should raise a value error."""
    with pytest.raises(ValueError):
        parse_property_text("is_collidable", "maybe", {})


def test_parse_color_hex_value():
    """Hex color text should convert to RGB tuple."""
    value = parse_property_text("color", "#3366CC", {})

    assert value == (51, 102, 204)


def test_parse_alpha_casts_to_int():
    """Alpha/opacity should be parsed as ints."""
    assert parse_property_text("alpha", "127.8", {}) == 127


def test_unsupported_expression_node_raises_value_error():
    """Function-call expressions should be rejected by evaluator."""
    evaluator = ExpressionEvaluator({})

    with pytest.raises(ValueError):
        evaluator.evaluate("abs(-1)")
