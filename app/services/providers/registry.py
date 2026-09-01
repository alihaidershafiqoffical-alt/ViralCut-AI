"""
providers/registry.py
---------------------
``ProviderRegistry`` — dispatch a validated URL to the correct VideoProvider.

The module-level ``registry`` singleton is pre-populated with all built-in
providers.  Routers and tasks import it directly::

    from app.services.providers import registry
    resolved = await registry.resolve(url)

Adding a new provider at runtime::

    from app.services.providers import registry
    registry.register(MyNewProvider())
"""

from __future__ import annotations

import logging
from typing import List

from app.services.providers.base import (
    IngestionError,
    ResolvedMedia,
    UnsupportedProviderError,
    VideoProvider,
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Ordered registry of ``VideoProvider`` instances.

    Providers are evaluated in registration order.  The first provider whose
    ``can_handle(url)`` returns True is used for resolution.  If none match,
    ``UnsupportedProviderError`` is raised.
    """

    def __init__(self) -> None:
        self._providers: List[VideoProvider] = []

    def register(self, provider: VideoProvider) -> None:
        """
        Register *provider*.  Providers added first have higher priority.

        Parameters
        ----------
        provider:
            A concrete ``VideoProvider`` instance.
        """
        self._providers.append(provider)
        logger.debug(
            "Registered provider '%s' (%s)",
            provider.provider_id,
            provider.display_name,
        )

    async def resolve(self, url: str) -> ResolvedMedia:
        """
        Dispatch *url* to the first matching provider and return a
        ``ResolvedMedia``.

        Parameters
        ----------
        url:
            A validated HTTPS URL (already passed through
            ``UrlValidationService.validate``).

        Returns
        -------
        ResolvedMedia
            Direct download URL + metadata from the matched provider.

        Raises
        ------
        UnsupportedProviderError
            When no registered provider can handle the URL.
        IngestionError
            When the matched provider raises one (propagated as-is).
        """
        for provider in self._providers:
            if provider.can_handle(url):
                logger.info(
                    "Provider '%s' handling URL: %s",
                    provider.provider_id,
                    url,
                )
                # Let provider exceptions propagate — the router maps them to
                # the appropriate HTTP status code.
                return await provider.resolve(url)

        raise UnsupportedProviderError(url)

    @property
    def registered_providers(self) -> List[str]:
        """Return a list of registered provider IDs (for health/info endpoints)."""
        return [p.provider_id for p in self._providers]


# ---------------------------------------------------------------------------
# Module-level singleton — populated at the bottom of this file so that
# circular-import risk is minimised.  Providers import from base.py only.
# ---------------------------------------------------------------------------

registry = ProviderRegistry()

# Deferred imports to avoid circular dependency at module load time.
from app.services.providers.youtube import YouTubeProvider       # noqa: E402
from app.services.providers.direct_url import DirectUrlProvider  # noqa: E402

registry.register(YouTubeProvider())
registry.register(DirectUrlProvider())
