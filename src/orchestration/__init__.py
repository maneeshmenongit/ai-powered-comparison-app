"""
Orchestration layer for multi-domain coordination.

This package handles cross-domain functionality like query routing,
result aggregation, and multi-domain recommendations.
"""

from .domain_router import DomainRouter, create_router

__all__ = [
    'DomainRouter',
    'create_router',
]
