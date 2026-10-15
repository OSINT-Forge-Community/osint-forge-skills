from __future__ import annotations

from copy import deepcopy

from .safeio import require

CARDS = (
    ("inpi-rne", "DATA INPI / RNE", "INPI", "organization", "FR", ["fr", "en"],
     "https://data.inpi.fr/", "Name, SIREN and supplied filing identifiers", "Company register extracts and filings",
     "Record filing and effective dates separately; coverage depends on the selected record",
     "A filed role does not establish current ownership; distinguish brands and legal entities"),
    ("bodacc", "BODACC", "DILA", "organization", "FR", ["fr"],
     "https://www.bodacc.fr/", "Company name, SIREN or announcement reference", "Published civil and commercial announcements",
     "An announcement describes its publication and stated event; later changes need separate records",
     "Publication does not establish implementation or an exhaustive current corporate profile"),
    ("gleif", "GLEIF LEI data", "GLEIF", "organization", "GLOBAL", ["en", "fr"],
     "https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy", "LEI and legal entity reference data",
     "LEI identities, accounting parent relationships and reporting exceptions",
     "Retain record status, reporting period and snapshot date",
     "Accounting parent relationships are not a complete beneficial-ownership register; exceptions and missing LEIs matter"),
    ("companies-house", "Companies House register", "Companies House", "organization", "GB", ["en"],
     "https://find-and-update.company-information.service.gov.uk/", "Company number or name", "UK company filings and register entries",
     "Use filing dates and historical roles; select the period required by the question",
     "The register warns that it does not check the accuracy of filed information"),
    ("ted", "TED procurement notices", "Publications Office of the European Union", "organization", "EU", ["en", "fr"],
     "https://docs.ted.europa.eu/api/latest/search.html", "Notice reference, organization and publication filters",
     "Published procurement notices", "Notice types and dates distinguish planning, award and changes",
     "A notice or award is not evidence that a contract was implemented or paid"),
    ("rdap", "RDAP guidance", "ICANN", "domain", "GLOBAL", ["en", "fr"],
     "https://www.icann.org/rdap", "Exact domain and its authoritative registry", "Registration data and authoritative service discovery",
     "Current responses are observations; interpret each event action and timestamp separately",
     "Redacted fields are unknown; registrar, registrant, DNS and hosting roles are distinct"),
    ("wayback", "Wayback Machine guidance", "Internet Archive", "archive", "GLOBAL", ["en"],
     "https://help.archive.org/help/using-the-wayback-machine/", "Exact public URL and selected capture date",
     "Available archived captures", "Archive time, source publication time and acquisition time are distinct",
     "Missing captures do not prove absence; incomplete resources can alter presentation; saving publicly is a separate transmission"),
    ("copernicus", "Copernicus Browser", "Copernicus Data Space Ecosystem", "imagery", "GLOBAL", ["en"],
     "https://documentation.dataspace.copernicus.eu/Applications/Browser.html", "Public area, date window and imagery collection",
     "Selected Earth observation imagery", "Record acquisition date, collection and processing context",
     "Resolution, clouds, season and viewing geometry limit visual comparison; no identification from a generic resemblance"),
    ("nominatim", "Nominatim usage policy", "OpenStreetMap Foundation", "imagery", "GLOBAL", ["en"],
     "https://operations.osmfoundation.org/policies/nominatim/", "Public place name or coarse area", "Place-name geocoding under service policy",
     "A geocoding response is a current database observation, not an image date",
     "A name match is a candidate, not a location verification; review rate limits and restrictions before any use"),
)


def source_cards(category=None, jurisdiction=None):
    require(category is None or category in ("organization", "domain", "archive", "imagery"), "INVALID_SOURCE_CATEGORY")
    require(jurisdiction is None or isinstance(jurisdiction, str) and 0 < len(jurisdiction) <= 20, "INVALID_JURISDICTION")
    cards = []
    for values in CARDS:
        identifier, name, publisher, kind, region, languages, url, accepts, scope, temporal, limits = values
        if category and kind != category or jurisdiction and region != jurisdiction.upper():
            continue
        cards.append({"id": identifier, "name": name, "publisher": publisher, "category": kind,
            "jurisdiction": region, "languages": deepcopy(languages), "documentation_url": url,
            "accepts": accepts, "coverage": scope, "temporal_scope": temporal, "limits": limits,
            "reviewed_at": "2026-10-15", "qualification": "documentation_reviewed_not_api_tested",
            "access": "Check the linked provider documentation, account requirements and terms before use",
            "data_leaving_case": "Selected query identifiers, filters and request metadata would reach the provider",
            "observability": "Third-party provider observes consultation; linked target resources may create direct contact",
            "upload_authorized": False, "network_tested": False,
            "synthetic_example": "Harbor Example Ltd is a synthetic name; resolve an exact identifier before drawing a relationship"})
    return {"sources": cards, "network_calls": False, "installation_required": False,
            "policy": "Static reference cards; neither availability nor authorization is inferred"}
