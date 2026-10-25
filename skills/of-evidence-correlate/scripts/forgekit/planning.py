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


PHASES = ("intake", "extract", "compare", "cite", "conclude")
INPUTS = ("selected_originals", "coherent_copy", "derived_text", "dated_captures", "clock_context", "precise_locators")
STOP_REASONS = ("question_answered", "scope_exhausted", "operator_stopped")
PHASE_ACTIONS = {
    "intake": ("Confirm the question, selected originals, provenance and processing limits", "of-case-start", "Selected originals and recorded provenance"),
    "extract": ("Derive only the fields needed for the question and retain the extraction context", None, "Bounded derived observations with source locators"),
    "compare": (None, None, "Comparison including a plausible competing explanation and conflicting observations"),
    "cite": ("Check every proposed excerpt against its registered original or declared derivation", "of-investigation-report", "Checked locators and explicit unresolved citation limits"),
    "conclude": ("State the supported finding, unresolved alternatives and stopping decision", "of-hypothesis-audit", "Evidence-linked finding with limits and the next useful discriminating check"),
}


def plan(kinds=None, request=None, case=None):
    if case is not None:
        from .snapshot import verified_case
        with verified_case(case):
            return _plan(kinds, request, case)
    return _plan(kinds, request, case)


def _plan(kinds=None, request=None, case=None):
    from .assurance import case_status, text
    request = {} if request is None else request
    require(isinstance(request, dict) and set(request) <= {"question", "kinds", "available", "authorized", "max_steps", "deferred_leads",
            "resume_from", "completed_steps", "available_inputs", "stop_reason", "specialize"}, "INVALID_PLAN_REQUEST")
    raw_selected = kinds if kinds is not None else request.get("kinds", [])
    require(isinstance(raw_selected, (list, tuple)), "INVALID_PLAN_KINDS")
    selected = list(raw_selected)
    require(0 < len(selected) <= 4 and all(isinstance(kind, str) and kind in ROUTES for kind in selected)
            and len(set(selected)) == len(selected), "INVALID_PLAN_KINDS")
    require(kinds is None or "kinds" not in request, "AMBIGUOUS_PLAN_INPUT")
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
    resume = request.get("resume_from", "intake")
    require(isinstance(resume, str) and resume in PHASES, "INVALID_PLAN_PHASE")
    completed = request.get("completed_steps", [])
    identifiers = {kind + ":" + phase for kind in selected for phase in PHASES}
    require(isinstance(completed, list) and len(completed) <= 20
            and all(isinstance(value, str) and value in identifiers for value in completed)
            and len(set(completed)) == len(completed), "INVALID_COMPLETED_STEPS")
    supplied = request.get("available_inputs")
    require(supplied is None or isinstance(supplied, list) and len(supplied) <= len(INPUTS)
            and all(isinstance(value, str) and value in INPUTS for value in supplied)
            and len(set(supplied)) == len(supplied), "INVALID_PLAN_INPUTS")
    stop = request.get("stop_reason")
    require(stop is None or isinstance(stop, str) and stop in STOP_REASONS, "INVALID_PLAN_STOP")
    specialize = request.get("specialize", False)
    require(type(specialize) is bool, "INVALID_PLAN_SPECIALIZATION")
    runnable = [value for value in available if value in authorized]
    candidates = []
    for phase in PHASES[PHASES.index(resume):]:
        for kind in selected:
            identifier = kind + ":" + phase
            if identifier in completed:
                continue
            action, skill, deliverable = PHASE_ACTIONS[phase]
            comparison, discriminant, inputs = STEPS[kind]
            previous = [] if phase == "intake" else [kind + ":" + PHASES[PHASES.index(phase) - 1]]
            needed = ["selected_originals"] if phase == "intake" else ["precise_locators"] if phase == "cite" else []
            if phase == "extract" and kind in ("browser", "windows-export", "logs", "agent-export"):
                needed = ["coherent_copy", "clock_context"]
            if phase == "compare" and kind in ("media", "domain", "organization", "versions"):
                needed = ["dated_captures"]
            missing_inputs = [item for item in needed if supplied is not None and item not in supplied]
            state = "capability_gap" if "local" not in runnable else "input_gap" if missing_inputs else "planned"
            candidates.append({"id": identifier, "kind": kind, "phase": phase, "question": question,
                "action": action or comparison, "discriminating_check": discriminant,
                "required_input": inputs, "required_inputs": needed, "missing_inputs": missing_inputs,
                "prerequisites": previous, "prerequisites_completed": all(item in completed for item in previous),
                "input_status": "operator_check_required" if supplied is None else "declared",
                "required_capabilities": ["local"], "skill": skill or ROUTES[kind][0],
                "deliverable": deliverable, "state": state})
    steps = [] if stop else candidates[:limit]
    prior = {}
    for index, row in enumerate(steps):
        row["step"] = index + 1
        ready = all(item in completed or prior.get(item) == "planned" for item in row["prerequisites"])
        row["prerequisite_status"] = "completed_as_declared" if row["prerequisites_completed"] else "scheduled_before" if ready else "missing_or_blocked"
        if row["state"] == "planned" and not ready:
            row["state"] = "prerequisite_gap"
        prior[row["id"]] = row["state"]
    status = case_status(case) if case else None
    case_gaps = []
    if status:
        if status["needs_review"]:
            case_gaps.append({"kind": "dependency_review", "count": status["needs_review"], "skill": "of-hypothesis-audit"})
        declared = status["coverage"]
        missing = declared["defined_categories"] - declared["completed_categories"]
        if missing:
            case_gaps.append({"kind": "coverage_gap", "count": missing, "skill": "of-hypothesis-audit"})
        if not declared["requirements"]:
            case_gaps.append({"kind": "coverage_undefined", "count": 1, "skill": "of-case-start"})
        from .queue import review_queue
        queue = review_queue(case, min(limit, 20))
        review_steps = []
        for index, task in enumerate(queue["tasks"]):
            phase = "cite" if task["kind"].startswith("citation_") else "intake" if task["kind"] in (
                "evidence_missing", "coverage_undefined") else "compare"
            review_steps.append({"id": "review:" + task["kind"] + ":" + str(index + 1), "kind": selected[0],
                "phase": phase, "question": question, "action": task["next_check"], "skill": task["skill"],
                "deliverable": "Resolved recorded gap or explicit retained limitation", "references": task["references"],
                "required_inputs": [], "required_capabilities": ["local"], "prerequisites": [],
                "prerequisites_completed": True, "prerequisite_status": "completed_as_declared",
                "state": "planned" if "local" in runnable else "capability_gap", "source": "recorded_case_gap"})
        if not stop:
            candidates = review_steps + candidates
            steps = candidates[:limit]
            for index, row in enumerate(steps):
                row["step"] = index + 1
    chosen = list(dict.fromkeys(row["kind"] for row in steps))
    tasks = []
    if specialize and not stop:
        for kind in chosen:
            tasks.append({"id": "inspect:" + kind, "role": "material_specialist", "kind": kind,
                          "skill": ROUTES[kind][0], "access": "read_only", "may_write_case": False,
                          "depends_on": [], "deliverable": "Evidence-linked observations and conflicting explanations"})
        tasks.append({"id": "challenge", "role": "independent_reviewer", "skill": "of-hypothesis-audit",
                      "access": "read_only", "may_write_case": False, "depends_on": [],
                      "deliverable": "Independently test a competing explanation against the selected originals"})
        tasks.append({"id": "integrate", "role": "case_writer", "skill": "of-investigation-report",
                      "access": "operator_controlled", "may_write_case": True,
                      "depends_on": [row["id"] for row in tasks],
                      "deliverable": "Review proposed findings, then append only operator-authorized records"})
    omitted = candidates if stop else candidates[len(steps):]
    return {"kind": selected[0] if len(selected) == 1 else None, "candidate_kinds": selected,
            "question": question, "requires_scope_question": question is None,
            "ambiguity": "Keep all proposed readings; resolve against the recorded question before collection" if len(selected) > 1 else None,
            "start": "of-case-start", "selected_skills": list(dict.fromkeys(skill for kind in chosen for skill in ROUTES[kind])),
            "review": ["of-hypothesis-audit", "of-investigation-report"], "steps": steps,
            "deferred_kinds": [kind for kind in selected if kind not in chosen], "deferred_leads": deferred,
            "deferred_steps": [row["id"] for row in omitted], "completed_steps_as_declared": completed,
            "resume_from": resume, "next_step": omitted[0]["id"] if omitted else None,
            "action_budget": {"limit": limit, "planned": len(steps), "remaining": len(omitted)},
            "state": "stopped" if stop else "complete_as_declared" if not candidates else "planned",
            "stop_reason": stop, "available": available, "authorized_as_declared": authorized,
            "usable_as_declared": runnable, "missing_capabilities": [value for value in authorized if value not in available],
            "unapproved_capabilities": [value for value in available if value not in authorized],
            "case_review": status, "case_gaps": case_gaps, "specialist_tasks": tasks,
            "specialization": {"advisory_only": True, "spawned": False, "maximum_case_writers": 1,
                "independence": "Separate model tasks are not independent evidence; review source origins separately"},
            "stop_conditions": ["Question answered within scope", "Action budget exhausted",
                "Required capability or evidence absent", "Remaining observations cannot discriminate hypotheses"],
            "loading": "Read only the selected skill and references needed for the current step",
            "executed": False, "network_authorized": False,
            "limits": "Declared inputs, completed steps and capabilities are not verified host state or permission to install, write or transmit data"}
