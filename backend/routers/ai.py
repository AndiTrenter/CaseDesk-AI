"""AI Chat & Proactive Router with Action Recognition"""
from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import logging
import json
import re

from deps import db, require_auth, log_action, get_user_language

logger = logging.getLogger(__name__)
router = APIRouter()


# Action detection patterns for German language
ACTION_PATTERNS = {
    "create_event": [
        r"(?:lege|erstelle|mach|plane).*(?:termin|ereignis|eintrag).*(?:an|für)",
        r"(?:termin|kalendereintrag).*(?:anlegen|erstellen|eintragen)",
        r"(?:trag|notier).*(?:in den kalender|termin)",
        r"geburtstag.*(?:eintragen|anlegen|erstellen)",
        r"(?:am|den|für).*\d+\..*(?:termin|eintrag|event)"
    ],
    "create_task": [
        r"(?:lege|erstelle|mach).*(?:aufgabe|task|todo|to-do).*(?:an|für)",
        r"(?:aufgabe|task).*(?:anlegen|erstellen)",
        r"erinnere mich.*(?:an|dass)"
    ],
    "create_case": [
        r"(?:lege|erstelle|eröffne).*(?:fall|akte|vorgang).*(?:an|für)",
        r"(?:fall|akte|vorgang).*(?:anlegen|erstellen|eröffnen)"
    ],
    "send_email": [
        r"(?:erstelle|schreibe|verfasse).*(?:e-?mail|nachricht|schreiben).*(?:an|für)",
        r"(?:e-?mail|nachricht).*(?:senden|schicken|schreiben).*(?:an|für)",
        r"schreib.*(?:an|der|dem).*(?:krankenkasse|versicherung|bank|amt|behörde|arbeitgeber)"
    ],
    "combined_event_task": [
        r"(?:erstelle|lege).*(?:termin|kalendereintrag).*(?:und|mit).*(?:aufgabe|task|erinnerung)",
        r"(?:termin|eintrag).*(?:erinnerung|aufgabe).*(?:gleichzeitig|dazu|auch)",
        r"(?:trage|erstelle).*(?:gleichzeitig|und).*(?:aufgabe|task)",
        r"(?:mit|und).*(?:einer?|).*erinnerung.*(?:vorher|davor)"
    ]
}


def detect_action_intent(message: str) -> Optional[str]:
    """Detect if the user message contains an action intent"""
    message_lower = message.lower()
    
    # Check for combined action first (event + task + reminder)
    for pattern in ACTION_PATTERNS["combined_event_task"]:
        if re.search(pattern, message_lower):
            return "combined_event_task"
    
    # Then check for single actions
    for action_type, patterns in ACTION_PATTERNS.items():
        if action_type == "combined_event_task":
            continue
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return action_type
    return None


async def parse_action_data(message: str, user: dict, action_type: str) -> dict:
    """Parse action data from message using AI"""
    from ai_service import get_ai_service
    
    ai_service = await get_ai_service(db)
    
    # Get user profile for context
    user_data = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    onboarding = await db.user_onboarding.find_one({"user_id": user["id"]}, {"_id": 0})
    
    user_name = onboarding.get("full_name") if onboarding else user_data.get("full_name", user_data.get("username", ""))
    user_address = onboarding.get("address", "") if onboarding else ""
    
    now = datetime.now(timezone.utc)
    current_date = now.strftime("%Y-%m-%d")
    current_year = now.year
    
    if action_type == "create_event":
        system_prompt = f"""Du bist ein Assistent der Kalendereinträge aus natürlicher Sprache extrahiert.
Heute ist der {current_date}.

Extrahiere folgende Informationen und antworte NUR mit validem JSON:
{{
    "title": "Titel des Termins",
    "description": "Beschreibung (optional)",
    "date": "YYYY-MM-DD",
    "start_time": "HH:MM",
    "end_time": "HH:MM",
    "all_day": true/false,
    "location": "Ort wenn angegeben",
    "ask_reminder": true
}}

Wenn kein Jahr angegeben, verwende {current_year} oder {current_year + 1}."""

    elif action_type == "create_task":
        system_prompt = f"""Du bist ein Assistent der Aufgaben aus natürlicher Sprache extrahiert.
Heute ist der {current_date}.

Extrahiere folgende Informationen und antworte NUR mit validem JSON:
{{
    "title": "Titel der Aufgabe",
    "description": "Beschreibung",
    "due_date": "YYYY-MM-DD oder null",
    "priority": "low/medium/high/urgent"
}}"""

    elif action_type == "create_case":
        system_prompt = """Du bist ein Assistent der Fallakten aus natürlicher Sprache extrahiert.

Extrahiere und antworte NUR mit validem JSON:
{
    "title": "Titel des Falls",
    "description": "Beschreibung",
    "reference_number": "Aktenzeichen oder null"
}"""

    elif action_type == "send_email":
        system_prompt = f"""Du bist ein Assistent der E-Mail-Anfragen extrahiert.

BENUTZERDATEN:
Name: {user_name}
Adresse: {user_address}
E-Mail: {user_data.get('email', '')}

Extrahiere und antworte NUR mit validem JSON:
{{
    "recipient": "Empfänger",
    "recipient_email": "E-Mail wenn bekannt oder null",
    "subject": "Betreff",
    "purpose": "Zweck/Anliegen",
    "draft_content": "Professioneller E-Mail-Entwurf",
    "suggested_documents": ["Dokumenttypen als Anlage"],
    "context": "Kurze Beschreibung für Nachverfolgung"
}}"""
    else:
        return {"success": False, "error": "Unbekannter Aktionstyp"}

    try:
        result = await ai_service.generate(message, system_prompt, max_tokens=1500)
        
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            action_data = json.loads(json_match.group())
            return {"success": True, "action_data": action_data}
    except Exception as e:
        logger.error(f"Parse action error: {e}")
    
    return {"success": False, "error": "Parsing fehlgeschlagen"}


