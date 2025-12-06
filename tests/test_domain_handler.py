"""tests/test_domain_handler.py

Tests for base domain handler functionality.
"""

import sys
sys.path.insert(0, 'src')

import pytest
from domains.base import DomainHandler, DomainQuery, DomainResult
from typing import List, Dict


class ConcreteDomainHandler(DomainHandler):
    """
    Concrete implementation for testing abstract base class.
    """

    def parse_query(self, raw_query: str, context: Dict = None) -> DomainQuery:
        return DomainQuery(
            raw_query=raw_query,
            user_location=context.get('user_location') if context else None
        )

    def fetch_options(self, query: DomainQuery) -> List[DomainResult]:
        return [
            DomainResult(provider="test1", score=85.0),
            DomainResult(provider="test2", score=92.0),
        ]

    def compare_options(self, options: List[DomainResult], priority: str = "balanced") -> str:
        best = max(options, key=lambda x: x.score)
        return f"Best option is {best.provider} with score {best.score}"

    def format_results(self, options: List[DomainResult], comparison: str) -> Dict:
        return {
            'options': [{'provider': opt.provider, 'score': opt.score} for opt in options],
            'comparison': comparison
        }


def test_domain_query_creation():
    """Test DomainQuery dataclass creation."""
    query = DomainQuery(
        raw_query="test query",
        user_location="New York"
    )

    assert query.raw_query == "test query"
    assert query.user_location == "New York"
    assert query.user_preferences == {}  # Defaults to empty dict


def test_domain_result_creation():
    """Test DomainResult dataclass creation."""
    result = DomainResult(
        provider="test_provider",
        score=85.5,
        metadata={'key': 'value'}
    )

    assert result.provider == "test_provider"
    assert result.score == 85.5
    assert result.metadata == {'key': 'value'}


def test_domain_result_score_validation():
    """Test that DomainResult validates score range."""
    # Valid score
    result = DomainResult(provider="test", score=50.0)
    assert result.score == 50.0

    # Invalid score (>100)
    with pytest.raises(ValueError, match="Score must be 0-100"):
        DomainResult(provider="test", score=150.0)

    # Invalid score (<0)
    with pytest.raises(ValueError, match="Score must be 0-100"):
        DomainResult(provider="test", score=-10.0)


def test_concrete_handler_instantiation():
    """Test that concrete handler can be instantiated."""
    handler = ConcreteDomainHandler()

    assert handler is not None
    assert handler.cache is None
    assert handler.geocoder is None


def test_concrete_handler_with_services():
    """Test handler initialization with services."""
    mock_cache = "mock_cache"
    mock_geocoder = "mock_geocoder"

    handler = ConcreteDomainHandler(
        cache_service=mock_cache,
        geocoding_service=mock_geocoder
    )

    assert handler.cache == mock_cache
    assert handler.geocoder == mock_geocoder


def test_handler_process_pipeline():
    """Test the complete process() pipeline."""
    handler = ConcreteDomainHandler()

    result = handler.process("test query", context={'user_location': 'NYC'})

    # Verify pipeline executed
    assert 'options' in result
    assert 'comparison' in result
    assert 'query' in result
    assert len(result['options']) == 2
    assert 'Best option is test2' in result['comparison']


def test_handler_process_pipeline_with_priority():
    """Test process pipeline with priority parameter."""
    handler = ConcreteDomainHandler()

    result = handler.process(
        "test query",
        context={'user_location': 'NYC'},
        priority='price'
    )

    assert 'options' in result
    assert 'comparison' in result


def test_abstract_handler_cannot_instantiate():
    """Test that abstract DomainHandler cannot be instantiated directly."""
    with pytest.raises(TypeError):
        handler = DomainHandler()


def test_handler_repr():
    """Test handler string representation."""
    handler = ConcreteDomainHandler()
    repr_str = repr(handler)

    assert isinstance(repr_str, str)
    assert 'ConcreteDomainHandler' in repr_str or 'no cache' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
