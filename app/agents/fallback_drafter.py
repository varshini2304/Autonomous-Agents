from typing import Any
from app.agents.request_analysis import RequestAnalysis, analyze_request
from app.schemas.agent import AgentPlan

def draft_fallback(request: str, plan: AgentPlan) -> dict[str, Any]:
    analysis = analyze_request(request)
    if analysis.kind == "appointment_proposal":
        return _appointment_proposal(plan, analysis)
    if analysis.kind == "chatbot_recovery":
        return _chatbot_recovery(analysis)
    return _general_document(request, plan, analysis)

def _appointment_proposal(plan: AgentPlan, analysis: RequestAnalysis) -> dict[str, Any]:
    weeks = analysis.duration_weeks or 4
    duration_label = f"{_number_word(weeks)}-week" if weeks <= 12 else f"{weeks}-week"
    timeline_heading = f"{duration_label} implementation timeline" if analysis.duration_weeks else "Implementation timeline"
    timeline_context = f"the requested {weeks}-week" if analysis.duration_weeks else f"an illustrative {weeks}-week"
    milestones = [
        "Discovery and foundation: confirm user journeys, policies, services, acceptance criteria, data fields, and technical decisions; establish the application skeleton and environments.",
        "Booking core: implement service availability, slot selection, booking creation, conflict prevention, and staff schedule views; review the flow with representative users.",
        "Complete workflows: add confirmations, reminders, rescheduling/cancellation, administration, permissions, responsive polish, and automated tests for critical paths.",
        "Readiness and release: run end-to-end, accessibility, security, and operational checks; fix launch blockers, train staff, prepare rollback, and release in a controlled manner.",
    ]
    timeline = []
    for week in range(1, weeks + 1):
        phase = min(int((week - 1) * len(milestones) / weeks), len(milestones) - 1)
        timeline.append(f"Week {week} — {milestones[phase]}")
    return {
        "Executive summary": [
            f"This proposal outlines {timeline_context} first release for the {analysis.topic.lower()}. It focuses on making appointment discovery, booking, and schedule management straightforward for customers and staff.",
            "The scope, roles, effort, and performance targets below are planning estimates for stakeholder review; no company-specific operating data was supplied.",
        ],
        "Business objectives": [
            "Let customers view service availability and request or confirm appointments online.",
            "Reduce avoidable manual coordination by giving staff a shared view of bookings and changes.",
            "Provide timely confirmations and reminders while keeping customer and appointment data appropriately protected.",
        ],
        "Target users": [
            "Customers or clients who need to find an available time and manage their own booking.",
            "Service providers or staff who publish availability and review their schedules.",
            "An administrator who manages services, opening hours, access, and operational settings.",
            "These user groups are a practical starting point and should be confirmed with the business.",
        ],
        "Scope and exclusions": {
            "Included in the proposed first release": [
                "Responsive booking flow, service and availability display, booking confirmation, rescheduling, and cancellation.",
                "Staff schedule and appointment management, basic administrative configuration, and email notifications.",
                "Access control, input validation, audit-relevant events, and a tested deployment with basic monitoring.",
            ],
            "Excluded unless approved separately": [
                "Native mobile applications, complex multi-location or multi-time-zone scheduling, and advanced workforce optimization.",
                "Payment processing, insurance or clinical records, third-party calendar synchronization, and custom analytics beyond basic reporting.",
            ],
        },
        "Key features": [
            "Service catalog with duration, description, and configurable availability.",
            "Availability search that prevents double booking and clearly handles unavailable slots.",
            "Booking confirmation plus cancellation and rescheduling links governed by configurable rules.",
            "Staff calendar with appointment details, status, and basic filtering.",
            "Email confirmations and reminders with delivery status and retry handling.",
            "Administrative controls for services, working hours, booking lead time, and cancellation windows.",
            "Accessible, mobile-responsive interface with clear validation and privacy notices.",
        ],
        "Technology considerations": [
            "Use a responsive web application first to support desktop and mobile browsers without separate native apps.",
            "Use a maintained backend framework and relational database with transactions or equivalent safeguards for slot reservation and double-booking prevention.",
            "Require encrypted transport, role-based access, secure session handling, input validation, backups, and a documented data-retention policy.",
            "Keep email delivery behind a replaceable service adapter; confirm hosting, data residency, identity, and integration choices with the business before implementation.",
            "These are options and decision criteria, not claims about the business's current technology stack.",
        ],
        timeline_heading: timeline,
        "Risks and mitigations": [
            "Double bookings or stale availability: use atomic reservation checks and test simultaneous booking attempts.",
            "Unclear cancellation and service rules: confirm policies and obtain owner sign-off during Week 1.",
            "Notification delivery failures: monitor delivery, retry transient failures, and provide a staff-visible booking record.",
            "Sensitive data exposure: minimize collected data, enforce least privilege, encrypt transport and backups, and review retention.",
            "Four-week schedule pressure: protect the core booking path and defer excluded integrations or advanced reporting through explicit decisions.",
        ],
        "Estimated roles and effort": [
            "Illustrative estimate only; validate against actual scope, team capacity, integrations, and quality requirements.",
            "Product owner/business representative: approximately 0.4–0.6 person-weeks per week for decisions and acceptance.",
            "Full-stack engineer: approximately 4 person-weeks; QA/test engineer: approximately 1.5–2 person-weeks, concentrated in Weeks 2–4.",
            "UX/design support: approximately 0.5–1 person-week; DevOps/security review: approximately 0.5 person-week.",
            "These are effort estimates, not named people, confirmed availability, or a cost quote.",
        ],
        "Measurable success criteria": [
            "Proposed target: at least 95% of test bookings complete successfully across agreed critical user journeys before release.",
            "Proposed target: zero confirmed double bookings in concurrency and regression tests for the release scope.",
            "Proposed target: at least 95% of confirmation messages are accepted by the configured email provider during a representative test run.",
            "Proposed target: customers can complete a standard booking in under three minutes in usability testing with representative participants.",
            "Proposed target: no unresolved critical security or accessibility defects at the release decision.",
            "Set production baselines and revise these proposed targets with stakeholders; they are not measured current performance.",
        ],
        "Assumptions and next steps": [
            f"The requested {weeks}-week period is the complete implementation horizon, with Week 1 beginning after project approval." if analysis.duration_weeks else f"A {weeks}-week implementation horizon is illustrative and requires stakeholder approval.",
            "The first release is a responsive web application and does not include payment processing or complex external integrations unless approved.",
            "Next: confirm services, booking rules, data/privacy requirements, decision owner, team capacity, hosting constraints, and acceptance targets.",
            f"Review scope at the end of Week 1 and make a release-readiness decision in Week {weeks} using the agreed test evidence.",
        ],
    }