@router.post("/ai/chat")
async def ai_chat(
    message: str = Form(...),
    session_id: str = Form(None),
    case_id: str = Form(None),
    document_id: str = Form(None),
    user: dict = Depends(require_auth)
):
    from ai_service import get_ai_service, ChatAssistant, AIMemory
    
    settings = await db.system_settings.find_one({}, {"_id": 0})
    if settings and settings.get("internet_access") == "denied" and settings.get("ai_provider") == "openai":
        return {
            "success": False,
            "error": "Externe KI benoetigt Internetzugriff. Bitte aktivieren Sie den Internetzugriff oder nutzen Sie die lokale KI (Ollama).",
            "response": None
        }
    
    session_id = session_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_msg = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "session_id": session_id,
        "role": "user",
        "content": message,
        "case_id": case_id,
        "document_id": document_id,
        "document_ids": [],
        "created_at": now
    }
    await db.chat_messages.insert_one(user_msg)
    
    context = {}
    
    all_docs = await db.documents.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "display_name": 1, "original_filename": 1, "ocr_text": 1,
         "ai_summary": 1, "tags": 1, "document_type": 1, "case_id": 1, "sender": 1,
         "document_date": 1}
    ).sort("created_at", -1).to_list(100)
    
    all_cases = await db.cases.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "status": 1, "reference_number": 1}
    ).to_list(50)
    
    # ADDED: Load recent emails for AI context (body_text for content)
    all_emails = await db.emails.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "subject": 1, "from_address": 1, "from_name": 1,
         "body_text": 1, "body_html": 1, "received_at": 1, "case_id": 1, "read": 1}
    ).sort("received_at", -1).to_list(50)
    
    context["all_documents"] = all_docs
    context["all_cases"] = all_cases
    context["all_emails"] = all_emails  # ADDED: Emails now available to AI
    
    # Focused document context
    if document_id:
        focused_doc = await db.documents.find_one(
            {"id": document_id, "user_id": user["id"]}, {"_id": 0}
        )
        if focused_doc:
            context["focused_document"] = focused_doc
    
    if case_id:
        case = await db.cases.find_one({"id": case_id, "user_id": user["id"]}, {"_id": 0})
        if case:
            context["current_case"] = case
            if case.get("document_ids"):
                docs = await db.documents.find(
                    {"id": {"$in": case["document_ids"]}, "user_id": user["id"]}, {"_id": 0}
                ).to_list(20)
                context["case_documents"] = docs
    
    open_tasks = await db.tasks.find(
        {"user_id": user["id"], "status": {"$ne": "done"}},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "due_date": 1, "priority": 1, "case_id": 1}
    ).sort("due_date", 1).to_list(20)
    context["open_tasks"] = open_tasks
    
    upcoming_events = await db.events.find(
        {"user_id": user["id"], "start_date": {"$gte": now}},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "start_date": 1, "end_date": 1}
    ).sort("start_date", 1).to_list(10)
    context["upcoming_events"] = upcoming_events
    
    user_language = await get_user_language(user)
    
    # Load onboarding data for comprehensive AI knowledge
    onboarding = await db.user_onboarding.find_one({"user_id": user["id"]}, {"_id": 0})
    if onboarding:
        context["onboarding_profile"] = onboarding
    
    try:
        ai_service = await get_ai_service(db)
        
        # Check if AI service is actually available (backwards compatible)
        if not ai_service:
            return {
                "success": False,
                "error": "KI-Service nicht verfügbar. Bitte konfigurieren Sie einen OpenAI API-Key in den Einstellungen oder richten Sie Ollama ein.",
                "response": "Ich kann Ihnen leider nicht helfen, da die KI-Integration nicht konfiguriert ist. Bitte gehen Sie zu Einstellungen → KI und konfigurieren Sie einen API-Key.",
                "action_preview": None
            }
        
        # Check if available property exists and is False
        if hasattr(ai_service, 'available') and not ai_service.available:
            return {
                "success": False,
                "error": "KI-Service nicht konfiguriert. API-Key fehlt oder ist ungültig.",
                "response": "Die KI-Integration ist nicht richtig konfiguriert. Bitte gehen Sie zu Einstellungen → KI und konfigurieren Sie einen gültigen OpenAI API-Key.",
                "action_preview": None
            }
        
        assistant = ChatAssistant(ai_service)
        memory = AIMemory(ai_service, db)
        
        # Load user profile and inject into context
        profile = await memory.get_profile(user["id"])
        profile_context = memory.build_profile_context(profile, user_language)
        context["user_profile_context"] = profile_context
        
        for doc in all_docs:
            doc["download_url"] = f"/api/documents/{doc['id']}/download"
        
        ai_response = await assistant.chat(message=message, context=context, language=user_language)
        
        referenced_docs = []
        for doc in all_docs:
            doc_name = doc.get('display_name', doc.get('original_filename', ''))
            if doc_name and doc_name.lower() in ai_response.lower():
                referenced_docs.append({
                    "id": doc["id"],
                    "name": doc_name,
                    "download_url": f"/api/documents/{doc['id']}/download"
                })
        
        # Extract facts in background (fire and forget)
        import asyncio
        asyncio.create_task(memory.extract_and_store_facts(user["id"], message, ai_response))
        
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        ai_response = f"KI-Fehler: {str(e)}"
        referenced_docs = []
    
    ai_msg = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "session_id": session_id,
        "role": "assistant",
        "content": ai_response,
        "case_id": case_id,
        "document_id": document_id,
        "document_ids": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(ai_msg)
    
    # Detect if message contains an action intent
    detected_action = detect_action_intent(message)
    action_preview = None
    
    if detected_action:
        try:
            # Parse action data for preview
            action_result = await parse_action_data(message, user, detected_action)
            if action_result.get("success"):
                action_preview = {
                    "action_type": detected_action,
                    "action_data": action_result.get("action_data"),
                    "needs_confirmation": True
                }
        except Exception as e:
            logger.error(f"Action detection error: {e}")
    
    return {
        "success": True,
        "response": ai_response,
        "session_id": session_id,
        "referenced_documents": referenced_docs,
        "action_preview": action_preview
    }


