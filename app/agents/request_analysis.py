import re
from dataclasses import dataclass

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
DURATION_PATTERN = re.compile(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*[- ]?\s*weeks?\b", re.IGNORECASE)

@dataclass(frozen=True)
class RequestAnalysis:
    document_type: str
    title: str
    objective: str
    topic: str
    duration_weeks: int | None
    kind: str

def extract_duration_weeks(request: str) -> int | None:
    values = extract_all_durations_weeks(request)
    return values[0] if values else None

def extract_all_durations_weeks(text: str) -> list[int]:
    values: list[int] = []
    for match in DURATION_PATTERN.finditer(text):
        raw = match.group(1).lower()
        value = int(raw) if raw.isdigit() else NUMBER_WORDS[raw]
        if value not in values:
            values.append(value)
    return values

def analyze_request(request: str) -> RequestAnalysis:
    text = " ".join(request.split())
    lower = text.lower()
    duration = extract_duration_weeks(text)

    if "appointment" in lower and ("booking" in lower or "scheduling" in lower):
        topic = "Online Appointment Booking System"
        document_type = "Project Proposal"
        kind = "appointment_proposal"
        objective = "Propose a practical four-week implementation for an online appointment booking system, with clear users, scope, features, technology choices, resourcing, risks, and measurable outcomes." if duration == 4 else f"Propose a practical implementation for {topic}, with clear users, scope, features, technology choices, resourcing, risks, and measurable outcomes{f' over {duration} weeks' if duration else ''}."
        title = f"Project Proposal: {topic}"
    elif "chatbot" in lower and ("recovery" in lower or "delayed" in lower or "launch" in lower):
        topic = "Customer Support Chatbot Launch"
        document_type = "Project Recovery Plan"
        kind = "chatbot_recovery"
        objective = f"Recover the delayed {topic.lower()} by agreeing a safe scope, prioritizing incomplete testing, and making an evidence-based launch decision{f' within {duration} weeks' if duration else ''}."
        title = f"Project Recovery Plan: {topic}"
    else:
        kind = "general"
        if "proposal" in lower:
            document_type = "Project Proposal"
        elif "recovery plan" in lower:
            document_type = "Project Recovery Plan"
        elif "plan" in lower:
            document_type = "Project Plan"
        else:
            document_type = "Business Document"
        topic = _infer_topic(text)
        title = f"{document_type}: {topic}" if topic else document_type
        objective = f"Prepare a {document_type.lower()} for {topic or 'the requested work'}, reflecting the stated requirements and constraints{f' over {duration} weeks' if duration else ''}."

    return RequestAnalysis(document_type, title[:180], objective[:1000], topic, duration, kind)

def _infer_topic(request: str) -> str:
    value = re.sub(r"^(please\s+)?(create|prepare|draft|write|develop|generate)\s+(a|an|the)\s+", "", request.strip(), flags=re.IGNORECASE)
    value = re.split(r"[.!?\n]", value, maxsplit=1)[0]
    value = re.sub(r"\s+(including|include|with objectives|covering)\b.*$", "", value, flags=re.IGNORECASE)
    value = value.strip(" ,;:")
    if len(value) > 100:
        value = value[:97].rsplit(" ", 1)[0] + "…"
    return value[:1].upper() + value[1:] if value else ""
