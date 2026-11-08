"""LangChain + Gemini agent that turns a problem description into job codes.

The model only picks jobs from our catalogue and may ask up to MAX_QUESTIONS
clarifying questions. Prices are never taken from the model.
"""

import logging
import re

from flask import current_app
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..extensions import db
from ..models import ServiceJob
from .schemas import AgentDecision
from .tools import find_service_jobs

log = logging.getLogger(__name__)

MAX_QUESTIONS = 3

SYSTEM_PROMPT = """You help car owners in Bangladesh understand what repair their car needs.
The car is a {vehicle} with {odometer} km on the odometer.

The owner may write in Bangla, in Banglish (Bangla written in English letters, for example
"brake e awaj kore") or in English. Always answer in the same language and script they use:
Bangla script for Bangla, English letters for Banglish, English for English. All text you
return (question, explanation, safety warnings) must follow this.
{script_rule}

Rules:
1. Only choose job codes from the catalogue below. Never invent codes, parts or prices.
2. If the problem is unclear, ask ONE short, specific question (action "ask"). Ask about
   things the owner can notice: sounds, when it happens, warning lights, smells, leaks.
3. You have asked {asked} of at most {max_questions} questions. When you reach the limit,
   or when you are fairly sure, give action "estimate".
4. For "estimate", list the jobs that most likely fix the problem, most likely first.
   Usually one to three jobs. If nothing fits, return an empty list and say so.
5. If brakes, steering, suspension, tyres or overheating are involved, add a safety warning
   telling the owner not to drive far until a mechanic checks it.

Catalogue (code: name. Typical words people use):
{catalogue}
"""


class AgentUnavailable(Exception):
    """The AI could not be used (no key, network error, bad reply)."""


def catalogue_text():
    jobs = db.session.execute(db.select(ServiceJob).order_by(ServiceJob.id)).scalars()
    return "\n".join(f"- {j.code}: {j.name_en} / {j.name_bn}. {j.keywords}" for j in jobs)


def get_chat_model():
    api_key = current_app.config.get("GOOGLE_API_KEY")
    if not api_key:
        raise AgentUnavailable("GOOGLE_API_KEY is not set.")
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=api_key,
        # The v1 API rejects system instructions, which the agent relies on.
        api_version="v1beta",
        temperature=0.2,
        timeout=30,
        max_retries=1,
    )


BANGLA_SCRIPT = re.compile(r"[ঀ-৿]")

SCRIPT_RULES = {
    "bangla": "This owner writes in Bangla script, so reply in Bangla script.",
    "latin": (
        "This owner writes in English letters only. Reply in English letters only, never in "
        "Bangla script: Banglish if they write Banglish, English if they write English."
    ),
}


def owner_script(problem_text, answers):
    text = problem_text + " ".join(turn["answer"] for turn in answers)
    return "bangla" if BANGLA_SCRIPT.search(text) else "latin"


def build_messages(problem_text, vehicle, answers):
    system = SYSTEM_PROMPT.format(
        script_rule=SCRIPT_RULES[owner_script(problem_text, answers)],
        vehicle=f"{vehicle.make} {vehicle.model} {vehicle.year} ({vehicle.engine_cc} cc)",
        odometer=f"{vehicle.odometer_km:,}",
        asked=len(answers),
        max_questions=MAX_QUESTIONS,
        catalogue=catalogue_text(),
    )
    messages = [SystemMessage(system), HumanMessage(problem_text)]
    for turn in answers:
        messages.append(AIMessage(turn["question"]))
        messages.append(HumanMessage(turn["answer"]))
    return messages


def run_agent(problem_text, vehicle, answers, model=None):
    """Return a cleaned AgentDecision. Raises AgentUnavailable if the AI cannot be used."""
    model = model or get_chat_model()
    try:
        structured = model.with_structured_output(AgentDecision)
        decision = structured.invoke(build_messages(problem_text, vehicle, answers))
    except AgentUnavailable:
        raise
    except Exception as err:  # network, quota, safety block, malformed output
        log.warning("AI agent failed: %s", err)
        raise AgentUnavailable(str(err)) from err

    if not isinstance(decision, AgentDecision):
        raise AgentUnavailable("The AI returned an unexpected reply.")

    valid = {job["code"] for job in find_service_jobs()}
    decision.job_codes = [c for c in dict.fromkeys(decision.job_codes) if c in valid][:5]
    decision.safety_warnings = [w.strip() for w in decision.safety_warnings if w and w.strip()][:5]
    decision.explanation = (decision.explanation or "").strip()[:1500]

    wants_to_ask = decision.action == "ask" and (decision.question or "").strip()
    if wants_to_ask and len(answers) < MAX_QUESTIONS:
        decision.question = decision.question.strip()[:300]
        decision.job_codes = []
    else:
        # Out of questions (or an empty question): the model must commit to an answer.
        decision.action = "estimate"
        decision.question = None
    return decision