@router.get("/ai/status")
async def get_ai_status(user: dict = Depends(require_auth)):
    from ai_service import AIService
    ai = AIService(provider="ollama")
    status = await ai.check_availability()
    settings = await db.system_settings.find_one({}, {"_id": 0})
    return {
        "configured_provider": settings.get("ai_provider", "ollama") if settings else "ollama",
        "ollama": status["ollama"],
        "openai": status["openai"],
        "internet_access": settings.get("internet_access", "denied") if settings else "denied"
    }


@router.get("/ai/history")
async def get_chat_history(session_id: str, user: dict = Depends(require_auth)):
    messages = await db.chat_messages.find(
        {"user_id": user["id"], "session_id": session_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    return {"messages": messages}


@router.post("/ai/suggest-documents")
async def suggest_documents_for_case(
    case_title: str = Form(...),
    case_description: str = Form(None),
    user: dict = Depends(require_auth)
):
    from ai_service import get_ai_service, ProactiveAssistant
    ai_service = await get_ai_service(db)
    assistant = ProactiveAssistant(ai_service, db)
    return await assistant.suggest_documents_for_case(user["id"], case_title, case_description)


@router.get("/cases/{case_id}/proactive-analysis")
async def get_proactive_case_analysis(case_id: str, user: dict = Depends(require_auth)):
    from ai_service import get_ai_service, ProactiveAssistant
    ai_service = await get_ai_service(db)
    assistant = ProactiveAssistant(ai_service, db)
    return await assistant.analyze_case_proactively(user["id"], case_id)


@router.get("/ai/daily-briefing")
async def get_daily_briefing(user: dict = Depends(require_auth)):
    from ai_service import get_ai_service, ProactiveAssistant
    ai_service = await get_ai_service(db)
    assistant = ProactiveAssistant(ai_service, db)
    return await assistant.get_daily_briefing(user["id"])


@router.get("/ai/profile")
async def get_ai_profile(user: dict = Depends(require_auth)):
    """Get the user's AI memory profile"""
    from ai_service import get_ai_service, AIMemory
    ai_service = await get_ai_service(db)
    memory = AIMemory(ai_service, db)
    profile = await memory.get_profile(user["id"])
    return {"success": True, "profile": profile}


@router.delete("/ai/profile/facts/{fact_index}")
async def delete_ai_profile_fact(fact_index: int, user: dict = Depends(require_auth)):
    """Delete a specific fact from the user's AI profile"""
    profile = await db.ai_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    if not profile or fact_index >= len(profile.get("facts", [])):
        return {"success": False, "error": "Fakt nicht gefunden"}
    
    facts = profile.get("facts", [])
    facts.pop(fact_index)
    await db.ai_profiles.update_one(
        {"user_id": user["id"]},
        {"$set": {"facts": facts, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True}


@router.post("/ai/profile/clear")
async def clear_ai_profile(
    password: str = Form(...),
    user: dict = Depends(require_auth)
):
    """Clear the entire AI memory profile - requires password confirmation"""
    from deps import verify_password
    
    # Verify password
    db_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not db_user or not verify_password(password, db_user.get("password_hash", "")):
        return {"success": False, "error": "Falsches Passwort"}
    
    # Get fact count for audit
    profile = await db.ai_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
    fact_count = len(profile.get("facts", [])) if profile else 0
    
    await db.ai_profiles.delete_one({"user_id": user["id"]})
    await log_action(user["id"], "clear_ai_profile", "ai_profile", None)
    
    return {"success": True, "deleted_facts": fact_count}


@router.get("/ai/knowledge")
async def get_ai_knowledge(user: dict = Depends(require_auth)):
    """Get everything the AI knows about the user - comprehensive view"""
    from ai_service import get_ai_service, AIMemory
    ai_service = await get_ai_service(db)
    memory = AIMemory(ai_service, db)
    profile = await memory.get_profile(user["id"])

    # Onboarding data
    onboarding = await db.user_onboarding.find_one({"user_id": user["id"]}, {"_id": 0})

    # Document summaries
    docs = await db.documents.find(
        {"user_id": user["id"], "ai_analyzed": True},
        {"_id": 0, "id": 1, "display_name": 1, "ai_summary": 1, "document_type": 1, "sender": 1, "tags": 1}
    ).to_list(200)

    # Case summaries
    cases = await db.cases.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "status": 1}
    ).to_list(100)

    return {
        "success": True,
        "onboarding": onboarding or {},
        "profile": profile,
        "documents_analyzed": len(docs),
        "documents": docs,
        "cases_count": len(cases),
        "cases": cases
    }


@router.post("/ai/onboarding")
async def save_onboarding_profile(
    full_name: str = Form(None),
    address: str = Form(None),
    phone: str = Form(None),
    birthdate: str = Form(None),
    marital_status: str = Form(None),
    partner_name: str = Form(None),
    children: str = Form(None),
    employer: str = Form(None),
    occupation: str = Form(None),
    insurance_health: str = Form(None),
    notes: str = Form(None),
    user: dict = Depends(require_auth)
):
    """Save or update user onboarding profile data"""
    now = datetime.now(timezone.utc).isoformat()
    data = {"user_id": user["id"], "updated_at": now}

    fields = {
        "full_name": full_name, "address": address, "phone": phone,
        "birthdate": birthdate, "marital_status": marital_status,
        "partner_name": partner_name, "children": children,
        "employer": employer, "occupation": occupation,
        "insurance_health": insurance_health, "notes": notes
    }
    for k, v in fields.items():
        if v is not None:
            data[k] = v

    await db.user_onboarding.update_one(
        {"user_id": user["id"]}, {"$set": data}, upsert=True
    )

    # Also store as AI facts for the memory system
    from ai_service import get_ai_service, AIMemory
    ai_service = await get_ai_service(db)
    memory = AIMemory(ai_service, db)

    fact_mappings = {
        "full_name": ("Name", full_name),
        "address": ("Adresse", address),
        "phone": ("Telefon", phone),
        "birthdate": ("Geburtsdatum", birthdate),
        "marital_status": ("Familienstand", marital_status),
        "partner_name": ("Partner", partner_name),
        "children": ("Kinder", children),
        "employer": ("Arbeitgeber", employer),
        "occupation": ("Beruf", occupation),
        "insurance_health": ("Krankenversicherung", insurance_health),
    }

    new_facts = []
    for field_key, (fact_key, value) in fact_mappings.items():
        if value and value.strip():
            new_facts.append({
                "key": fact_key,
                "value": value.strip(),
                "source": "onboarding",
                "extracted_at": now
            })

    if new_facts:
        await db.ai_profiles.update_one(
            {"user_id": user["id"]},
            {
                "$push": {"facts": {"$each": new_facts}},
                "$set": {"updated_at": now},
                "$setOnInsert": {"id": str(uuid.uuid4()), "summary": ""}
            },
            upsert=True
        )

    return {"success": True}


@router.get("/ai/onboarding")
async def get_onboarding_profile(user: dict = Depends(require_auth)):
    """Get user onboarding profile"""
    data = await db.user_onboarding.find_one({"user_id": user["id"]}, {"_id": 0})
    return {"success": True, "profile": data or {}}


@router.post("/documents/suggest-metadata")
async def suggest_document_metadata(
    document_id: str = Form(...),
    user: dict = Depends(require_auth)
):
    """AI suggests tags and matching cases for a newly uploaded document"""
    from ai_service import get_ai_service
    import re as _re

    doc = await db.documents.find_one(
        {"id": document_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not doc:
        return {"success": False, "error": "Document not found"}

    # Get existing cases for matching
    cases = await db.cases.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "status": 1, "reference_number": 1}
    ).to_list(50)

    # Get existing tags across all docs
    all_tags_pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags"}},
        {"$limit": 50}
    ]
    existing_tags = [t["_id"] async for t in db.documents.aggregate(all_tags_pipeline)]

    doc_text = doc.get("ocr_text", "")[:3000]
    doc_name = doc.get("display_name", doc.get("original_filename", ""))
    doc_summary = doc.get("ai_summary", "")

    if not doc_text and not doc_summary:
        return {"success": True, "suggested_tags": doc.get("tags", []), "suggested_cases": []}

    user_language = "de"

    cases_str = "\n".join([f"- ID:{c['id']} | {c['title']} | {c.get('description','')[:100]}" for c in cases]) if cases else "Keine Fälle vorhanden"
    tags_str = ", ".join(existing_tags) if existing_tags else "Keine"

    prompt = f"""Analysiere dieses Dokument und schlage passende Tags und Fälle vor.

DOKUMENT: {doc_name}
ZUSAMMENFASSUNG: {doc_summary}
INHALT: {doc_text[:2000]}

VORHANDENE TAGS: {tags_str}
VORHANDENE FÄLLE:
{cases_str}

Antworte NUR mit validem JSON:
{{"suggested_tags": ["tag1", "tag2", "tag3"], "suggested_case_ids": ["case-id-1"], "reasoning": "kurze Begründung"}}

Regeln:
- Maximal 5 Tags vorschlagen (bevorzuge existierende Tags, ergänze neue wenn sinnvoll)
- Nur passende Fälle vorschlagen (case IDs aus der Liste oben)
- Tags auf Deutsch"""

    try:
        ai_service = await get_ai_service(db)
        result = await ai_service.generate(prompt, "Du bist ein Dokumenten-Klassifizierungs-Assistent.", max_tokens=500)

        json_match = _re.search(r'\{[\s\S]*\}', result)
        if json_match:
            import json
            data = json.loads(json_match.group())
            return {
                "success": True,
                "suggested_tags": data.get("suggested_tags", []),
                "suggested_cases": [c for c in cases if c["id"] in data.get("suggested_case_ids", [])],
                "reasoning": data.get("reasoning", "")
            }
    except Exception as e:
        logger.error(f"Suggestion error: {e}")

    return {"success": True, "suggested_tags": doc.get("tags", []), "suggested_cases": []}



# ==================== AI Action Endpoints ====================

@router.post("/ai/parse-action")
async def parse_action_from_message(
    message: str = Form(...),
    user: dict = Depends(require_auth)
):
    """
    Parse user message to extract structured action data using AI.
    Returns action type and structured data for preview/confirmation.
    """
    from ai_service import get_ai_service
    
    # First, detect action type using patterns
    action_type = detect_action_intent(message)
    
    if not action_type:
        return {"success": False, "action_detected": False, "message": "Keine Aktion erkannt"}
    
    ai_service = await get_ai_service(db)
    
    # Get user profile for context (for email sender info etc.)
    user_data = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    onboarding = await db.user_onboarding.find_one({"user_id": user["id"]}, {"_id": 0})
    
    user_name = onboarding.get("full_name") if onboarding else user_data.get("full_name", user_data.get("username", ""))
    user_address = onboarding.get("address", "") if onboarding else ""
    
    # Get correspondence history for email tracking context
    correspondence_history = await db.correspondence.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "subject": 1, "recipient": 1, "type": 1, "status": 1, "sent_at": 1, "created_at": 1, "context": 1}
    ).sort("created_at", -1).to_list(50)
    
    now = datetime.now(timezone.utc)
    current_date = now.strftime("%Y-%m-%d")
    current_year = now.year
    
    if action_type == "create_event":
        system_prompt = f"""Du bist ein Assistent der Kalendereinträge aus natürlicher Sprache extrahiert.
Heute ist der {current_date}.

Extrahiere folgende Informationen aus der Benutzeranfrage und antworte NUR mit validem JSON:
{{
    "title": "Titel des Termins",
    "description": "Beschreibung (optional)",
    "date": "YYYY-MM-DD (das erkannte Datum)",
    "start_time": "HH:MM (wenn angegeben, sonst '09:00')",
    "end_time": "HH:MM (wenn angegeben, sonst '10:00')",
    "all_day": true/false,
    "location": "Ort wenn angegeben",
    "reminder_question": "Soll ich auch eine Erinnerungsaufgabe anlegen? Falls ja, wie viele Tage vorher?"
}}

Regeln:
- Wenn nur "Geburtstag" erwähnt wird, setze all_day auf true
- Wenn kein Jahr angegeben, verwende {current_year} oder {current_year + 1} (je nachdem ob das Datum bereits vorbei ist)
- Bei "nächsten Montag" etc. berechne das korrekte Datum
- Stelle IMMER die reminder_question"""

    elif action_type == "create_task":
        system_prompt = f"""Du bist ein Assistent der Aufgaben aus natürlicher Sprache extrahiert.
Heute ist der {current_date}.

Extrahiere folgende Informationen und antworte NUR mit validem JSON:
{{
    "title": "Titel der Aufgabe",
    "description": "Beschreibung (optional)",
    "due_date": "YYYY-MM-DD (wenn Frist erkennbar)",
    "priority": "low/medium/high/urgent (basierend auf Kontext)"
}}"""

    elif action_type == "create_case":
        system_prompt = """Du bist ein Assistent der Fallakten aus natürlicher Sprache extrahiert.

Extrahiere folgende Informationen und antworte NUR mit validem JSON:
{
    "title": "Titel des Falls",
    "description": "Beschreibung des Falls",
    "reference_number": "Aktenzeichen wenn angegeben (sonst null)"
}"""

    elif action_type == "send_email":
        # Include correspondence history for tracking
        history_text = ""
        if correspondence_history:
            history_text = "\n\nBISHERIGE KORRESPONDENZ:\n"
            for h in correspondence_history[:20]:
                status_text = "gesendet" if h.get("status") == "sent" else "Entwurf"
                sent_info = f" am {h.get('sent_at', '')[:10]}" if h.get("sent_at") else ""
                history_text += f"- {h.get('subject', 'Ohne Betreff')} an {h.get('recipient', 'Unbekannt')} ({status_text}{sent_info})\n"
                if h.get("context"):
                    history_text += f"  Kontext: {h.get('context')}\n"
        
        system_prompt = f"""Du bist ein Assistent der E-Mail-Anfragen aus natürlicher Sprache extrahiert.

BENUTZERDATEN:
Name: {user_name}
Adresse: {user_address}
E-Mail: {user_data.get('email', '')}
{history_text}

Extrahiere folgende Informationen und antworte NUR mit validem JSON:
{{
    "recipient": "Empfänger (z.B. 'Krankenkasse', 'AOK', 'Finanzamt')",
    "recipient_email": "E-Mail-Adresse wenn bekannt (sonst null)",
    "subject": "Betreff der E-Mail",
    "purpose": "Zweck/Anliegen der E-Mail (z.B. 'Zahlungsfristverlängerung', 'Kündigung')",
    "draft_content": "Entwurf des E-Mail-Textes (formal, höflich, professionell)",
    "suggested_documents": ["Liste von Dokumenttypen die als Anlage nützlich wären"],
    "context": "Kurze Beschreibung des Anliegens für die Nachverfolgung"
}}

Regeln:
- Erstelle einen vollständigen, professionellen E-Mail-Entwurf
- Verwende die Benutzerdaten für den Absender
- Der Entwurf soll formal und höflich sein
- Bei Behörden verwende "Sehr geehrte Damen und Herren"
- Speichere den Kontext für spätere Nachverfolgung"""

    elif action_type == "combined_event_task":
        system_prompt = f"""Du bist ein Assistent der kombinierte Kalender- und Aufgabenanfragen aus natürlicher Sprache extrahiert.
Heute ist der {current_date}.

Der Benutzer möchte GLEICHZEITIG:
1. Einen Kalendereintrag erstellen
2. Eine oder mehrere Aufgaben erstellen
3. Optional: Eine Erinnerung festlegen

Extrahiere folgende Informationen und antworte NUR mit validem JSON:
{{
    "event": {{
        "title": "Titel des Kalendereintrags",
        "description": "Beschreibung",
        "date": "YYYY-MM-DD",
        "start_time": "HH:MM (oder '09:00' wenn ganztägig)",
        "end_time": "HH:MM (oder '10:00' wenn ganztägig)",
        "all_day": true/false,
        "location": "Ort wenn angegeben"
    }},
    "tasks": [
        {{
            "title": "Titel der Aufgabe",
            "description": "Beschreibung",
            "due_date": "YYYY-MM-DD oder null",
            "priority": "medium"
        }}
    ],
    "reminder": {{
        "enabled": true/false,
        "type": "1_week/1_day/2_days/none",
        "description": "z.B. '1 Woche vorher'"
    }}
}}

Regeln:
- Wenn "Geburtstag" erwähnt wird, setze all_day auf true
- Wenn kein Jahr angegeben, verwende {current_year} oder {current_year + 1}
- Erkenne "Erinnerung X Tage/Wochen vorher" und setze reminder.enabled=true mit passendem type
- type kann sein: none, 1_day, 2_days, 1_week, 2_weeks
- Wenn eine separate Aufgabe erwähnt wird (z.B. "Kuchen kaufen"), füge sie zur tasks-Liste hinzu
- Die Aufgabe due_date sollte VOR dem Event-Datum liegen wenn sinnvoll"""

    try:
        result = await ai_service.generate(message, system_prompt, max_tokens=1500)
        
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            action_data = json.loads(json_match.group())
            
            return {
                "success": True,
                "action_detected": True,
                "action_type": action_type,
                "action_data": action_data,
                "original_message": message
            }
        else:
            return {"success": False, "action_detected": True, "action_type": action_type, "error": "Konnte Daten nicht extrahieren"}
            
    except Exception as e:
        logger.error(f"Action parse error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/ai/execute-action")
