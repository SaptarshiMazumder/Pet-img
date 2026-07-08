"""
Tests for the frame pricing catalog.

These guard *business rules*, not trivia. The most important one:
we must never accidentally price a product below what it costs us.
A fat-fingered number in prices.py would be caught here before it ships.
"""
from backend.config.prices import (
    CATEGORY_OPTIONS,
    get_price,
    get_framed_base_cost,
    get_available_sizes,
    get_available_colors,
)


def test_every_size_has_a_positive_price():
    """No product should ever be listed with a missing or zero price."""
    for category in CATEGORY_OPTIONS:
        for size in get_available_sizes(category):
            price = get_price(category, size)
            assert price > 0, f"{category} / {size} has a non-positive price: {price}"


def test_price_is_never_below_cost():
    """
    Core money rule: the sale price must always cover the framed base cost,
    otherwise we'd lose money on every sale of that item.
    """
    for category in CATEGORY_OPTIONS:
        for size in get_available_sizes(category):
            price = get_price(category, size)
            cost = get_framed_base_cost(category, size)
            assert price >= cost, (
                f"{category} / {size}: price {price} is below cost {cost} "
                f"— this item would sell at a loss!"
            )


def test_every_frame_has_at_least_one_color_and_size():
    """A frame with no colors or no sizes can't actually be ordered."""
    for category in CATEGORY_OPTIONS:
        assert len(get_available_colors(category)) >= 1, f"{category} has no colors"
        assert len(get_available_sizes(category)) >= 1, f"{category} has no sizes"


def test_unknown_lookups_return_safe_defaults():
    """Bad input must fail safe (0 / empty), never crash the caller."""
    assert get_price("no such frame", "no such size") == 0
    assert get_framed_base_cost("no such frame", "no such size") == 0
    assert get_available_sizes("no such frame") == []
    assert get_available_colors("no such frame") == []
