import re
from typing import Any
from app.agents.request_analysis import analyze_request, extract_all_durations_weeks

APPOINTMENT_REQUIRED_SECTIONS = (
    "Executive summary", "Business objectives", "Target users", "Scope and exclusions",
    "Key features", "Technology considerations", "Four-week implementation timeline",
    "Risks and mitigations", "Estimated roles and effort", "Measurable success criteria",
    "Assumptions and next steps",
)
RECOVERY_REQUIRED_SECTIONS = (
    "Situation and objective", "Priority work and dependencies", "Revised two-week schedule",
    "Risks and mitigations", "Go/no-go criteria and decision points", "Missing information", "Success measures",
)

def validate_content(request: str, title: str, document_type: str, objective: str, assumptions: list[str], content: dict[str, Any]) -> dict[str, Any]:
    analysis = analyze_request(request)
    issues: list[str] = []
    if not isinstance(content, dict) or not content:
        return {"valid": False, "issues": ["No document sections were produced"], "section_count": 0}
    if not _has_text(title) or not _has_text(document_type) or not _has_text(objective):
        issues.append("Document title, type, and objective must be non-empty")
    if analysis.kind == "appointment_proposal":
        if "recovery" in title.lower() or not all(word in title.lower() for word in ("appointment", "booking")):
            issues.append("Title is not relevant to the requested appointment-booking proposal")
        if "recovery" in document_type.lower():
            issues.append("Document type contradicts the requested project proposal")
        required_sections = tuple(
            (f"{_number_word(analysis.duration_weeks)}-week implementation timeline" if analysis.duration_weeks else "Implementation timeline")
            if section == "Four-week implementation timeline" else section
            for section in APPOINTMENT_REQUIRED_SECTIONS
        )
    elif analysis.kind == "chatbot_recovery":
        if "recovery" not in title.lower() or "chatbot" not in title.lower():
            issues.append("Title is not relevant to the requested chatbot recovery plan")
        required_sections = RECOVERY_REQUIRED_SECTIONS
    else:
        required_sections = _requested_section_names(request)

    normalized = {_normalize(name): name for name in content}
    missing = [heading for heading in required_sections if _normalize(heading) not in normalized]
    if missing:
        issues.append("Missing required sections: " + ", ".join(missing))

    for heading, value in content.items():
        if not _has_content(value):
            issues.append(f"Empty section: {heading}")
        elif len(" ".join(_flatten(value)).strip()) < 24 or _contains_placeholder(value):
            issues.append(f"Section lacks substantive content: {heading}")
        elif _normalize(request) and _normalize(request) in _normalize(" ".join(_flatten(value))):
            issues.append(f"Section repeats the complete user request instead of answering it: {heading}")

    duration = analysis.duration_weeks
    if duration:
        timeline = _timeline_text(content)
        if not timeline:
            issues.append("Missing timeline content")
        else:
            missing_weeks = [week for week in range(1, duration + 1) if not re.search(rf"\bweek\s*{week}\b", timeline, re.IGNORECASE)]
            if missing_weeks:
                week_list = ", ".join(str(week) for week in missing_weeks)
                issues.append(f"Timeline must explicitly cover every requested week; missing Week(s): {week_list}")
        explicit_durations = extract_all_durations_weeks(" ".join([title, document_type, objective, *_flatten(assumptions), *_flatten(content)]))
        if any(value != duration for value in explicit_durations):
            issues.append(f"Timeline or section content contradicts the requested {duration}-week duration")
        if _has_contradictory_duration(assumptions, duration):
            issues.append(f"Assumptions contradict the requested {duration}-week duration")

    if analysis.kind == "appointment_proposal":
        _validate_appointment_sections(content, issues)

    return {"valid": not issues, "issues": issues, "section_count": len(content)}

def _requested_section_names(request: str) -> tuple[str, ...]:
    lower = request.lower()
    aliases = (
        (("objective", "objectives", "goal"), "Objectives"),
        (("target user", "audience", "stakeholder"), "Target users"),
        (("scope", "exclusion"), "Scope and exclusions"),
        (("feature", "capabilit"), "Key features"),
        (("technology", "technical", "platform"), "Technology considerations"),
        (("timeline", "schedule", "week", "deadline"), "Timeline"),
        (("risk", "mitigation"), "Risks and mitigations"),
        (("resource", "role", "effort", "staffing"), "Estimated roles and effort"),
        (("success criteria", "success metric", "measure", "kpi"), "Measurable success criteria"),
        (("executive summary", "overview"), "Executive summary"),
    )
    selected = [heading for needles, heading in aliases if any(needle in lower for needle in needles)]
    return tuple(dict.fromkeys(selected))

def _timeline_text(content: dict[str, Any]) -> str:
    values = [value for heading, value in content.items() if "timeline" in heading.lower() or "schedule" in heading.lower()]
    return " ".join(_flatten(values))

def _flatten(value: Any) -> list[str]:
    if isinstance(value, dict):
        output: list[str] = []
        for key, item in value.items():
            output.append(str(key))
            output.extend(_flatten(item))
        return output
    if isinstance(value, (list, tuple)):
        return [text for item in value for text in _flatten(item)]
    return [str(value)] if value is not None else []

def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value) and all(_has_content(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return bool(value) and all(_has_content(item) for item in value)
    return True

def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

def _has_contradictory_duration(assumptions: list[str], requested: int) -> bool:
    return any(value != requested for item in assumptions for value in extract_all_durations_weeks(item))

def _number_word(value: int) -> str:
    words = {1:"One", 2:"Two", 3:"Three", 4:"Four", 5:"Five", 6:"Six", 7:"Seven", 8:"Eight", 9:"Nine", 10:"Ten", 11:"Eleven", 12:"Twelve"}
    return words.get(value, str(value))

def _validate_appointment_sections(content: dict[str, Any], issues: list[str]) -> None:
    normalized = {_normalize(name): value for name, value in content.items()}
    checks = {
        "Target users": (r"customer|client|staff|provider|user|administrator", "Target users must identify plausible user groups"),
        "Key features": (r"booking|availability|calendar|notification|reschedul|cancel", "Key features must describe booking capabilities"),
        "Technology considerations": (r"application|database|hosting|security|technology|platform|integration|stack", "Technology considerations must discuss implementation choices"),
        "Estimated roles and effort": (r"illustrative|estimate", "Roles and effort must be labelled as illustrative estimates"),
        "Measurable success criteria": (r"proposed target|proposed measure|target", "Success criteria must be labelled as proposed targets"),
    }
    for heading, (pattern, message) in checks.items():
        value = normalized.get(_normalize(heading))
        if value is not None and not re.search(pattern, " ".join(_flatten(value)), re.IGNORECASE):
            issues.append(message)
    target_text = " ".join(_flatten(normalized.get(_normalize("Measurable success criteria"), "")))
    if target_text and not re.search(r"\d|%|under|less than|zero", target_text, re.IGNORECASE):
        issues.append("Success criteria must include at least one measurable proposed target")

def _contains_placeholder(value: Any) -> bool:
    text = " ".join(_flatten(value))
    return bool(re.search(r"\b(?:todo|tbd|lorem ipsum|fill this in|to be determined|n/?a)\b", text, re.IGNORECASE))