async def execute_action(
    action_type: str = Form(...),
    action_data: str = Form(...),  # JSON string
    confirmed: bool = Form(True),
    user: dict = Depends(require_auth)
):
    """
    Execute a confirmed action (create event, task, case, or email draft).
    """
    if not confirmed:
        return {"success": False, "error": "Aktion wurde nicht bestätigt"}
    
    try:
        data = json.loads(action_data)
    except json.JSONDecodeError:
        return {"success": False, "error": "Ungültige Aktionsdaten"}
    
    now = datetime.now(timezone.utc).isoformat()
    
    if action_type == "create_event":
        event_id = str(uuid.uuid4())
        
        # Parse date and time
        event_date = data.get("date", now[:10])
        start_time_str = data.get("start_time", "09:00")
        end_time_str = data.get("end_time", "10:00")
        
        # FIXED: Convert to datetime objects instead of strings
        from datetime import datetime
        start_datetime = datetime.fromisoformat(f"{event_date}T{start_time_str}:00")
        end_datetime = datetime.fromisoformat(f"{event_date}T{end_time_str}:00")
        
        event = {
            "id": event_id,
            "user_id": user["id"],
            "title": data.get("title", "Neuer Termin"),
            "description": data.get("description", ""),
            "start_time": start_datetime,  # datetime object!
            "end_time": end_datetime,      # datetime object!
            "all_day": data.get("all_day", False),
            "location": data.get("location"),
            "case_id": data.get("case_id"),
            "source": "ai_chat",
            "created_at": now,
            "updated_at": now
        }
        
        await db.events.insert_one(event)
        await log_action(user["id"], "create_event_via_ai", "event", event_id)
        
        # Create reminder task if requested
        reminder_task = None
        if data.get("create_reminder") and data.get("reminder_days"):
            try:
                reminder_days = int(data.get("reminder_days", 1))
                event_dt = datetime.fromisoformat(event_date)
                reminder_date = (event_dt - timedelta(days=reminder_days)).strftime("%Y-%m-%d")
                
                task_id = str(uuid.uuid4())
                reminder_task = {
                    "id": task_id,
                    "user_id": user["id"],
                    "title": f"Erinnerung: {data.get('title', 'Termin')}",
                    "description": f"Termin am {event_date}: {data.get('title', '')}",
                    "priority": "medium",
                    "status": "todo",
                    "due_date": reminder_date,
                    "event_id": event_id,
                    "source": "ai_reminder",
                    "created_at": now,
                    "updated_at": now
                }
                await db.tasks.insert_one(reminder_task)
                # Remove _id from reminder_task for JSON serialization
                if "_id" in reminder_task:
                    del reminder_task["_id"]
            except Exception as e:
                logger.error(f"Reminder creation error: {e}")
        
        # Remove _id from event for JSON serialization
        if "_id" in event:
            del event["_id"]
        
        return {
            "success": True,
            "action_type": "create_event",
            "created": event,
            "reminder_task": reminder_task,
            "message": f"Termin '{data.get('title')}' am {event_date} wurde erstellt."
        }
    
    elif action_type == "create_task":
        task_id = str(uuid.uuid4())
        
        # FIXED: Convert due_date string to datetime object if provided
        due_date_obj = None
        if data.get("due_date"):
            try:
                from datetime import datetime
                due_date_str = data.get("due_date")
                # Handle both "2026-04-10" and "2026-04-10T15:00:00" formats
                if "T" in due_date_str:
                    due_date_obj = datetime.fromisoformat(due_date_str)
                else:
                    due_date_obj = datetime.fromisoformat(f"{due_date_str}T23:59:59")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid due_date format: {data.get('due_date')} - {e}")
                due_date_obj = None
        
        task = {
            "id": task_id,
            "user_id": user["id"],
            "title": data.get("title", "Neue Aufgabe"),
            "description": data.get("description", ""),
            "priority": data.get("priority", "medium"),
            "status": "todo",
            "due_date": due_date_obj,  # datetime object or None!
            "case_id": data.get("case_id"),
            "source": "ai_chat",
            "created_at": now,
            "updated_at": now
        }
        
        await db.tasks.insert_one(task)
        await log_action(user["id"], "create_task_via_ai", "task", task_id)
        
        # Remove _id from task for JSON serialization
        if "_id" in task:
            del task["_id"]
        
        return {
            "success": True,
            "action_type": "create_task",
            "created": task,
            "message": f"Aufgabe '{data.get('title')}' wurde erstellt."
        }
    
    elif action_type == "create_case":
        case_id = str(uuid.uuid4())
        
        case = {
            "id": case_id,
            "user_id": user["id"],
            "title": data.get("title", "Neuer Fall"),
            "description": data.get("description", ""),
            "reference_number": data.get("reference_number"),
            "status": "open",
            "tags": [],
            "document_ids": [],
            "email_ids": [],
            "created_at": now,
            "updated_at": now
        }
        
        await db.cases.insert_one(case)
        await log_action(user["id"], "create_case_via_ai", "case", case_id)
        
        # Remove _id from case for JSON serialization
        if "_id" in case:
            del case["_id"]
        
        return {
            "success": True,
            "action_type": "create_case",
            "created": case,
            "message": f"Fall '{data.get('title')}' wurde erstellt."
        }
    
    elif action_type == "send_email":
        # Create email draft/correspondence for review
        correspondence_id = str(uuid.uuid4())
        
        correspondence = {
            "id": correspondence_id,
            "user_id": user["id"],
            "type": "email",
            "subject": data.get("subject", ""),
            "recipient": data.get("recipient", ""),
            "recipient_email": data.get("recipient_email"),
            "content": data.get("draft_content", ""),
            "purpose": data.get("purpose", ""),
            "context": data.get("context", ""),  # For tracking/search
            "suggested_documents": data.get("suggested_documents", []),
            "document_ids": [],
            "status": "draft",
            "source": "ai_chat",
            "created_at": now,
            "updated_at": now,
            "sent_at": None
        }
        
        await db.correspondence.insert_one(correspondence)
        await log_action(user["id"], "create_email_draft_via_ai", "correspondence", correspondence_id)
        
        # Remove _id from correspondence for JSON serialization
        if "_id" in correspondence:
            del correspondence["_id"]
        
        return {
            "success": True,
            "action_type": "send_email",
            "created": correspondence,
            "message": f"E-Mail-Entwurf an '{data.get('recipient')}' wurde erstellt. Bitte überprüfen und bestätigen Sie den Versand."
        }
    
    elif action_type == "combined_event_task":
        # Handle combined event + task + reminder creation
        results = {
            "event": None,
            "tasks": [],
            "reminder": None
        }
        messages = []
        
        # 1. Create Event
        event_data = data.get("event", {})
        if event_data:
            event_id = str(uuid.uuid4())
            event_date = event_data.get("date", now[:10])
            start_time = event_data.get("start_time", "09:00")
            end_time = event_data.get("end_time", "10:00")
            
            # Handle reminder settings
            reminder_data = data.get("reminder", {})
            reminder_enabled = reminder_data.get("enabled", False)
            reminder_type = reminder_data.get("type", "none")
            
            # Map reminder type to minutes
            reminder_minutes_map = {
                "none": None, "at_time": 0, "5_min": 5, "15_min": 15, "30_min": 30,
                "1_hour": 60, "2_hours": 120, "1_day": 1440, "2_days": 2880,
                "1_week": 10080, "2_weeks": 20160
            }
            reminder_minutes = reminder_minutes_map.get(reminder_type)
            
            event = {
                "id": event_id,
                "user_id": user["id"],
                "title": event_data.get("title", "Neuer Termin"),
                "description": event_data.get("description", ""),
                "start_time": f"{event_date}T{start_time}:00",
                "end_time": f"{event_date}T{end_time}:00",
                "all_day": event_data.get("all_day", False),
                "location": event_data.get("location"),
                "reminder_enabled": reminder_enabled,
                "reminder_type": reminder_type,
                "reminder_minutes": reminder_minutes,
                "reminder_channels": ["app"],
                "reminder_sent": False,
                "source": "ai_chat",
                "created_at": now,
                "updated_at": now
            }
            
            await db.events.insert_one(event)
            await log_action(user["id"], "create_event_via_ai", "event", event_id)
            
            # Create reminder record if enabled
            if reminder_enabled and reminder_minutes is not None:
                try:
                    event_dt = datetime.fromisoformat(f"{event_date}T{start_time}:00")
                    reminder_time = event_dt - timedelta(minutes=reminder_minutes)
                    reminder_id = str(uuid.uuid4())
                    reminder = {
                        "id": reminder_id,
                        "user_id": user["id"],
                        "event_id": event_id,
                        "title": f"Erinnerung: {event_data.get('title', 'Termin')}",
                        "reminder_time": reminder_time.isoformat(),
                        "channels": ["app"],
                        "sent": False,
                        "created_at": now
                    }
                    await db.reminders.insert_one(reminder)
                    if "_id" in reminder:
                        del reminder["_id"]
                    results["reminder"] = reminder
                except Exception as e:
                    logger.error(f"Reminder creation error: {e}")
            
            if "_id" in event:
                del event["_id"]
            results["event"] = event
            messages.append(f"Kalendereintrag '{event_data.get('title')}' am {event_date} erstellt")
            if reminder_enabled:
                messages.append(f"Erinnerung {reminder_data.get('description', '')} hinzugefügt")
        
        # 2. Create Tasks
        tasks_data = data.get("tasks", [])
        for task_data in tasks_data:
            task_id = str(uuid.uuid4())
            task = {
                "id": task_id,
                "user_id": user["id"],
                "title": task_data.get("title", "Neue Aufgabe"),
                "description": task_data.get("description", ""),
                "priority": task_data.get("priority", "medium"),
                "status": "todo",
                "due_date": task_data.get("due_date"),
                "event_id": event_id if event_data else None,
                "source": "ai_chat",
                "created_at": now,
                "updated_at": now
            }
            await db.tasks.insert_one(task)
            await log_action(user["id"], "create_task_via_ai", "task", task_id)
            
            if "_id" in task:
                del task["_id"]
            results["tasks"].append(task)
            messages.append(f"Aufgabe '{task_data.get('title')}' erstellt")
        
        return {
            "success": True,
            "action_type": "combined_event_task",
            "created": results,
            "message": " | ".join(messages)
        }
    
    else:
        return {"success": False, "error": f"Unbekannter Aktionstyp: {action_type}"}


