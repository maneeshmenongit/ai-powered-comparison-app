"""
Base domain classes and interfaces.

Provides abstract base classes that all domains must implement.
"""

from .domain_handler import DomainHandler, DomainQuery, DomainResult

__all__ = [
    'DomainHandler',
    'DomainQuery',
    'DomainResult',
]
