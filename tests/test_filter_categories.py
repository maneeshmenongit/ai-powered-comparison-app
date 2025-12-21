"""Test filter categories for restaurant domain.

Tests the new filter category feature:
- Filter categories (Food, Drinks, Dessert, Cafe)
- Default to "Food"
- Validation and normalization
"""

import sys
sys.path.insert(0, 'src')

import pytest
from domains.restaurants.models import (
    RestaurantQuery,
    FILTER_CATEGORIES,
    get_filter_category,
    validate_filter_category
)


class TestFilterCategories:
    """Test filter category constants and functionality."""

    def test_filter_categories_exist(self):
        """Test that all filter categories are defined."""
        assert 'Food' in FILTER_CATEGORIES
        assert 'Drinks' in FILTER_CATEGORIES
        assert 'Ice Cream' in FILTER_CATEGORIES
        assert 'Cafe' in FILTER_CATEGORIES

    def test_filter_category_structure(self):
        """Test that each filter has required fields."""
        for category in FILTER_CATEGORIES.values():
            assert 'name' in category
            assert 'description' in category
            assert 'keywords' in category
            assert 'icon' in category
            assert isinstance(category['keywords'], list)

    def test_filter_category_icons(self):
        """Test that filter categories have correct icons."""
        assert FILTER_CATEGORIES['Food']['icon'] == '🍽️'
        assert FILTER_CATEGORIES['Drinks']['icon'] == '🍸'
        assert FILTER_CATEGORIES['Ice Cream']['icon'] == '🍨'
        assert FILTER_CATEGORIES['Cafe']['icon'] == '☕'

    def test_filter_category_keywords(self):
        """Test that filter categories have relevant keywords."""
        assert 'restaurant' in FILTER_CATEGORIES['Food']['keywords']
        assert 'bar' in FILTER_CATEGORIES['Drinks']['keywords']
        assert 'ice cream' in FILTER_CATEGORIES['Ice Cream']['keywords']
        assert 'coffee' in FILTER_CATEGORIES['Cafe']['keywords']


class TestRestaurantQueryWithFilters:
    """Test RestaurantQuery with filter categories."""

    def test_default_filter_is_food(self):
        """Test that filter_category defaults to Food."""
        query = RestaurantQuery(location="New York")
        assert query.filter_category == "Food"

    def test_explicit_filter_category(self):
        """Test setting filter_category explicitly."""
        query = RestaurantQuery(
            location="New York",
            filter_category="Drinks"
        )
        assert query.filter_category == "Drinks"

    def test_filter_in_to_dict(self):
        """Test that filter_category is included in to_dict()."""
        query = RestaurantQuery(
            location="New York",
            filter_category="Cafe"
        )
        result = query.to_dict()

        assert 'filter_category' in result
        assert result['filter_category'] == "Cafe"

    def test_filter_in_repr_non_food(self):
        """Test that filter appears in repr when not Food."""
        query = RestaurantQuery(
            cuisine="Italian",
            location="New York",
            filter_category="Drinks"
        )
        repr_str = repr(query)

        assert '[Drinks]' in repr_str
        assert 'Italian' in repr_str

    def test_filter_not_in_repr_when_food(self):
        """Test that Food filter doesn't appear in repr (default)."""
        query = RestaurantQuery(
            cuisine="Italian",
            location="New York",
            filter_category="Food"
        )
        repr_str = repr(query)

        # Should not show [Food] since it's the default
        assert '[Food]' not in repr_str
        assert 'Italian' in repr_str

    def test_all_filter_categories(self):
        """Test creating queries with all filter categories."""
        for category in ['Food', 'Drinks', 'Ice Cream', 'Cafe']:
            query = RestaurantQuery(
                location="New York",
                filter_category=category
            )
            assert query.filter_category == category


class TestFilterHelperFunctions:
    """Test helper functions for filter categories."""

    def test_get_filter_category_valid(self):
        """Test getting a valid filter category."""
        result = get_filter_category('Food')

        assert result['name'] == 'Food'
        assert result['icon'] == '🍽️'
        assert isinstance(result['keywords'], list)

    def test_get_filter_category_invalid_returns_food(self):
        """Test that invalid filter returns Food."""
        result = get_filter_category('InvalidCategory')

        assert result['name'] == 'Food'
        assert result['icon'] == '🍽️'

    def test_validate_filter_category_valid(self):
        """Test validating valid filter names."""
        assert validate_filter_category('Food') == 'Food'
        assert validate_filter_category('Drinks') == 'Drinks'
        assert validate_filter_category('Ice Cream') == 'Ice Cream'
        assert validate_filter_category('Cafe') == 'Cafe'

    def test_validate_filter_category_case_insensitive(self):
        """Test that validation is case-insensitive."""
        assert validate_filter_category('food') == 'Food'
        assert validate_filter_category('DRINKS') == 'Drinks'
        assert validate_filter_category('ice cream') == 'Ice Cream'
        assert validate_filter_category('CaFe') == 'Cafe'

    def test_validate_filter_category_invalid_returns_food(self):
        """Test that invalid filter defaults to Food."""
        assert validate_filter_category('Pizza') == 'Food'
        assert validate_filter_category('') == 'Food'
        assert validate_filter_category('Random') == 'Food'

    def test_validate_filter_category_normalization(self):
        """Test that validation normalizes to proper case."""
        # Should normalize to proper case
        result = validate_filter_category('drinks')
        assert result == 'Drinks'
        assert result in FILTER_CATEGORIES


class TestFilterCategoryIntegration:
    """Test filter categories in real-world scenarios."""

    def test_bar_search_query(self):
        """Test creating a bar search query."""
        query = RestaurantQuery(
            location="Manhattan",
            filter_category="Drinks",
            price_range="$$"
        )

        assert query.filter_category == "Drinks"
        assert '[Drinks]' in repr(query)
        assert query.to_dict()['filter_category'] == "Drinks"

    def test_coffee_shop_query(self):
        """Test creating a cafe search query."""
        query = RestaurantQuery(
            location="Brooklyn",
            filter_category="Cafe",
            open_now=True
        )

        assert query.filter_category == "Cafe"
        assert '[Cafe]' in repr(query)

    def test_ice_cream_query(self):
        """Test creating an ice cream search query."""
        query = RestaurantQuery(
            location="Queens",
            filter_category="Ice Cream",
            rating_min=4.0
        )

        assert query.filter_category == "Ice Cream"
        assert '[Ice Cream]' in repr(query)

    def test_restaurant_query_default(self):
        """Test creating a normal restaurant query (default Food)."""
        query = RestaurantQuery(
            cuisine="Italian",
            location="Bronx",
            price_range="$$$"
        )

        assert query.filter_category == "Food"
        # Food should not appear in repr since it's default
        assert '[Food]' not in repr(query)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