@router.get("/ai/correspondence-search")
async def search_correspondence(
    query: str,
    user: dict = Depends(require_auth)
):
    """
    Search correspondence history for tracking purposes.
    Used when user asks "Was I already contacted about X?" type questions.
    """
    from ai_service import get_ai_service
    
    # Get all correspondence
    all_correspondence = await db.correspondence.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    if not all_correspondence:
        return {
            "success": True,
            "found": False,
            "message": "Keine Korrespondenz gefunden.",
            "results": []
        }
    
    # Use AI to find relevant correspondence
    ai_service = await get_ai_service(db)
    
    correspondence_list = ""
    for c in all_correspondence:
        status_text = "gesendet" if c.get("status") == "sent" else "Entwurf"
        sent_info = f" am {c.get('sent_at', '')[:10]}" if c.get("sent_at") else f" erstellt am {c.get('created_at', '')[:10]}"
        correspondence_list += f"\n- ID: {c['id']}"
        correspondence_list += f"\n  Betreff: {c.get('subject', 'Ohne Betreff')}"
        correspondence_list += f"\n  Empfänger: {c.get('recipient', 'Unbekannt')}"
        correspondence_list += f"\n  Zweck: {c.get('purpose', c.get('type', ''))}"
        correspondence_list += f"\n  Kontext: {c.get('context', '')}"
        correspondence_list += f"\n  Status: {status_text}{sent_info}"
        correspondence_list += f"\n  Inhalt (Auszug): {c.get('content', '')[:200]}..."
        correspondence_list += "\n"
    
    system_prompt = """Du bist ein Assistent der Korrespondenz durchsucht.

Analysiere die Anfrage des Benutzers und finde passende Korrespondenz aus der Liste.
Antworte NUR mit validem JSON:
{
    "found": true/false,
    "matching_ids": ["id1", "id2"],
    "summary": "Zusammenfassung was gefunden wurde und wann",
    "details": "Detaillierte Antwort auf die Benutzeranfrage"
}"""

    prompt = f"""BENUTZERANFRAGE: {query}

VORHANDENE KORRESPONDENZ:
{correspondence_list}

Finde relevante Korrespondenz und gib eine hilfreiche Antwort."""

    try:
        result = await ai_service.generate(prompt, system_prompt, max_tokens=1000)
        
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            search_result = json.loads(json_match.group())
            
            # Get full correspondence for matching IDs
            matching_ids = search_result.get("matching_ids", [])
            matching_correspondence = [c for c in all_correspondence if c["id"] in matching_ids]
            
            return {
                "success": True,
                "found": search_result.get("found", False),
                "summary": search_result.get("summary", ""),
                "details": search_result.get("details", ""),
                "results": matching_correspondence
            }
    except Exception as e:
        logger.error(f"Correspondence search error: {e}")
    
    return {
        "success": True,
        "found": False,
        "message": "Suche konnte nicht durchgeführt werden.",
        "results": []
    }


