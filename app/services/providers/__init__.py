"""
providers — Video provider abstraction package.

Public surface
--------------
VideoProvider   — abstract base class every provider must implement.
ResolvedMedia   — dataclass returned by VideoProvider.resolve().
ProviderRegistry — singleton registry; dispatch URL → provider.

Usage::

    from app.services.providers import registry, ResolvedMedia
    resolved: ResolvedMedia = await registry.resolve(url)
"""

from app.services.providers.base import VideoProvider, ResolvedMedia  # noqa: F401
from app.services.providers.registry import ProviderRegistry, registry  # noqa: F401
