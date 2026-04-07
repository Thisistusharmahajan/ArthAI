# """
# Chat Route — /api/chat
# Handles multi-turn conversations with RAG context injection.
# """
# import json
# import logging
# from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
# import anthropic

# logger = logging.getLogger(__name__)
# chat_bp = Blueprint("chat", __name__)


# def get_rag():
#     return current_app.config["RAG_ENGINE"]


# def get_client():
#     return current_app.config["ANTHROPIC_CLIENT"]


# # ── Classify user profile ─────────────────────────────────────

# def classify_user(profile: dict) -> str:
#     """Build a user profile string for the prompt."""
#     income = profile.get("monthly_income", 0)
#     annual = income * 12
#     if annual < 500000:
#         bracket = "Low Income (below ₹5L/yr)"
#     elif annual < 1500000:
#         bracket = "Middle Class (₹5L-15L/yr)"
#     elif annual < 3000000:
#         bracket = "Upper Middle Class (₹15L-30L/yr)"
#     elif annual < 10000000:
#         bracket = "Rich (₹30L-1Cr/yr)"
#     else:
#         bracket = "Super Rich (above ₹1Cr/yr)"

#     lines = [f"User Income Bracket: {bracket}"]
#     if profile.get("name"):
#         lines.append(f"Name: {profile['name']}")
#     if profile.get("city"):
#         lines.append(f"City: {profile['city']}")
#     if profile.get("profession"):
#         lines.append(f"Profession: {profile['profession']}")
#     if income:
#         lines.append(f"Monthly Income: ₹{income:,.0f}")
#     if profile.get("monthly_savings"):
#         lines.append(f"Monthly Savings Target: ₹{profile['monthly_savings']:,.0f}")
#     if profile.get("risk_appetite"):
#         lines.append(f"Risk Appetite: {profile['risk_appetite']}")
#     if profile.get("investment_goal"):
#         lines.append(f"Investment Goal: {profile['investment_goal']}")
#     return "\n".join(lines)


# # ── Main chat endpoint ────────────────────────────────────────

# @chat_bp.route("/api/chat", methods=["POST"])
# def chat():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "Invalid JSON"}), 400

#         messages = data.get("messages", [])      # Full conversation history
#         user_profile = data.get("profile", {})   # User's financial profile
#         stream = data.get("stream", False)

#         if not messages:
#             return jsonify({"error": "No messages provided"}), 400

#         # Last user message for RAG retrieval
#         last_user_msg = next(
#             (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
#         )

#         # Build RAG context
#         rag = get_rag()
#         rag_context = rag.build_context(last_user_msg) if rag else ""

#         # Build user profile string
#         profile_str = classify_user(user_profile) if user_profile else ""

#         # Compose system prompt with context
#         from config import Config
#         system = Config.SYSTEM_PROMPT
#         if profile_str:
#             system += f"\n\n### User Profile\n{profile_str}"
#         if rag_context:
#             system += f"\n\n{rag_context}"

#         # Format messages for Anthropic API (only user/assistant roles)
#         api_messages = [
#             {"role": m["role"], "content": m["content"]}
#             for m in messages
#             if m.get("role") in ("user", "assistant") and m.get("content")
#         ]

#         client = get_client()

#         if stream:
#             return _stream_response(client, system, api_messages)
#         else:
#             return _sync_response(client, system, api_messages)

#     except Exception as e:
#         logger.error(f"Chat error: {e}", exc_info=True)
#         return jsonify({"error": str(e)}), 500


# def _sync_response(client, system: str, messages: list):
#     from config import Config
#     response = client.messages.create(
#         model=Config.CLAUDE_MODEL,
#         max_tokens=2048,
#         system=system,
#         messages=messages,
#     )
#     text = response.content[0].text if response.content else ""
#     return jsonify({
#         "response": text,
#         "usage": {
#             "input_tokens": response.usage.input_tokens,
#             "output_tokens": response.usage.output_tokens,
#         }
#     })


# def _stream_response(client, system: str, messages: list):
#     from config import Config

#     def generate():
#         with client.messages.stream(
#             model=Config.CLAUDE_MODEL,
#             max_tokens=2048,
#             system=system,
#             messages=messages,
#         ) as stream:
#             for text in stream.text_stream:
#                 yield f"data: {json.dumps({'token': text})}\n\n"
#         yield "data: [DONE]\n\n"

#     return Response(
#         stream_with_context(generate()),
#         mimetype="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "X-Accel-Buffering": "no",
#         }
#     )


# # ── Save / list conversations ─────────────────────────────────

# @chat_bp.route("/api/conversations", methods=["GET"])
# def list_conversations():
#     """List saved conversation stubs for the sidebar."""
#     # In production: query a database. Here: return mock data.
#     convs = [
#         {"id": "c1", "title": "SIP vs FD Analysis", "updated_at": "2025-01-20"},
#         {"id": "c2", "title": "Gold Investment 2025", "updated_at": "2025-01-18"},
#         {"id": "c3", "title": "Tax Saving ELSS Options", "updated_at": "2025-01-15"},
#         {"id": "c4", "title": "Home Loan Planning", "updated_at": "2025-01-10"},
#     ]
#     return jsonify({"conversations": convs})