def _number_word(value: int) -> str:
    words = {1:"One", 2:"Two", 3:"Three", 4:"Four", 5:"Five", 6:"Six", 7:"Seven", 8:"Eight", 9:"Nine", 10:"Ten", 11:"Eleven", 12:"Twelve"}
    return words.get(value, str(value))

def _chatbot_recovery(analysis: RequestAnalysis) -> dict[str, Any]:
    return {
        "Situation and objective": f"Recover delivery of the delayed {analysis.topic.lower()} within the stated two-week window by agreeing a safe minimum scope, closing critical quality gaps, and making an evidence-based go/no-go decision. No company-specific delivery or quality data was supplied.",
        "Priority work and dependencies": [
            "P0, Days 1–2: name the decision owner and approve the minimum launch scope; this gates test planning.",
            "P0, Days 2–6: inventory incomplete tests, map critical user journeys, and resolve launch-blocking defects; recorded evidence gates release approval.",
            "P1, Days 5–8: run regression, privacy/security, and operational readiness checks on the agreed scope.",
            "P1, Days 8–10: review evidence, confirm support ownership, and rehearse monitoring and rollback.",
            "Decision gate, Day 10: launch only if the agreed go/no-go criteria pass; otherwise reduce scope or defer.",
        ],
        "Revised two-week schedule": [
            "Week 1: Days 1–2 scope and ownership decisions; Days 3–5 fix critical issues and complete priority-path tests; Days 6–7 review test evidence and remaining blockers.",
            "Week 2: Days 8–9 finish regression and operational readiness; Day 10 make the launch/defer decision; Days 11–14 use a controlled rollout and daily monitoring only if approved, retaining rollback and contingency.",
        ],
        "Risks and mitigations": [
            "Unresolved scope disagreement: name one accountable decision owner and time-box the decision to Day 2.",
            "Incomplete testing: prioritize safety, privacy, and core support journeys; block launch on critical failures.",
            "Limited budget or capacity: protect P0 work, defer nonessential features, and avoid unapproved spend.",
            "Compressed schedule: preserve the decision gate and contingency; never treat missed tests as passed.",
        ],
        "Go/no-go criteria and decision points": [
            "Go only when scope is signed off, agreed critical journeys have passing evidence, no unresolved critical defect remains, monitoring and rollback are rehearsed, and support ownership is clear.",
            "Day 2: scope approval. Day 7: critical test evidence review. Day 10: accountable launch/defer decision.",
            "No-go if critical tests are incomplete or failing, privacy/security concerns remain, or rollback/support coverage is unavailable.",
        ],
        "Missing information": [
            "Named decision owner and available team capacity.",
            "Current defect inventory, severity definitions, and test coverage/results.",
            "Data handling requirements, budget ceiling, rollout constraints, and rollback capability.",
            "Agreed minimum launch scope and measurable service success thresholds.",
        ],
        "Success measures": [
            "All agreed critical journeys pass with recorded evidence and no open critical defects at the launch decision.",
            "Operational monitoring, support ownership, and rollback are ready before any rollout.",
            "Review agreed customer and service measures daily during controlled rollout.",
        ],
    }

