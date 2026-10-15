from __future__ import annotations

from .safeio import require

ROUTES = {
    "documents": ["of-document-triage", "of-source-provenance"],
    "media": ["of-media-forensics", "of-geolocation"],
    "domain": ["of-domain-infrastructure", "of-source-provenance"],
    "organization": ["of-organization-research", "of-source-provenance"],
    "versions": ["of-version-compare", "of-source-provenance"],
    "windows-export": ["of-windows-artifacts", "of-log-timeline"],
    "browser": ["of-browser-artifacts", "of-evidence-correlate"],
    "logs": ["of-log-timeline", "of-evidence-correlate"],
    "agent-export": ["of-agent-artifacts", "of-evidence-correlate"],
}
CAPABILITIES = ("local", "search", "fetch", "maps", "image_upload", "exiftool", "pdftotext", "tesseract", "ffprobe")
STEPS = {
    "documents": ("Compare the selected passage with its original and extraction context", "Which exact passage supports the claim?", "Selected pages or text export"),
    "media": ("Test the strongest plausible competing scene and viewpoint", "Which visible feature would distinguish the candidates?", "Selected image and dated independent map or scene captures"),
    "domain": ("Compare registry, DNS and certificate roles at their observation dates", "Does a recorded identifier establish the proposed relationship?", "Exact domain and dated DNS/RDAP/certificate captures"),
    "organization": ("Compare legal identifiers, jurisdictions and effective periods", "Can namesakes be distinguished using a registry identifier?", "Selected registry extracts and dated filings"),
    "versions": ("Compare the same passage in both versions and inspect extraction differences", "Is this a content change or an extraction difference?", "Two unchanged versions with derivation context"),
    "windows-export": ("Map source columns and separate artifact observation from execution", "Does this artifact establish execution, or only inventory?", "Selected CSV, parser version, options and clock context"),
    "browser": ("Check copy completeness and correlate only relevant recorded visits", "Is the visit independently linked to the question?", "Coherent supplied SQLite copy and acquisition context"),
    "logs": ("Compare original records while retaining uncertain times", "Could filtering or clock uncertainty explain the apparent sequence?", "Selected structured events and exporter context"),
    "agent-export": ("Separate model text, tool requests, reported results and host observations", "Is the claimed effect corroborated outside the agent narrative?", "Selected normalized event export and any separately supplied host evidence"),
}


def plan(kinds=None, request=None, case=None):
    from .assurance import case_status, text
    request = {} if request is None else request
    require(isinstance(request, dict) and set(request) <= {"question", "kinds", "available", "authorized", "max_steps", "deferred_leads"},
            "INVALID_PLAN_REQUEST")
    selected = list(kinds or request.get("kinds", []))
    require(0 < len(selected) <= 4 and all(isinstance(kind, str) and kind in ROUTES for kind in selected)
            and len(set(selected)) == len(selected), "INVALID_PLAN_KINDS")
    require(not kinds or "kinds" not in request, "AMBIGUOUS_PLAN_INPUT")
    question = request.get("question")
    if question is not None:
        text(question, 4000, "INVALID_PLAN_QUESTION")
    available, authorized = request.get("available", ["local"]), request.get("authorized", ["local"])
    for values in (available, authorized):
        require(isinstance(values, list) and len(values) <= len(CAPABILITIES)
                and all(isinstance(value, str) and value in CAPABILITIES for value in values)
                and len(set(values)) == len(values), "INVALID_PLAN_CAPABILITIES")
    limit = request.get("max_steps", 4)
    require(type(limit) is int and 1 <= limit <= 20, "INVALID_PLAN_BUDGET")
    deferred = request.get("deferred_leads", [])
    require(isinstance(deferred, list) and len(deferred) <= 20, "INVALID_DEFERRED_LEADS")
    for lead in deferred:
        text(lead, 1000, "INVALID_DEFERRED_LEADS")
    runnable = [value for value in available if value in authorized]
    steps = []
    for index, kind in enumerate(selected[:limit]):
        action, discriminant, inputs = STEPS[kind]
        steps.append({"step": index + 1, "kind": kind, "question": question,
                      "action": action, "discriminating_check": discriminant,
                      "required_input": inputs, "skill": ROUTES[kind][0],
                      "deliverable": "Evidence-linked observation, unresolved alternatives and next useful check",
                      "state": "planned" if "local" in runnable else "capability_gap"})
    status = case_status(case) if case else None
    return {"kind": selected[0] if len(selected) == 1 else None, "candidate_kinds": selected,
            "question": question, "requires_scope_question": question is None,
            "ambiguity": "Keep all proposed readings; resolve against the recorded question before collection" if len(selected) > 1 else None,
            "start": "of-case-start", "selected_skills": list(dict.fromkeys(skill for kind in selected[:limit] for skill in ROUTES[kind])),
            "review": ["of-hypothesis-audit", "of-investigation-report"], "steps": steps,
            "deferred_kinds": selected[limit:], "deferred_leads": deferred,
            "available": available, "authorized_as_declared": authorized,
            "usable_as_declared": runnable, "missing_capabilities": [value for value in authorized if value not in available],
            "unapproved_capabilities": [value for value in available if value not in authorized],
            "case_review": status, "stop_conditions": ["Question answered within scope", "Budget exhausted",
                "Required capability or evidence absent", "Remaining observations cannot discriminate hypotheses"],
            "loading": "Read only the selected skill and references needed for the current step",
            "executed": False, "network_authorized": False,
            "limits": "Declared capabilities are not host enforcement or permission to install or transmit data"}
