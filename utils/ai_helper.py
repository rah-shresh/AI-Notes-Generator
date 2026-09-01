"""Reliable Groq wrapper used by the Streamlit notes generator."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

try:
    from groq import (
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        Groq,
        NotFoundError,
        PermissionDeniedError,
        RateLimitError,
    )
except ImportError:  # The UI can still show a useful installation error.
    Groq = None


PROJECT_ROOT: Final = Path(__file__).resolve().parents[1]
ENV_FILE: Final = PROJECT_ROOT / ".env"
DEFAULT_MODEL: Final = "openai/gpt-oss-20b"
REQUEST_TIMEOUT_SECONDS: Final = 45.0
MAX_COMPLETION_TOKENS: Final = 2_048


NOTE_STYLES = {
    "Short summary": (
        "Keep the notes concise. Include a short overview and only the most important "
        "facts, terms, and takeaways."
    ),
    "Detailed explanation": (
        "Give a thorough, beginner-friendly explanation with clear sections, key terms, "
        "examples, and a brief recap."
    ),
    "Exam notes": (
        "Make revision-focused notes. Prioritise definitions, key points, formulas or "
        "dates when relevant, common exam questions, and a quick memory aid."
    ),
}


class NotesGenerationError(Exception):
    """An expected, user-facing error while generating notes."""


def _debug(message: str) -> None:
    """Write safe diagnostics for `streamlit run app.py` terminal output.

    Never put the API key or the full user prompt in these logs.
    """
    print(f"[ai_helper] {message}", flush=True)


def _load_api_key() -> str:
    """Load the root .env file explicitly and return a validated Groq key."""
    dotenv_loaded = load_dotenv(dotenv_path=ENV_FILE, override=False)
    _debug(f"dotenv_path={ENV_FILE}; file_exists={ENV_FILE.is_file()}; loaded={dotenv_loaded}")

    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    _debug(f"GROQ_API_KEY_present={bool(api_key)}; key_length={len(api_key)}")

    if not api_key:
        raise NotesGenerationError(
            f"GROQ_API_KEY was not found. Add it to {ENV_FILE.name} in the project root, "
            "then restart Streamlit."
        )
    if not api_key.startswith("gsk_"):
        raise NotesGenerationError(
            "GROQ_API_KEY has an unexpected format. Create a new key in the Groq console "
            "and update your .env file."
        )

    return api_key


def _raise_provider_error(error: Exception, model: str) -> None:
    """Log a safe, specific diagnostic and raise a useful UI error."""
    status_code = getattr(error, "status_code", "n/a")
    _debug(
        "Groq request failed: "
        f"type={type(error).__name__}; status_code={status_code}; model={model}"
    )

    if isinstance(error, AuthenticationError):
        raise NotesGenerationError(
            "Groq rejected the API key (HTTP 401). Check GROQ_API_KEY, then restart Streamlit."
        ) from error
    if isinstance(error, PermissionDeniedError):
        raise NotesGenerationError(
            "This Groq API key does not have permission to use the requested service (HTTP 403)."
        ) from error
    if isinstance(error, NotFoundError):
        raise NotesGenerationError(
            f"The Groq model '{model}' is unavailable to this account (HTTP 404). "
            "Set GROQ_MODEL to a model returned by the Groq Models API."
        ) from error
    if isinstance(error, RateLimitError):
        raise NotesGenerationError(
            "Groq rate limit reached (HTTP 429). Wait a moment and try again."
        ) from error
    if isinstance(error, BadRequestError):
        raise NotesGenerationError(
            "Groq rejected the request (HTTP 400). Check the selected model and request settings."
        ) from error
    if isinstance(error, APITimeoutError):
        raise NotesGenerationError(
            "The Groq request timed out. Check your connection and try again."
        ) from error
    if isinstance(error, APIConnectionError):
        raise NotesGenerationError(
            "Could not connect to Groq. Check your internet connection, firewall, or proxy."
        ) from error
    if isinstance(error, APIStatusError):
        raise NotesGenerationError(
            f"Groq returned an unexpected HTTP {status_code} error. Please try again later."
        ) from error

    # Preserve the original exception through exception chaining and log its type above.
    raise NotesGenerationError(
        "An unexpected error occurred while generating notes. See the Streamlit terminal logs "
        "for the error type."
    ) from error


def generate_notes(topic: str, style: str) -> str:
    """Generate Markdown notes for *topic* using the selected writing *style*.

    Required configuration in the project-root ``.env`` file::

        GROQ_API_KEY=gsk_...

    ``GROQ_MODEL`` is optional and defaults to ``openai/gpt-oss-20b``.
    """
    clean_topic = topic.strip()
    if not clean_topic:
        raise NotesGenerationError("Please enter a topic before generating notes.")
    if style not in NOTE_STYLES:
        raise NotesGenerationError("Please choose one of the available note styles.")
    if Groq is None:
        raise NotesGenerationError(
            "The Groq package is not installed. Run `pip install -r requirements.txt`."
        )

    api_key = _load_api_key()
    model = (os.getenv("GROQ_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    _debug(
        f"starting_generation: topic_length={len(clean_topic)}; style={style!r}; model={model!r}"
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert study assistant. Produce accurate, clearly structured "
                "study notes in Markdown. Use descriptive headings, bullets where useful, "
                "and practical examples. Do not include a preamble."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Create notes about: {clean_topic}\n\n"
                f"Requested style: {style}. {NOTE_STYLES[style]}"
            ),
        },
    ]

    try:
        _debug("creating Groq client")
        client = Groq(
            api_key=api_key,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_retries=2,
        )
        _debug("sending chat completion request")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_completion_tokens=MAX_COMPLETION_TOKENS,
        )
    except Exception as error:
        _raise_provider_error(error, model)

    choice_count = len(response.choices)
    _debug(f"Groq response received: choices={choice_count}")
    if not response.choices:
        raise NotesGenerationError("Groq returned no completion choices. Please try again.")

    notes = response.choices[0].message.content or ""
    if not notes.strip():
        _debug("Groq returned an empty completion")
        raise NotesGenerationError(
            "Groq returned an empty response. Please try again or use a larger completion limit."
        )

    _debug(f"generation_succeeded: response_length={len(notes.strip())}")
    return notes.strip()