@router.post("/ai/send-correspondence/{correspondence_id}")
async def send_correspondence_via_ai(
    correspondence_id: str,
    mail_account_id: str = Form(...),
    recipient_email: str = Form(...),
    user: dict = Depends(require_auth)
):
    """
    Send a correspondence/email draft via SMTP.
    """
    from response_service import ResponseGeneratorService
    from ai_service import get_ai_service
    
    # Check if mail account has SMTP configured
    mail_account = await db.mail_accounts.find_one(
        {"id": mail_account_id, "user_id": user["id"]},
        {"_id": 0}
    )
    
    if not mail_account:
        return {"success": False, "error": "E-Mail-Konto nicht gefunden"}
    
    if not mail_account.get("smtp_server"):
        return {
            "success": False,
            "error": "SMTP ist für dieses E-Mail-Konto nicht konfiguriert. Bitte konfigurieren Sie SMTP in den E-Mail-Kontoeinstellungen."
        }
    
    ai_service = await get_ai_service(db)
    response_service = ResponseGeneratorService(db, ai_service)
    
    result = await response_service.send_via_email(
        correspondence_id, user["id"], mail_account_id, recipient_email
    )
    
    if result.get("success"):
        # Update correspondence with tracking info
        now = datetime.now(timezone.utc).isoformat()
        await db.correspondence.update_one(
            {"id": correspondence_id},
            {"$set": {
                "status": "sent",
                "sent_at": now,
                "sent_to": recipient_email,
                "sent_via": "smtp"
            }}
        )
        await log_action(user["id"], "send_email_via_ai", "correspondence", correspondence_id, {"recipient": recipient_email})
    
    return result


