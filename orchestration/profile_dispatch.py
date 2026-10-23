"""Dispatch of an existing LAB analysis_jobs PROFILE job to XPS.

No queue, no independent claim, no scientific code on the orchestrator.
"""
from __future__ import annotations

from contracts.job import JobEnvelope
from contracts.target import Target
from transport.api import ApiClient
from transport.targets import TargetRegistry

KEYS = {
    "duree": "duration", "tempo": "tempo", "mesure": "meter",
    "tonalite": "key", "genre": "genre", "instruments": "instrument:0",
    "voix_principale": "lead_vocal", "voix_accompagnement": "backing_vocals",
    "harmonies_vocales": "vocal_harmonies", "choeurs": "choir",
}


def dispatch(job: JobEnvelope, registry: TargetRegistry, *, xps_url: str):
    if job.target is not Target.LAB or job.kind != "assistant.profile.review":
        raise ValueError("unsupported_dispatch_job")
    payload = job.request.get("expertise_payload")
    if not isinstance(payload, dict) or payload.get("expertise_type") != "profile":
        raise ValueError("profile_payload_required")
    if not xps_url or not xps_url.startswith(("http://", "https://")):
        raise ValueError("assistant_xps_url_required")
    endpoint = registry.endpoint(Target.LAB)
    response = ApiClient(xps_url, endpoint.token).post(
        "/api/profile/verify", payload, timeout=900.0)
    if not isinstance(response, dict) or response.get("analysis_id") != payload.get("analysis_id") \
            or response.get("expertise_type") != payload["expertise_type"] \
            or response.get("preset_id") != payload.get("preset_id"):
        raise RuntimeError("profile_response_identity_mismatch")
    rows = response.get("reviews")
    if not isinstance(rows, dict) or set(rows) != set(KEYS):
        raise RuntimeError("profile_response_items_invalid")
    assertions = []
    sources = set()
    for name, key in KEYS.items():
        row = rows[name]
        if not isinstance(row, dict) or row.get("verdict") not in (
                "bon", "faux", "non_trouve", "sans_valeur_lab"):
            raise RuntimeError("profile_response_verdict_invalid")
        urls = row.get("consulted_urls") or []
        if not isinstance(urls, list) or any(not isinstance(u, str) for u in urls):
            raise RuntimeError("profile_response_sources_invalid")
        sources.update(urls)
        assertions.append({
            "key": key, "value": payload["items"][name],
            "verdict": row["verdict"], "reason": row.get("reason"),
            "reference_value": row.get("reference_value"),
            "citations": [u for u in urls if u.startswith("https://")],
        })
    review = {
        "run_id": payload["analysis_id"],
        "revision_key": "profile-%d-assistant-push-v1" % payload["analysis_id"],
        "reviewer": "assistant-xps", "status": "draft", "confidence": 0,
        "identity": {"title": payload["title"], "artist": payload["artist"],
                     "identity_confirmed": bool(response.get("identity_confirmed"))},
        "sources": [{"name": "Web consulté", "url": u} for u in sorted(sources)],
        "comparison": {"final_verification": {"assertions": assertions}},
        "consensus": {"technical_status": response.get("technical_status"),
                      "technical_errors": response.get("technical_errors")},
    }
    submitted = endpoint.client().post(
        "/internal/analysis/desktop/profile/reviews", review, timeout=30)
    if not isinstance(submitted, dict) or submitted.get("ok") is not True:
        raise RuntimeError("profile_lab_persistence_failed")
    return submitted
