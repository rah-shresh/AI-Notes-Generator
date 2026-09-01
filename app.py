"""Streamlit user interface for the AI Notes Generator."""

from __future__ import annotations

import html
import json
import uuid

import streamlit as st
import streamlit.components.v1 as components

from utils.ai_helper import NOTE_STYLES, NotesGenerationError, generate_notes
from utils.pdf_helper import create_notes_pdf
from utils.storage import StorageError, clear_history, load_history, save_note


st.set_page_config(
    page_title="AI Notes Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_page_styles() -> None:
    """Add a small amount of CSS to make the default Streamlit UI more polished."""
    st.markdown(
        """
        <style>
            .block-container { max-width: 1200px; padding-top: 2.5rem; }
            [data-testid="stSidebar"] { border-right: 1px solid #e5e7eb; }
            .hero-copy { color: #4b5563; font-size: 1.05rem; margin-bottom: 1rem; }
            .note-meta { color: #6b7280; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialise_session_state() -> None:
    """Load persisted history once for this browser session."""
    if "history" not in st.session_state:
        try:
            st.session_state.history = load_history()
            st.session_state.history_error = None
        except StorageError:
            # The main app is still usable if a local history file is unavailable.
            st.session_state.history = []
            st.session_state.history_error = (
                "Saved history could not be loaded. New notes can still be generated."
            )

    st.session_state.setdefault("selected_note", None)
    st.session_state.setdefault("topic_input", "")
    st.session_state.setdefault("note_style", "Detailed explanation")


def select_note(note: dict) -> None:
    """Make a history item the active note and prefill its topic in the form."""
    st.session_state.selected_note = note
    st.session_state.topic_input = note["topic"]


def format_timestamp(timestamp: str) -> str:
    """Return a compact, human-friendly timestamp without failing on old data."""
    try:
        from datetime import datetime

        return datetime.fromisoformat(timestamp).strftime("%d %b %Y, %I:%M %p")
    except (TypeError, ValueError):
        return timestamp or "Saved note"


def render_sidebar() -> None:
    """Render the persistent note history controls."""
    with st.sidebar:
        st.header("📚 Note history")
        st.caption("Your generated notes are saved locally on this device.")

        if st.session_state.history_error:
            st.warning(st.session_state.history_error)

        history = st.session_state.history
        if not history:
            st.info("No saved notes yet. Your generated notes will appear here.")
            return

        for note in history:
            topic = note["topic"]
            label = f"📄 {topic[:34]}{'…' if len(topic) > 34 else ''}"
            if st.button(label, key=f"history_{note['id']}", use_container_width=True):
                select_note(note)
            st.caption(format_timestamp(note["timestamp"]))

        st.divider()
        if st.button("🗑️ Clear saved history", use_container_width=True):
            try:
                clear_history()
                st.session_state.history = []
                st.session_state.selected_note = None
                st.success("Saved history cleared.")
            except StorageError:
                st.error("History could not be cleared. Please try again.")


def clipboard_button(text: str) -> None:
    """Render a browser-side copy button with a compatibility fallback.

    Streamlit has no native clipboard control, so this small isolated component
    copies the active note without sending its text to another service.
    """
    button_id = f"copy-{uuid.uuid4().hex}"
    # Prevent note content from ending the script tag if it contains HTML-like text.
    safe_text = json.dumps(text).replace("</", "<\\/")
    components.html(
        f"""
        <button id="{button_id}" style="
            width: 100%; padding: 0.55rem 1rem; border: 1px solid #d1d5db;
            border-radius: 0.5rem; background: white; cursor: pointer; font-size: 0.95rem;">
            📋 Copy notes
        </button>
        <script>
            const button = document.getElementById({json.dumps(button_id)});
            const noteText = {safe_text};
            button.addEventListener('click', async () => {{
                try {{
                    if (navigator.clipboard && window.isSecureContext) {{
                        await navigator.clipboard.writeText(noteText);
                    }} else {{
                        const area = document.createElement('textarea');
                        area.value = noteText;
                        document.body.appendChild(area);
                        area.select();
                        document.execCommand('copy');
                        area.remove();
                    }}
                    button.textContent = '✓ Copied to clipboard';
                    setTimeout(() => button.textContent = '📋 Copy notes', 1800);
                }} catch (error) {{
                    button.textContent = 'Copy failed — select the text instead';
                }}
            }});
        </script>
        """,
        height=52,
    )


def render_active_note() -> None:
    """Render the currently selected note plus copy and download actions."""
    note = st.session_state.selected_note
    if not note:
        st.info("Enter a topic above to create your first set of notes.")
        return

    st.divider()
    title_column, meta_column = st.columns([3, 1])
    with title_column:
        st.subheader(f"Notes: {note['topic']}")
    with meta_column:
        st.markdown(
            f"<p class='note-meta'>Saved {html.escape(format_timestamp(note['timestamp']))}</p>",
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        # Streamlit safely renders model-generated Markdown without allowing raw HTML.
        st.markdown(note["notes"])

    copy_column, download_column = st.columns(2)
    with copy_column:
        clipboard_button(note["notes"])
    with download_column:
        try:
            pdf_bytes = create_notes_pdf(
                topic=note["topic"], notes=note["notes"], timestamp=note["timestamp"]
            )
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"{note['topic'][:50].strip() or 'ai-notes'}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            # PDF output is optional; keep the notes available if a local PDF issue occurs.
            st.warning("The PDF could not be prepared. You can still copy the notes.")


def render_note_form() -> None:
    """Render the note request form and save successful generations."""
    with st.form("note_form"):
        left_column, right_column = st.columns([2, 1])
        with left_column:
            topic = st.text_input(
                "What would you like to study?",
                key="topic_input",
                placeholder="For example: Photosynthesis or Python decorators",
            )
        with right_column:
            style = st.selectbox("Note style", list(NOTE_STYLES), key="note_style")

        submitted = st.form_submit_button(
            "✨ Generate notes", type="primary", use_container_width=True
        )

    if not submitted:
        return

    if not topic.strip():
        st.warning("Please enter a topic before generating notes.")
        return

    with st.spinner("Creating clear, structured notes…"):
        try:
            notes = generate_notes(topic=topic, style=style)
        except NotesGenerationError as error:
            st.error(str(error))
            return

    try:
        saved_note = save_note(topic=topic, notes=notes)
        st.session_state.history.insert(0, saved_note)
        st.session_state.selected_note = saved_note
        st.success("Your notes are ready and saved to history.")
    except StorageError:
        # Generation succeeded, so still show the useful result even if disk saving failed.
        st.session_state.selected_note = {
            "id": "unsaved",
            "topic": topic.strip(),
            "notes": notes,
            "timestamp": "Not saved locally",
        }
        st.warning("Your notes are ready, but they could not be saved to history.")


def main() -> None:
    apply_page_styles()
    initialise_session_state()
    render_sidebar()

    st.title("📝 AI Notes Generator")
    st.markdown(
        "<p class='hero-copy'>Turn any topic into well-structured study notes in seconds.</p>",
        unsafe_allow_html=True,
    )
    render_note_form()
    render_active_note()


if __name__ == "__main__":
    main()
