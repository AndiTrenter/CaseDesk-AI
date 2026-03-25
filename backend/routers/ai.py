"""AI Chat & Proactive Router"""
from fastapi import APIRouter, HTTPException, Depends, Form
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from deps import db, require_auth, log_action, get_user_language

logger = logging.getLogger(__name__)
router = APIRouter()


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
    
    context["all_documents"] = all_docs
    context["all_cases"] = all_cases
    
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
    
    return {
        "success": True,
        "response": ai_response,
        "session_id": session_id,
        "referenced_documents": referenced_docs
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