# @chat_bp.route("/api/conversations/<conv_id>", methods=["GET"])
# def get_conversation(conv_id):
#     """Get a specific conversation's messages. Extend with DB."""
#     return jsonify({"messages": [], "id": conv_id})


"""
Chat Route — /api/chat
Handles multi-turn conversations with RAG context injection using Google Gemini.
"""
import json
import logging
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
import google.generativeai as genai

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


def get_rag():
    return current_app.config.get("RAG_ENGINE")


# ── Classify user profile ─────────────────────────────────────

def classify_user(profile: dict) -> str:
    """Build a user profile string for the prompt."""
    income = profile.get("monthly_income", 0)
    annual = income * 12
    if annual < 500000:
        bracket = "Low Income (below ₹5L/yr)"
    elif annual < 1500000:
        bracket = "Middle Class (₹5L-15L/yr)"
    elif annual < 3000000:
        bracket = "Upper Middle Class (₹15L-30L/yr)"
    elif annual < 10000000:
        bracket = "Rich (₹30L-1Cr/yr)"
    else:
        bracket = "Super Rich (above ₹1Cr/yr)"

    lines = [f"User Income Bracket: {bracket}"]
    if profile.get("name"):
        lines.append(f"Name: {profile['name']}")
    if profile.get("city"):
        lines.append(f"City: {profile['city']}")
    if profile.get("profession"):
        lines.append(f"Profession: {profile['profession']}")
    if income:
        lines.append(f"Monthly Income: ₹{income:,.0f}")
    if profile.get("monthly_savings"):
        lines.append(f"Monthly Savings Target: ₹{profile['monthly_savings']:,.0f}")
    if profile.get("risk_appetite"):
        lines.append(f"Risk Appetite: {profile['risk_appetite']}")
    if profile.get("investment_goal"):
        lines.append(f"Investment Goal: {profile['investment_goal']}")
    return "\n".join(lines)


# ── Main chat endpoint ────────────────────────────────────────

@chat_bp.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    # Handle preflight CORS request for this specific route if needed
    if request.method == "OPTIONS":
        return jsonify({}), 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        messages = data.get("messages", [])      # Full conversation history
        user_profile = data.get("profile", {})   # User's financial profile
        stream = data.get("stream", False)

        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        # Last user message for RAG retrieval
        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )

        # Build RAG context
        rag = get_rag()
        rag_context = rag.build_context(last_user_msg) if rag else ""

        # Build user profile string
        profile_str = classify_user(user_profile) if user_profile else ""

        # Compose system prompt with context
        from config import Config
        system = Config.SYSTEM_PROMPT
        if profile_str:
            system += f"\n\n### User Profile\n{profile_str}"
        if rag_context:
            system += f"\n\n{rag_context}"

        # Format messages for Gemini API
        # Gemini uses 'user' and 'model' (instead of 'assistant' or 'ai')
        api_messages = []
        for m in messages:
            role = m.get("role")
            content = m.get("content")
            
            if not content:
                continue
                
            # Map frontend roles to Gemini roles
            gemini_role = "model" if role in ("assistant", "ai") else "user"
            api_messages.append({"role": gemini_role, "parts": [content]})

        # Check if Gemini was configured globally in app.py
        if not current_app.config.get("GEMINI_CONFIGURED", False):
            return jsonify({"error": "Gemini API is not configured. Please check your .env file."}), 500

        if stream:
            return _stream_response(system, api_messages)
        else:
            return _sync_response(system, api_messages)

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def _sync_response(system: str, messages: list):
    from config import Config
    
    # Initialize the Gemini model with the system instructions injected
    model = genai.GenerativeModel(
        model_name=Config.GEMINI_MODEL,
        system_instruction=system
    )
    
    response = model.generate_content(messages)
    
    # Extract token usage metadata if available
    input_tokens = 0
    output_tokens = 0
    if hasattr(response, 'usage_metadata'):
        input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
        output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
    
    return jsonify({
        "response": response.text,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
    })


def _stream_response(system: str, messages: list):
    from config import Config
    
    model = genai.GenerativeModel(
        model_name=Config.GEMINI_MODEL,
        system_instruction=system
    )

    def generate():
        # Enable streaming mode in the generate_content call
        response = model.generate_content(messages, stream=True)
        
        for chunk in response:
            if chunk.text:
                # Format to match your existing frontend SSE setup
                yield f"data: {json.dumps({'token': chunk.text})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# ── Save / list conversations ─────────────────────────────────

@chat_bp.route("/api/conversations", methods=["GET"])
def list_conversations():
    """List saved conversation stubs for the sidebar."""
    # In production: query a database. Here: return mock data.
    convs = [
        {"id": "c1", "title": "SIP vs FD Analysis", "updated_at": "2025-01-20"},
        {"id": "c2", "title": "Gold Investment 2025", "updated_at": "2025-01-18"},
        {"id": "c3", "title": "Tax Saving ELSS Options", "updated_at": "2025-01-15"},
        {"id": "c4", "title": "Home Loan Planning", "updated_at": "2025-01-10"},
    ]
    return jsonify({"conversations": convs})


@chat_bp.route("/api/conversations/<conv_id>", methods=["GET"])
def get_conversation(conv_id):
    """Get a specific conversation's messages. Extend with DB."""
    return jsonify({"messages": [], "id": conv_id})