def _general_document(request: str, plan: AgentPlan, analysis: RequestAnalysis) -> dict[str, Any]:
    lower = request.lower()
    requested = {
        "Objectives": any(word in lower for word in ("objective", "goal")),
        "Target users": any(word in lower for word in ("target user", "audience", "stakeholder")),
        "Scope and exclusions": any(word in lower for word in ("scope", "exclusion")),
        "Key features": any(word in lower for word in ("feature", "capability")),
        "Technology considerations": any(word in lower for word in ("technology", "technical", "platform")),
        "Timeline": analysis.duration_weeks is not None or any(word in lower for word in ("timeline", "schedule", "deadline")),
        "Risks and mitigations": any(word in lower for word in ("risk", "mitigation")),
        "Estimated roles and effort": any(word in lower for word in ("resource", "role", "effort", "staffing")),
        "Measurable success criteria": any(word in lower for word in ("success", "metric", "measure", "kpi")),
    }
    proposals: dict[str, Any] = {
        "Objectives": [plan.objective, "Confirm measurable acceptance criteria with the accountable stakeholders."],
        "Target users": ["Identify primary users, their key tasks, and accessibility needs during discovery; confirm these groups with stakeholders."],
        "Scope and exclusions": ["Include only the outcomes explicitly requested and the minimum work needed to deliver them.", "Record exclusions and defer unrequested integrations or enhancements until approved."],
        "Key features": ["Convert each stated user outcome into a prioritized capability and acceptance test.", "Prioritize a usable core workflow before optional enhancements."],
        "Technology considerations": ["Select maintained technologies that fit security, privacy, hosting, integration, and support requirements.", "Confirm the approved stack and constraints before implementation; no current company stack was provided."],
        "Risks and mitigations": ["Unclear requirements: confirm scope, owners, and acceptance criteria early.", "Schedule or resource pressure: prioritize essential outcomes and review changes at milestones.", "Quality or adoption issues: test with representative users and monitor agreed outcomes."],
        "Estimated roles and effort": ["Illustrative estimate only; confirm actual roles and capacity before committing.", "Identify a product/business decision owner, delivery owner, implementation capacity, and test/review capacity; no actual staffing information was supplied."],
        "Measurable success criteria": ["Proposed targets should be agreed and baselined before delivery; no current performance data was supplied.", "Track completion of the requested core outcomes, quality against agreed acceptance tests, and stakeholder/user feedback."],
    }
    sections: dict[str, Any] = {
        "Executive summary": f"This {analysis.document_type.lower()} addresses {analysis.topic or 'the requested work'} and turns the stated requirements into an actionable proposal. Organization-specific information not supplied in the request is left for confirmation.",
    }
    sections.update({heading: value for heading, value in proposals.items() if requested[heading]})
    if requested["Timeline"]:
        weeks = analysis.duration_weeks or 3
        sections["Timeline"] = [f"Week {week}: confirm the milestone and deliverable with the accountable owner." for week in range(1, weeks + 1)]
    sections["Assumptions and next steps"] = [
        f"The requested duration is {analysis.duration_weeks} weeks; the listed weeks cover that full period." if analysis.duration_weeks else "No duration was specified; any sequencing is illustrative.",
        "Confirm owners, dates, capacity, budget, technology constraints, and measurable acceptance criteria with stakeholders.",
    ]
    return sections
