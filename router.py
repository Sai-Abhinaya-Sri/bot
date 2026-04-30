from language import translate_to_english
from agents import smart_agent, workflow_agent


def route_request(query, lang_info, db=None, history=None):
    """
    Entry point for voice input — lang_info already built from get_voice_config.
    Delegates to agent_router with safe defaults.
    """
    return agent_router(query, db, history or [], lang_info)


def agent_router(q, db, history, language_info):
    """
    Three-step pipeline:
    1. Translate query → English for accurate vector search
    2. Retrieve relevant context from English PDFs
    3. Generate response locked to user's original language & script style
    """
    # Translate once — reused for both workflow detection and vector search
    english_query = translate_to_english(q, language_info['language_code'], language_info)

    # Route to workflow agent if intent matches
    if any(x in english_query.lower() for x in ["automate", "automation", "workflow", "build", "create"]):
        return workflow_agent(q, history, language_info)

    # Search English PDFs with translated query
    ctx_chunks = db.search(english_query)
    context = "\n".join(ctx_chunks) if ctx_chunks else "No relevant info found."

    # Generate response — pass original query so LLM mirrors user's style
    return smart_agent(q, context, language_info)
