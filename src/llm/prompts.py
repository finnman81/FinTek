"""
Prompt templates for the Anchorpoint system.

These prompts are tailored for equipment service company use cases:
troubleshooting, training, SOP lookup, and general technical Q&A.
"""

# Machine-parseable citation format: [source|p=N|s=Section>Subsection]
# Examples: [file.pdf|p=12|s=Maintenance>Valve] [file.pdf|p=13] [file.pdf]
CITATION_FORMAT = "[source|p=N|s=Section>Subsection]"
CITATION_EXAMPLE = "[manual.pdf|p=12|s=Maintenance>Valve]"

SYSTEM_PROMPT = """You are a technical assistant for an equipment service company.

INSTRUCTIONS:
1. Answer using only the provided context.
2. Every paragraph must end with a bracket citation copied exactly from the context.
3. If the answer is not supported by the context, respond with exactly: Not found in provided documents.

CONTEXT DOCUMENTS:
{context}
"""

QUERY_REWRITE_PROMPT = """Given the conversation history and the latest user question, \
rewrite the question to be a standalone question that captures the full intent.

Conversation history:
{history}

Latest question: {question}

Rewritten standalone question:"""

NO_CONTEXT_RESPONSE = "Not found in provided documents."

NO_CONTEXT_GENERAL_PROMPT = """The user asked: "{question}"

No relevant passages were found in the knowledge base.

Respond with exactly this:
Not found in provided documents.
"""

# Two-pass answer flow: extract exact sentences with citations, then compose only from those (reduces hallucinations, improves citations)
EXTRACT_SENTENCES_PROMPT = """Given the question and the context documents below, extract exactly 3–5 sentences from the context that directly answer the question. Copy sentences verbatim or as near-verbatim as possible.

For each extracted sentence, append its citation in the exact format shown in the context: [source|p=page|s=section] (e.g. [manual.pdf|p=12|s=Maintenance]).

Output format: one sentence per line, with the citation at the end of that line. Output ONLY the extracted lines—no preamble, no numbering, no other text.

QUESTION: {question}

CONTEXT DOCUMENTS:
{context}

EXTRACTED SENTENCES (one per line, citation at end):"""

COMPOSE_FROM_SENTENCES_PROMPT = """Compose the final answer using ONLY the extracted sentences below. Do not add any fact, number, or claim that is not present word-for-word (or near-word-for-word) in those sentences. Preserve the exact citation format [source|p=N|s=...] for every claim. If the extracted sentences do not fully answer the question, say so and cite only what is supported—do not fill in from general knowledge.

QUESTION: {question}

EXTRACTED SENTENCES (with citations):
{extracted}

ANSWER (based only on the extracted sentences above):"""


def citation_bracket(metadata: dict) -> str:
    """Build machine-parseable citation: [source|p=N|s=...]"""
    source = metadata.get("source", "Unknown")
    page = metadata.get("page") or metadata.get("page_start")
    section = metadata.get("section") or metadata.get("section_path", "")
    if page is not None and str(page).strip():
        if section and str(section).strip():
            return f"[{source}|p={page}|s={section}]"
        return f"[{source}|p={page}]"
    if section and str(section).strip():
        return f"[{source}|s={section}]"
    return f"[{source}]"


def build_chat_messages(
    user_question: str,
    context_chunks: list[dict],
    conversation_history: list[dict] | None = None,
) -> list[dict[str, str]]:
    """
    Build the full message list for the LLM.

    Args:
        user_question: The user's current question.
        context_chunks: Retrieved document chunks with text and metadata.
        conversation_history: Prior turns in the conversation (optional).

    Returns:
        List of message dicts ready for the LLM provider.
    """
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        text = chunk.get("text", "")
        context_parts.append(f"--- Document {i} ---\n{text}")

    context_text = "\n\n".join(context_parts) if context_parts else "No relevant documents found."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context_text)},
    ]

    if conversation_history:
        for turn in conversation_history[-6:]:
            messages.append(turn)

    messages.append({"role": "user", "content": user_question})

    return messages


def build_extract_sentences_messages(
    user_question: str,
    context_chunks: list[dict],
) -> list[dict[str, str]]:
    """Build messages for pass 1: extract 3–5 relevant sentences with citations."""
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        text = chunk.get("text", "")
        context_parts.append(f"--- Document {i} ---\n{text}")
    context_text = "\n\n".join(context_parts) if context_parts else ""
    content = EXTRACT_SENTENCES_PROMPT.format(question=user_question, context=context_text)
    return [{"role": "user", "content": content}]


def build_compose_from_extracted_messages(
    user_question: str,
    extracted_text: str,
) -> list[dict[str, str]]:
    """Build messages for pass 2: compose final answer from extracted sentences only."""
    content = COMPOSE_FROM_SENTENCES_PROMPT.format(
        question=user_question,
        extracted=extracted_text.strip() or "(No sentences extracted)",
    )
    return [{"role": "user", "content": content}]
