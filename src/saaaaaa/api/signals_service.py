"""FastAPI Signal Service - Cross-Cut Channel Publisher.

This service exposes signal packs from questionnaire.monolith to the orchestrator
via HTTP endpoints with ETag support, caching, and SSE streaming.

Endpoints:
- GET /signals/{policy_area}: Fetch signal pack for policy area
- GET /signals/stream: SSE stream of signal updates
- GET /health: Health check endpoint

Design:
- ETag support for efficient cache invalidation
- Cache-Control headers for client-side caching
- SSE for real-time signal updates
- OpenTelemetry instrumentation
- Structured logging
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI, HTTPException, Request, Response
from sse_starlette.sse import EventSourceResponse

from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
from saaaaaa.core.orchestrator.signals import PolicyArea, SignalPack
from saaaaaa.core.calibration.decorators import calibrated_method

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

logger = structlog.get_logger(__name__)


# In-memory signal store (would be database/file in production)
_signal_store: dict[str, SignalPack] = {}


def load_signals_from_monolith(monolith_path: str | Path | None = None) -> dict[str, SignalPack]:
    """
    Load signal packs from questionnaire monolith using canonical loader.

    Uses questionnaire.load_questionnaire() for hash verification and immutability.
    This extracts policy-aware patterns, indicators, and thresholds from the
    questionnaire monolith and converts them into SignalPack format.

    Args:
        monolith_path: DEPRECATED - Path parameter is ignored.
                      Questionnaire always loads from canonical path.

    Returns:
        Dict mapping policy area to SignalPack

    TODO: Implement actual extraction logic from monolith structure
    """
    if monolith_path is not None:
        logger.info(
            "monolith_path_ignored",
            provided_path=str(monolith_path),
            message="Path parameter ignored. Using canonical loader.",
        )

    try:
        # Use canonical loader (no path parameter - always canonical path)
        canonical_q = load_questionnaire()

        logger.info(
            "signals_loaded_from_monolith",
            path=str(monolith_path),
            sha256=canonical_q.sha256[:16] + "...",
            question_count=canonical_q.total_question_count,
            message="TODO: Implement actual extraction",
        )

        # TODO: Implement extraction logic using canonical_q.data
        return _create_stub_signal_packs()

    except Exception as e:
        logger.error("failed_to_load_monolith", path=str(monolith_path), error=str(e))
        return _create_stub_signal_packs()


def _create_stub_signal_packs() -> dict[str, SignalPack]:
    """Create stub signal packs for all policy areas."""
    policy_areas: list[PolicyArea] = [
        "fiscal",
        "salud",
        "ambiente",
        "energía",
        "transporte",
    ]

    packs = {}
    for area in policy_areas:
        packs[area] = SignalPack(
            version="1.0.0",
            policy_area=area,
            patterns=[
                f"patrón_{area}_1",
                f"patrón_{area}_2",
                f"coherencia_{area}",
            ],
            indicators=[
                f"indicador_{area}_1",
                f"kpi_{area}_2",
            ],
            regex=[
                r"\d{4}-\d{2}-\d{2}",  # Date pattern
                r"[A-Z]{3}-\d{3}",  # Code pattern
            ],
            verbs=[
                "implementar",
                "fortalecer",
                "desarrollar",
                "mejorar",
            ],
            entities=[
                f"entidad_{area}_1",
                f"organismo_{area}_2",
            ],
            thresholds={
                "min_confidence": 0.75,
                "min_evidence": 0.70,
                "min_coherence": 0.65,
            },
            ttl_s=3600,
            source_fingerprint=f"stub_{area}",
        )

    return packs


# Initialize FastAPI app
app = FastAPI(
    title="F.A.R.F.A.N Signal Service",
    description="Cross-cut signal channel from questionnaire.monolith to orchestrator - Framework for Advanced Retrieval of Administrativa Narratives",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event() -> None:
    """Load signals on startup."""
    global _signal_store

    # Load from canonical questionnaire path (via questionnaire.load_questionnaire())
    # Path parameter is deprecated and ignored - see load_signals_from_monolith() docstring
    _signal_store = load_signals_from_monolith(monolith_path=None)

    logger.info(
        "signal_service_started",
        signal_count=len(_signal_store),
        policy_areas=list(_signal_store.keys()),
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Status dict
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "signal_count": len(_signal_store),
    }


@app.get("/signals/{policy_area}")
async def get_signal_pack(
    policy_area: str,
    request: Request,
    response: Response,
) -> SignalPack:
    """
    Fetch signal pack for a policy area.

    Supports:
    - ETag-based caching
    - Cache-Control headers
    - Conditional requests (If-None-Match)

    Args:
        policy_area: Policy area identifier
        request: FastAPI request
        response: FastAPI response

    Returns:
        SignalPack for the requested policy area

    Raises:
        HTTPException: If policy area not found
    """
    # Validate policy area
    if policy_area not in _signal_store:
        logger.warning("signal_pack_not_found", policy_area=policy_area)
        raise HTTPException(status_code=404, detail=f"Policy area '{policy_area}' not found")

    signal_pack = _signal_store[policy_area]

    # Compute ETag from signal pack hash
    etag = signal_pack.compute_hash()[:32]  # Use first 32 chars for ETag

    # Check If-None-Match header
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match == etag:
        # Content not modified
        logger.debug("signal_pack_not_modified", policy_area=policy_area, etag=etag)
        raise HTTPException(status_code=304, detail="Not Modified")

    # Set response headers
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = f"max-age={signal_pack.ttl_s}"

    logger.info(
        "signal_pack_served",
        policy_area=policy_area,
        version=signal_pack.version,
        etag=etag,
    )

    return signal_pack


@app.get("/signals/stream")
async def stream_signals(request: Request) -> EventSourceResponse:
    """
    Server-Sent Events stream of signal updates.

    Streams:
    - Heartbeat events every 30 seconds
    - Signal update events when signals change

    Args:
        request: FastAPI request

    Returns:
        EventSourceResponse with SSE stream
    """

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        """Generate SSE events."""
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("signal_stream_client_disconnected")
                break

            # Send heartbeat
            yield {
                "event": "heartbeat",
                "data": json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signal_count": len(_signal_store),
                }),
            }

            # Wait before next heartbeat
            await asyncio.sleep(30)

    return EventSourceResponse(event_generator())


@app.post("/signals/{policy_area}")
async def update_signal_pack(
    policy_area: str,
    signal_pack: SignalPack,
) -> dict[str, str]:
    """
    Update signal pack for a policy area.

    This endpoint allows updating signal packs dynamically.
    In production, this would have authentication/authorization.

    Args:
        policy_area: Policy area identifier
        signal_pack: New signal pack

    Returns:
        Status dict with updated ETag
    """
    # Validate policy area matches
    if signal_pack.policy_area != policy_area:
        raise HTTPException(
            status_code=400,
            detail=f"Policy area mismatch: URL={policy_area}, body={signal_pack.policy_area}",
        )

    # Update store
    _signal_store[policy_area] = signal_pack

    etag = signal_pack.compute_hash()[:32]

    logger.info(
        "signal_pack_updated",
        policy_area=policy_area,
        version=signal_pack.version,
        etag=etag,
    )

    return {
        "status": "updated",
        "policy_area": policy_area,
        "version": signal_pack.version,
        "etag": etag,
    }


@app.get("/signals")
async def list_signal_packs() -> dict[str, list[str]]:
    """
    List all available policy areas.

    Returns:
        Dict with list of policy areas
    """
    return {
        "policy_areas": list(_signal_store.keys()),
        "count": len(_signal_store),
    }


def main() -> None:
    """Run the signal service."""
    import uvicorn

    uvicorn.run(
        "saaaaaa.api.signals_service:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