@router.post("/ai/generate-email")
async def generate_email_with_ai(
    data: dict,
    user: dict = Depends(require_auth)
):
    """Generate email content using AI (Ollama or OpenAI)"""
    prompt = data.get("prompt", "")
    context = data.get("context", {})
    document_id = data.get("document_id")
    email_id = data.get("email_id")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt erforderlich")
    
    try:
        from ai_service import get_ai_service
        ai_service = await get_ai_service(db)
        
        # Check if AI is available
        availability = await ai_service.check_availability()
        if not availability["ollama"]["available"] and not availability["openai"]["available"]:
            raise HTTPException(
                status_code=503, 
                detail="KI-Service nicht verfügbar. Bitte aktivieren Sie Ollama (lokal) oder fügen Sie einen OpenAI API-Key in den Einstellungen hinzu."
            )
        
        # Build context from document or email if provided
        context_info = ""
        
        if document_id:
            doc = await db.documents.find_one({"id": document_id, "user_id": user["id"]}, {"_id": 0})
            if doc:
                doc_name = context.get("document_name") or doc.get("display_name") or doc.get("original_filename")
                doc_summary = context.get("document_summary") or doc.get("ai_summary") or ""
                doc_text = doc.get("ocr_text", "")[:2000]
                context_info = f"\n\nKONTEXT - DOKUMENT '{doc_name}':\nZusammenfassung: {doc_summary}\nInhalt (Auszug): {doc_text}"
        
        if email_id:
            email = await db.emails.find_one({"id": email_id, "user_id": user["id"]}, {"_id": 0})
            if email:
                email_subject = context.get("email_subject") or email.get("subject", "")
                email_from = context.get("email_from") or email.get("from_name") or email.get("from_address", "")
                email_content = context.get("email_content") or email.get("body_text", "")[:2000]
                context_info = f"\n\nKONTEXT - E-MAIL von {email_from}:\nBetreff: {email_subject}\nInhalt (Auszug): {email_content}"
        
        # Build AI prompt for email generation
        recipient = context.get("recipient", "")
        existing_subject = context.get("subject", "")
        
        system_prompt = """Du bist ein professioneller E-Mail-Assistent für eine Rechtskanzlei/Dokumentenverwaltung.
Deine Aufgabe ist es, professionelle, höfliche und gut strukturierte E-Mails auf Deutsch zu verfassen.

Wichtige Regeln:
- Verwende eine höfliche, förmliche Anrede (Sehr geehrte/r...)
- Halte die E-Mail klar und präzise
- Beende mit einer höflichen Grußformel (Mit freundlichen Grüßen)
- Füge keine Platzhalter wie [Name] ein - verwende allgemeine Anreden wenn nötig
- Die Antwort muss im folgenden JSON-Format sein:

{
  "subject": "Betreffzeile der E-Mail",
  "body": "Der vollständige E-Mail-Text"
}"""
        
        user_prompt = f"""Erstelle eine E-Mail basierend auf folgender Beschreibung:

{prompt}

{f"Empfänger: {recipient}" if recipient else ""}
{f"Bisheriger Betreff: {existing_subject}" if existing_subject else ""}
{context_info}

Antworte NUR mit dem JSON-Objekt."""
        
        # Use generate() method instead of non-existent chat()
        response_text = await ai_service.generate(user_prompt, system_prompt, max_tokens=1500)
        
        # Try to parse JSON from response
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response_text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            email_data = json.loads(content.strip())
            
            return {
                "success": True,
                "subject": email_data.get("subject", ""),
                "body": email_data.get("body", "")
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract content manually
            logger.warning(f"Could not parse AI response as JSON: {response_text[:200]}")
            
            # Fallback: use the content as body
            return {
                "success": True,
                "subject": existing_subject or "Ihre Anfrage",
                "body": response_text
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI email generation error: {e}")
        raise HTTPException(status_code=500, detail=f"E-Mail-Generierung fehlgeschlagen: {str(e)}")
