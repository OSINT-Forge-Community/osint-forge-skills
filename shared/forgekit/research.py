from __future__ import annotations

from copy import deepcopy
import re
import unicodedata

from .safeio import require

PIVOTS = {
    "domain": (
        "A selected DNS, RDAP or certificate observation contains an exact domain",
        "Record the full domain, record type, source and observation time",
        "Compare registration events, DNS roles and dated certificate names before proposing a relationship",
        "Dated infrastructure inventory with separate registrar, registrant, DNS and hosting roles",
        "Shared hosting, an IP match or a certificate name does not establish a common operator",
        "Stop if the remaining step requires scanning, enumeration or an unapproved provider",
        "of-domain-infrastructure"),
    "organization": (
        "A supplied filing names a legal entity or related organization",
        "Resolve jurisdiction and an exact registry identifier; preserve the effective period",
        "Compare the cited filing with a dated record for the candidate entity and relationship",
        "Candidate entity or relation with identifier, period, evidence references and matching criteria",
        "A brand, namesake, address or officer match does not establish ownership or control",
        "Stop at ambiguous identifiers, inaccessible records or relationships outside the scoped question",
        "of-organization-research"),
    "publication": (
        "Several selected reports repeat the same statement or media",
        "Retain exact passages, source URLs, publication dates and acquisition dates",
        "Trace the cited original and test whether later reports contain independent observations",
        "Origin map distinguishing copies, independent observations and unavailable originals",
        "Repeated coverage, an earlier visible date or a search snippet does not establish independence",
        "Stop when the origin is unavailable; record the gap instead of counting copies as confirmation",
        "of-source-provenance"),
    "document": (
        "A selected document contains a producer, author field or embedded URL",
        "Preserve original bytes and the extraction tool, version and field locator",
        "Compare the field with separately selected dated records relevant to the question",
        "Field-level observation and alternative explanations such as templates, export defaults or copied metadata",
        "Editable metadata or a username string does not identify the author or prove execution",
        "Stop before following embedded links, running macros or querying private identity services",
        "of-document-triage"),
    "media": (
        "A visible public-place feature suggests a candidate scene",
        "Keep image provenance, date uncertainty and a competing location hypothesis",
        "Compare a discriminating feature across candidate scenes, viewpoints and possible mirrored images",
        "Candidate comparison with matching and conflicting features linked to selected captures",
        "A generic resemblance or geocoder result does not verify a location or a person's presence",
        "Stop when resolution or viewpoint prevents discrimination, or a step would expose private whereabouts",
        "of-geolocation"),
    "agent-export": (
        "A supplied normalized agent export reports a tool call or external effect",
        "Keep the event locator, tool-call identifier, reported result and exporter context",
        "Compare the claimed effect with separately supplied host observations and original artifacts",
        "Event timeline separating requests, reported results, observed artifacts and unresolved effects",
        "Model narration, a successful-looking return or a matching hash does not prove an external action",
        "Stop at missing host evidence; never replay recorded calls or collect a live profile",
        "of-agent-artifacts"),
}
QUERY_KINDS = ("domain", "organization", "publication")


def pivots(kind=None):
    require(kind is None or isinstance(kind, str) and kind in PIVOTS, "INVALID_PIVOT_KIND")
    rows = []
    for name, values in PIVOTS.items():
        if kind and name != kind:
            continue
        rows.append(dict(zip(("trigger", "prerequisite", "next_check", "deliverable", "non_inference", "stop", "skill"), values),
                         kind=name, reviewed_at="2026-10-15"))
    return {"pivots": deepcopy(rows), "executed": False, "network_calls": False,
            "policy": "Advisory checks within the existing question; record a lead before any separately authorized collection"}


def domain_name(value):
    require(isinstance(value, str) and 0 < len(value) <= 253, "INVALID_QUERY_DOMAIN")
    try:
        name = value.encode("idna").decode("ascii").lower()
    except UnicodeError:
        require(False, "INVALID_QUERY_DOMAIN")
    labels = name.split(".")
    require(len(name) <= 253 and len(labels) >= 2 and not labels[-1].isdigit()
            and all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels),
            "INVALID_QUERY_DOMAIN")
    return name


def query_templates(kind, value, site=None):
    require(isinstance(kind, str) and kind in QUERY_KINDS, "INVALID_QUERY_KIND")
    require(isinstance(value, str) and 0 < len(value) <= 200 and value == value.strip()
            and not any(unicodedata.category(char).startswith("C") or char in '\\"\u2028\u2029' for char in value),
            "INVALID_QUERY_VALUE")
    term = domain_name(value) if kind == "domain" else value
    site_filter = "site:" + domain_name(site) + " " if site is not None else ""
    suffixes = {"domain": ("", "DNS", "certificate"),
                "organization": ("", "registry", "filing"),
                "publication": ("", "correction", "original")}[kind]
    return {"kind": kind, "queries": [{"query": site_filter + '"' + term + '"' + (" " + suffix if suffix else ""),
                                      "purpose": suffix or "exact phrase"} for suffix in suffixes],
            "executed": False, "network_calls": False,
            "limits": ["Review identifiers and scope before submitting a query through an authorized host tool",
                       "The search provider receives the submitted terms; query syntax and coverage vary",
                       "Results and snippets are leads; preserve and check the original source",
                       "No result does not establish absence; no email, breach or credential enumeration is performed"]}
