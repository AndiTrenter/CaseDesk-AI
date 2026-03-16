"""
CaseDesk AI - AI Service
Abstraction layer for local (Ollama) and external (OpenAI) AI providers
"""
import os
import httpx
import json
import re
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')


class AIService:
    """AI Service supporting Ollama (local) and OpenAI (external)"""
    
    def __init__(self, provider: str = "ollama", api_key: str = None):
        self.provider = provider
        self.api_key = api_key or OPENAI_API_KEY
        self.ollama_url = OLLAMA_URL
        self.model = "llama3.2" if provider == "ollama" else "gpt-4"
    
    async def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
        """Generate text using configured AI provider"""
        if self.provider == "ollama":
            return await self._generate_ollama(prompt, system_prompt)
        elif self.provider == "openai" and self.api_key:
            return await self._generate_openai(prompt, system_prompt, max_tokens)
        else:
            return "AI ist nicht konfiguriert. Bitte aktivieren Sie Ollama oder OpenAI in den Einstellungen."
    
    async def _generate_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Generate using local Ollama"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "")
                else:
                    logger.error(f"Ollama error: {response.status_code} - {response.text}")
                    return f"Ollama Fehler: {response.status_code}"
                    
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama service")
            return "Ollama-Service nicht erreichbar. Bitte starten Sie den Ollama-Container."
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"KI-Fehler: {str(e)}"
    
    async def _generate_openai(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
        """Generate using OpenAI API"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return f"OpenAI Fehler: {str(e)}"
    
    async def check_availability(self) -> Dict[str, Any]:
        """Check if AI services are available"""
        result = {
            "ollama": {"available": False, "model": None},
            "openai": {"available": bool(self.api_key)}
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    result["ollama"]["available"] = True
                    result["ollama"]["models"] = models
                    result["ollama"]["model"] = self.model if self.model in models else (models[0] if models else None)
        except:
            pass
        
        return result


class DocumentAnalyzer:
    """AI-powered document analysis for metadata extraction"""
    
    def __init__(self, ai_service: AIService):
        self.ai = ai_service
    
    async def analyze_document(self, ocr_text: str, filename: str = None) -> Dict[str, Any]:
        """
        Analyze OCR text and extract:
        - date (Datum)
        - sender (Absender)
        - document_type (Dokumenttyp)
        - reference (Referenz/Aktenzeichen)
        - subject (Kurzthema)
        - tags
        - deadlines
        """
        
        system_prompt = """Du bist ein Experte für Dokumentenanalyse. Analysiere den folgenden Dokumenttext und extrahiere die Metadaten.

WICHTIG: Antworte NUR mit einem validen JSON-Objekt, keine anderen Texte.

Das JSON muss folgende Felder enthalten:
{
    "datum": "YYYY-MM-DD oder null wenn nicht erkennbar",
    "absender": "Name/Organisation des Absenders oder null",
    "dokumenttyp": "einer von: Brief, Rechnung, Vertrag, Formular, Bescheid, Mahnung, Antrag, Mitteilung, Kontoauszug, Steuerbescheid, Versicherung, Sonstiges",
    "referenz": "Aktenzeichen, Vertragsnummer, Rechnungsnummer etc. oder null",
    "kurzthema": "Kurze Beschreibung in 2-5 Wörtern",
    "tags": ["liste", "relevanter", "schlagwörter"],
    "fristen": ["Liste von erkannten Fristen im Format YYYY-MM-DD"],
    "zusammenfassung": "Kurze Zusammenfassung in 1-2 Sätzen",
    "wichtigkeit": "hoch/mittel/niedrig basierend auf Inhalt"
}"""

        prompt = f"""Analysiere dieses Dokument:

Dateiname: {filename or 'Unbekannt'}

Dokumentinhalt:
{ocr_text[:4000]}  # Limit to avoid token overflow

Extrahiere die Metadaten als JSON."""

        try:
            response = await self.ai.generate(prompt, system_prompt)
            
            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                metadata = json.loads(json_match.group())
                return {
                    "success": True,
                    "metadata": metadata
                }
            else:
                logger.warning(f"Could not parse JSON from AI response: {response[:200]}")
                return {
                    "success": False,
                    "error": "JSON konnte nicht extrahiert werden",
                    "raw_response": response
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {
                "success": False,
                "error": f"JSON Parse Fehler: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_filename(self, metadata: Dict[str, Any], original_ext: str = ".pdf") -> str:
        """
        Generate standardized filename:
        Format: Datum – Absender – Dokumenttyp – Referenz – Kurzthema.ext
        """
        parts = []
        
        # Datum
        datum = metadata.get("datum")
        if datum and datum != "null":
            parts.append(datum)
        else:
            parts.append(datetime.now().strftime("%Y-%m-%d"))
        
        # Absender
        absender = metadata.get("absender")
        if absender and absender != "null":
            # Clean for filename
            absender = re.sub(r'[<>:"/\\|?*]', '', absender)[:30]
            parts.append(absender)
        
        # Dokumenttyp
        dokumenttyp = metadata.get("dokumenttyp", "Sonstiges")
        parts.append(dokumenttyp)
        
        # Referenz
        referenz = metadata.get("referenz")
        if referenz and referenz != "null":
            referenz = re.sub(r'[<>:"/\\|?*]', '', referenz)[:20]
            parts.append(referenz)
        
        # Kurzthema
        kurzthema = metadata.get("kurzthema")
        if kurzthema and kurzthema != "null":
            kurzthema = re.sub(r'[<>:"/\\|?*]', '', kurzthema)[:40]
            parts.append(kurzthema)
        
        # Join with " – " and add extension
        filename = " – ".join(parts) + original_ext
        
        return filename


class ChatAssistant:
    """AI Chat Assistant for document and case queries - Full Knowledge Agent"""
    
    def __init__(self, ai_service: AIService):
        self.ai = ai_service
    
    async def chat(
        self, 
        message: str, 
        context: Dict[str, Any] = None,
        language: str = "de"
    ) -> str:
        """
        Process chat message with full document knowledge
        The assistant knows about ALL user documents and can make cross-references
        """
        
        lang_instruction = "Antworte auf Deutsch." if language == "de" else "Answer in English."
        
        system_prompt = f"""Du bist CaseDesk AI, ein persönlicher KI-Assistent und Agent für Dokumenten- und Fallverwaltung.
Du hast vollständigen Zugriff auf ALLE Dokumente, Fälle, Aufgaben und Termine des Benutzers.

{lang_instruction}

DEINE FÄHIGKEITEN:
1. **Dokumentenwissen**: Du kennst alle Dokumente des Benutzers und kannst:
   - Inhalte zusammenfassen
   - Verbindungen zwischen Dokumenten erkennen (z.B. gleicher Absender, ähnliches Thema)
   - Relevante Dokumente für Anfragen finden
   - Fristen und wichtige Daten identifizieren

2. **Fallunterstützung**: Du kannst:
   - Dokumente zu passenden Fällen vorschlagen
   - Querverweise zwischen Fällen und Dokumenten herstellen
   - Bei der Vorbereitung von Antworten helfen

3. **Persönliche Assistenz**: Du kannst:
   - Aufgaben und Termine im Blick behalten
   - An Fristen erinnern
   - Handlungsempfehlungen geben
   - Bei Behördenangelegenheiten den besten legitimen Weg aufzeigen

4. **Proaktive Hilfe**: Du analysierst aktiv:
   - Welche Dokumente zusammengehören könnten
   - Ob Fristen drohen
   - Welche Aufgaben dringend sind

WICHTIGE REGELN:
- NIEMALS Fakten erfinden - nur auf Basis der vorhandenen Daten arbeiten
- Bei Unsicherheit nachfragen
- Dokumente klar referenzieren (Name, Datum, Absender)
- Praktische, umsetzbare Empfehlungen geben
- Wenn ein relevantes Dokument zu einem Fall passt, das explizit erwähnen"""

        # Build comprehensive context
        context_text = self._build_context(context, message) if context else ""

        prompt = message
        if context_text:
            prompt = f"{context_text}\n\n---\nBenutzeranfrage: {message}"

        return await self.ai.generate(prompt, system_prompt, max_tokens=3000)
    
    def _build_context(self, context: Dict[str, Any], message: str) -> str:
        """Build a comprehensive context string for the AI"""
        parts = []
        
        # Current case context
        if context.get("current_case"):
            case = context["current_case"]
            parts.append(f"## AKTUELLER FALL\nTitel: {case.get('title')}\nBeschreibung: {case.get('description')}\nStatus: {case.get('status')}\nAktenzeichen: {case.get('reference_number', 'Nicht angegeben')}")
            
            if context.get("case_documents"):
                parts.append("\n### Dokumente in diesem Fall:")
                for doc in context["case_documents"]:
                    doc_info = f"- **{doc.get('display_name', doc.get('original_filename'))}**"
                    if doc.get('sender'):
                        doc_info += f" | Absender: {doc['sender']}"
                    if doc.get('document_date'):
                        doc_info += f" | Datum: {doc['document_date']}"
                    if doc.get('ai_summary'):
                        doc_info += f"\n  Zusammenfassung: {doc['ai_summary']}"
                    if doc.get('ocr_text'):
                        doc_info += f"\n  Inhalt (Auszug): {doc['ocr_text'][:800]}..."
                    parts.append(doc_info)
        
        # All documents overview
        if context.get("all_documents"):
            parts.append("\n## ALLE DOKUMENTE DES BENUTZERS")
            for doc in context["all_documents"][:50]:  # Limit to 50 docs
                doc_info = f"- **{doc.get('display_name', doc.get('original_filename'))}**"
                if doc.get('sender'):
                    doc_info += f" | Von: {doc['sender']}"
                if doc.get('document_type'):
                    doc_info += f" | Typ: {doc['document_type']}"
                if doc.get('tags'):
                    doc_info += f" | Tags: {', '.join(doc['tags'][:5])}"
                if doc.get('case_id'):
                    # Find case name
                    for c in context.get("all_cases", []):
                        if c["id"] == doc["case_id"]:
                            doc_info += f" | Fall: {c['title']}"
                            break
                if doc.get('ai_summary'):
                    doc_info += f"\n  → {doc['ai_summary'][:200]}"
                parts.append(doc_info)
        
        # All cases overview
        if context.get("all_cases"):
            parts.append("\n## ALLE FÄLLE")
            for case in context["all_cases"]:
                case_info = f"- **{case.get('title')}** | Status: {case.get('status')}"
                if case.get('reference_number'):
                    case_info += f" | Aktenzeichen: {case['reference_number']}"
                if case.get('description'):
                    case_info += f"\n  {case['description'][:150]}"
                parts.append(case_info)
        
        # Open tasks
        if context.get("open_tasks"):
            parts.append("\n## OFFENE AUFGABEN")
            for task in context["open_tasks"]:
                task_info = f"- **{task.get('title')}**"
                if task.get('due_date'):
                    task_info += f" | Fällig: {task['due_date']}"
                if task.get('priority'):
                    task_info += f" | Priorität: {task['priority']}"
                parts.append(task_info)
        
        # Upcoming events
        if context.get("upcoming_events"):
            parts.append("\n## ANSTEHENDE TERMINE")
            for event in context["upcoming_events"]:
                event_info = f"- **{event.get('title')}** | {event.get('start_date')}"
                parts.append(event_info)
        
        return "\n".join(parts)


async def get_ai_service(db) -> AIService:
    """Get configured AI service from database settings"""
    settings = await db.system_settings.find_one({}, {"_id": 0})
    
    if not settings:
        # Default to Ollama
        return AIService(provider="ollama")
    
    provider = settings.get("ai_provider", "ollama")
    api_key = settings.get("openai_api_key")
    
    if provider == "disabled":
        provider = "ollama"  # Fallback to Ollama even if "disabled"
    
    return AIService(provider=provider, api_key=api_key)


class ProactiveAssistant:
    """Proactive AI Assistant that automatically prepares relevant information"""
    
    def __init__(self, ai_service: AIService, db):
        self.ai = ai_service
        self.db = db
    
    async def find_related_documents(self, user_id: str, query: str = None, 
                                    sender: str = None, tags: List[str] = None,
                                    reference: str = None, limit: int = 10) -> List[Dict]:
        """Find documents related to given criteria"""
        # Build search query
        search_conditions = {"user_id": user_id}
        
        # Text search if query provided
        if query:
            # Use MongoDB text search
            documents = await self.db.documents.find(
                {"user_id": user_id, "$text": {"$search": query}},
                {"_id": 0, "score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list(limit)
            return documents
        
        # Search by sender
        if sender:
            search_conditions["sender"] = {"$regex": sender, "$options": "i"}
        
        # Search by tags
        if tags:
            search_conditions["tags"] = {"$in": tags}
            
        # Search by reference number
        if reference:
            search_conditions["$or"] = [
                {"ocr_text": {"$regex": reference, "$options": "i"}},
                {"display_name": {"$regex": reference, "$options": "i"}}
            ]
        
        documents = await self.db.documents.find(
            search_conditions, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return documents
    
    async def suggest_documents_for_case(self, user_id: str, case_title: str, 
                                         case_description: str = None) -> Dict[str, Any]:
        """Suggest relevant documents when creating or viewing a case"""
        
        # Get all user documents
        all_docs = await self.db.documents.find(
            {"user_id": user_id},
            {"_id": 0, "id": 1, "display_name": 1, "original_filename": 1, 
             "sender": 1, "document_type": 1, "tags": 1, "ai_summary": 1,
             "document_date": 1, "ocr_text": 1}
        ).sort("created_at", -1).to_list(100)
        
        if not all_docs:
            return {"suggestions": [], "analysis": "Keine Dokumente vorhanden."}
        
        # Use AI to find relevant documents
        system_prompt = """Du bist ein Experte für Dokumentenanalyse und Fallzuordnung.
Analysiere den Falltitel und die Beschreibung und finde die relevantesten Dokumente.

WICHTIG: Antworte NUR mit einem validen JSON-Objekt:
{
    "relevant_document_ids": ["id1", "id2", ...],
    "relevanz_erklaerung": {
        "id1": "Warum dieses Dokument relevant ist",
        "id2": "Warum dieses Dokument relevant ist"
    },
    "empfohlene_aktionen": ["Aktion 1", "Aktion 2"],
    "erkannte_zusammenhaenge": "Beschreibung erkannter Zusammenhänge zwischen Dokumenten",
    "moegliche_fristen": ["Frist 1 mit Datum", "Frist 2 mit Datum"],
    "fehlende_dokumente": ["Was könnte noch fehlen"]
}"""

        # Build document list for AI
        doc_list = []
        for doc in all_docs:
            doc_info = f"ID: {doc['id']}\n"
            doc_info += f"Name: {doc.get('display_name', doc.get('original_filename'))}\n"
            if doc.get('sender'):
                doc_info += f"Absender: {doc['sender']}\n"
            if doc.get('document_type'):
                doc_info += f"Typ: {doc['document_type']}\n"
            if doc.get('tags'):
                doc_info += f"Tags: {', '.join(doc['tags'])}\n"
            if doc.get('ai_summary'):
                doc_info += f"Zusammenfassung: {doc['ai_summary']}\n"
            if doc.get('ocr_text'):
                doc_info += f"Inhalt (Auszug): {doc['ocr_text'][:500]}...\n"
            doc_list.append(doc_info)
        
        prompt = f"""FALL:
Titel: {case_title}
Beschreibung: {case_description or 'Nicht angegeben'}

VERFÜGBARE DOKUMENTE:
{chr(10).join(doc_list)}

Finde die relevantesten Dokumente für diesen Fall und analysiere Zusammenhänge."""

        try:
            response = await self.ai.generate(prompt, system_prompt, max_tokens=2000)
            
            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Get full document info for suggested IDs
                suggested_docs = []
                for doc_id in analysis.get("relevant_document_ids", []):
                    for doc in all_docs:
                        if doc["id"] == doc_id:
                            doc["relevanz"] = analysis.get("relevanz_erklaerung", {}).get(doc_id, "")
                            suggested_docs.append(doc)
                            break
                
                return {
                    "success": True,
                    "suggestions": suggested_docs,
                    "analysis": analysis
                }
            else:
                return {"success": False, "suggestions": [], "analysis": response}
                
        except Exception as e:
            logger.error(f"Document suggestion error: {e}")
            return {"success": False, "suggestions": [], "error": str(e)}
    
    async def analyze_case_proactively(self, user_id: str, case_id: str) -> Dict[str, Any]:
        """Proactively analyze a case and provide recommendations"""
        
        # Get case
        case = await self.db.cases.find_one({"id": case_id, "user_id": user_id}, {"_id": 0})
        if not case:
            return {"success": False, "error": "Fall nicht gefunden"}
        
        # Get case documents
        case_docs = []
        if case.get("document_ids"):
            case_docs = await self.db.documents.find(
                {"id": {"$in": case["document_ids"]}, "user_id": user_id},
                {"_id": 0}
            ).to_list(50)
        
        # Get ALL user documents for cross-reference
        all_docs = await self.db.documents.find(
            {"user_id": user_id, "id": {"$nin": case.get("document_ids", [])}},
            {"_id": 0, "id": 1, "display_name": 1, "sender": 1, "tags": 1, 
             "ai_summary": 1, "document_date": 1, "ocr_text": 1}
        ).to_list(100)
        
        # Get open tasks
        open_tasks = await self.db.tasks.find(
            {"user_id": user_id, "case_id": case_id, "status": {"$ne": "done"}},
            {"_id": 0}
        ).to_list(20)
        
        # Get correspondence
        correspondence = await self.db.correspondence.find(
            {"case_id": case_id, "user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(10)
        
        system_prompt = """Du bist ein proaktiver KI-Assistent für Fallbearbeitung.
Analysiere den Fall und alle zugehörigen Daten umfassend.

WICHTIG: Antworte NUR mit einem validen JSON-Objekt:
{
    "status_zusammenfassung": "Kurze Zusammenfassung des aktuellen Fallstatus",
    "dringende_aktionen": [
        {"aktion": "Was zu tun ist", "grund": "Warum dringend", "prioritaet": "hoch/mittel/niedrig"}
    ],
    "erkannte_fristen": [
        {"frist": "Datum oder Zeitraum", "quelle": "Woher die Frist stammt", "aktion_erforderlich": "Was zu tun ist"}
    ],
    "fehlende_dokumente": [
        {"dokument": "Was fehlt", "warum_wichtig": "Warum es benötigt wird"}
    ],
    "zusaetzliche_dokumente_vorschlag": [
        {"dokument_id": "ID", "grund": "Warum es zum Fall gehören könnte"}
    ],
    "naechster_schritt": {
        "empfehlung": "Was als nächstes zu tun ist",
        "begruendung": "Warum dieser Schritt"
    },
    "warnungen": ["Wichtige Warnungen oder Risiken"],
    "zusammenhaenge": "Erkannte Verbindungen zu anderen Dokumenten oder Fällen"
}"""

        # Build context
        case_docs_text = ""
        for doc in case_docs:
            case_docs_text += f"\n--- Dokument: {doc.get('display_name', doc.get('original_filename'))} ---\n"
            if doc.get('sender'):
                case_docs_text += f"Absender: {doc['sender']}\n"
            if doc.get('document_date'):
                case_docs_text += f"Datum: {doc['document_date']}\n"
            if doc.get('ai_summary'):
                case_docs_text += f"Zusammenfassung: {doc['ai_summary']}\n"
            if doc.get('ocr_text'):
                case_docs_text += f"Inhalt:\n{doc['ocr_text'][:1500]}\n"
        
        other_docs_text = ""
        for doc in all_docs[:30]:  # Limit for token management
            other_docs_text += f"\n- {doc.get('display_name', 'Unbekannt')} (ID: {doc['id']})"
            if doc.get('sender'):
                other_docs_text += f" | Von: {doc['sender']}"
            if doc.get('ai_summary'):
                other_docs_text += f"\n  {doc['ai_summary'][:100]}"
        
        tasks_text = ""
        for task in open_tasks:
            tasks_text += f"\n- {task.get('title')} (Fällig: {task.get('due_date', 'Nicht gesetzt')}, Priorität: {task.get('priority', 'normal')})"
        
        corr_text = ""
        for corr in correspondence:
            corr_text += f"\n- {corr.get('type')}: {corr.get('subject')} ({corr.get('status')}) - {corr.get('created_at', '')[:10]}"
        
        prompt = f"""FALL: {case.get('title')}
Aktenzeichen: {case.get('reference_number', 'Nicht angegeben')}
Status: {case.get('status')}
Beschreibung: {case.get('description', 'Keine')}

DOKUMENTE IM FALL ({len(case_docs)}):
{case_docs_text if case_docs_text else 'Keine Dokumente'}

OFFENE AUFGABEN ({len(open_tasks)}):
{tasks_text if tasks_text else 'Keine offenen Aufgaben'}

KORRESPONDENZ ({len(correspondence)}):
{corr_text if corr_text else 'Keine Korrespondenz'}

WEITERE DOKUMENTE DES BENUTZERS (für Querverweise):
{other_docs_text if other_docs_text else 'Keine weiteren Dokumente'}

Analysiere den Fall proaktiv und gib umfassende Empfehlungen."""

        try:
            response = await self.ai.generate(prompt, system_prompt, max_tokens=3000)
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis = json.loads(json_match.group())
                return {
                    "success": True,
                    "case_id": case_id,
                    "case_title": case.get("title"),
                    "analysis": analysis,
                    "documents_count": len(case_docs),
                    "tasks_count": len(open_tasks),
                    "correspondence_count": len(correspondence)
                }
            else:
                return {"success": False, "raw_response": response}
                
        except Exception as e:
            logger.error(f"Proactive analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def auto_link_documents(self, user_id: str, document_id: str) -> Dict[str, Any]:
        """Automatically find and suggest links for a document"""
        
        # Get the document
        doc = await self.db.documents.find_one(
            {"id": document_id, "user_id": user_id}, {"_id": 0}
        )
        if not doc:
            return {"success": False, "error": "Dokument nicht gefunden"}
        
        # Get all other documents
        other_docs = await self.db.documents.find(
            {"user_id": user_id, "id": {"$ne": document_id}},
            {"_id": 0, "id": 1, "display_name": 1, "sender": 1, "tags": 1,
             "ai_summary": 1, "ocr_text": 1, "case_id": 1}
        ).to_list(100)
        
        # Get all cases
        cases = await self.db.cases.find(
            {"user_id": user_id},
            {"_id": 0, "id": 1, "title": 1, "description": 1, "reference_number": 1}
        ).to_list(50)
        
        system_prompt = """Du bist ein Experte für Dokumentenverknüpfung.
Analysiere das Dokument und finde Verbindungen zu anderen Dokumenten und Fällen.

WICHTIG: Antworte NUR mit einem validen JSON-Objekt:
{
    "verwandte_dokumente": [
        {"id": "dok_id", "verbindung": "Art der Verbindung", "staerke": "hoch/mittel/niedrig"}
    ],
    "passende_faelle": [
        {"id": "fall_id", "grund": "Warum passend"}
    ],
    "erkannte_referenzen": ["Aktenzeichen, Vertragsnummern etc."],
    "empfohlene_tags": ["tag1", "tag2"],
    "zusammenfassung": "Kurze Analyse der Dokumentenbeziehungen"
}"""

        doc_text = f"""DOKUMENT ZUR ANALYSE:
Name: {doc.get('display_name', doc.get('original_filename'))}
Absender: {doc.get('sender', 'Unbekannt')}
Typ: {doc.get('document_type', 'Unbekannt')}
Tags: {', '.join(doc.get('tags', []))}
Zusammenfassung: {doc.get('ai_summary', 'Keine')}
Inhalt: {doc.get('ocr_text', '')[:2000]}

ANDERE DOKUMENTE:
"""
        for od in other_docs[:50]:
            doc_text += f"\n- ID: {od['id']} | {od.get('display_name', 'Unbekannt')}"
            if od.get('sender'):
                doc_text += f" | Von: {od['sender']}"
            if od.get('ai_summary'):
                doc_text += f"\n  {od['ai_summary'][:150]}"
        
        doc_text += "\n\nVERFÜGBARE FÄLLE:\n"
        for c in cases:
            doc_text += f"\n- ID: {c['id']} | {c['title']}"
            if c.get('reference_number'):
                doc_text += f" | AZ: {c['reference_number']}"
            if c.get('description'):
                doc_text += f"\n  {c['description'][:100]}"
        
        try:
            response = await self.ai.generate(doc_text, system_prompt, max_tokens=2000)
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis = json.loads(json_match.group())
                return {
                    "success": True,
                    "document_id": document_id,
                    "links": analysis
                }
            else:
                return {"success": False, "raw_response": response}
                
        except Exception as e:
            logger.error(f"Auto-link error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_daily_briefing(self, user_id: str) -> Dict[str, Any]:
        """Generate a daily briefing with important items"""
        
        from datetime import timedelta
        
        today = datetime.now()
        week_ahead = (today + timedelta(days=7)).isoformat()
        today_str = today.isoformat()
        
        # Get upcoming tasks
        upcoming_tasks = await self.db.tasks.find(
            {"user_id": user_id, "status": {"$ne": "done"}, 
             "due_date": {"$lte": week_ahead}},
            {"_id": 0}
        ).sort("due_date", 1).to_list(20)
        
        # Get upcoming events
        upcoming_events = await self.db.events.find(
            {"user_id": user_id, "start_date": {"$gte": today_str, "$lte": week_ahead}},
            {"_id": 0}
        ).sort("start_date", 1).to_list(20)
        
        # Get recent documents (last 7 days)
        week_ago = (today - timedelta(days=7)).isoformat()
        recent_docs = await self.db.documents.find(
            {"user_id": user_id, "created_at": {"$gte": week_ago}},
            {"_id": 0, "id": 1, "display_name": 1, "ai_summary": 1, "tags": 1}
        ).sort("created_at", -1).to_list(10)
        
        # Get open cases
        open_cases = await self.db.cases.find(
            {"user_id": user_id, "status": {"$in": ["open", "in_progress"]}},
            {"_id": 0}
        ).to_list(20)
        
        # Get pending correspondence
        pending_corr = await self.db.correspondence.find(
            {"user_id": user_id, "status": "draft"},
            {"_id": 0}
        ).to_list(10)
        
        system_prompt = """Du bist ein proaktiver persönlicher Assistent.
Erstelle ein hilfreiches Tagesbriefing basierend auf den Daten.

WICHTIG: Antworte NUR mit einem validen JSON-Objekt:
{
    "begruessung": "Personalisierte Begrüßung",
    "prioritaeten_heute": [
        {"item": "Was heute wichtig ist", "grund": "Warum", "typ": "aufgabe/termin/frist"}
    ],
    "anstehende_fristen": [
        {"frist": "Datum", "beschreibung": "Was", "tage_verbleibend": 3}
    ],
    "offene_faelle_status": [
        {"fall": "Fallname", "status": "Status", "naechster_schritt": "Empfehlung"}
    ],
    "unbearbeitete_dokumente": [
        {"dokument": "Name", "empfehlung": "Was damit zu tun"}
    ],
    "entwuerfe_zu_senden": [
        {"entwurf": "Betreff", "empfaenger": "An wen"}
    ],
    "tipp_des_tages": "Ein hilfreicher Tipp basierend auf der Situation",
    "zusammenfassung": "Kurze Zusammenfassung des Tages"
}"""

        context = f"""DATUM: {today.strftime('%d.%m.%Y')}

ANSTEHENDE AUFGABEN ({len(upcoming_tasks)}):
"""
        for task in upcoming_tasks:
            context += f"\n- {task.get('title')} (Fällig: {task.get('due_date', 'Nicht gesetzt')}, Priorität: {task.get('priority', 'normal')})"
        
        context += f"\n\nANSTEHENDE TERMINE ({len(upcoming_events)}):"
        for event in upcoming_events:
            context += f"\n- {event.get('title')} am {event.get('start_date', '')[:10]}"
        
        context += f"\n\nNEUE DOKUMENTE LETZTE 7 TAGE ({len(recent_docs)}):"
        for doc in recent_docs:
            context += f"\n- {doc.get('display_name', 'Unbekannt')}"
            if doc.get('ai_summary'):
                context += f": {doc['ai_summary'][:100]}"
        
        context += f"\n\nOFFENE FÄLLE ({len(open_cases)}):"
        for case in open_cases:
            context += f"\n- {case.get('title')} ({case.get('status')})"
        
        context += f"\n\nUNGESENDETE ENTWÜRFE ({len(pending_corr)}):"
        for corr in pending_corr:
            context += f"\n- {corr.get('subject')} an {corr.get('recipient')}"
        
        try:
            response = await self.ai.generate(context, system_prompt, max_tokens=2000)
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                briefing = json.loads(json_match.group())
                return {
                    "success": True,
                    "date": today.strftime('%d.%m.%Y'),
                    "briefing": briefing,
                    "stats": {
                        "tasks": len(upcoming_tasks),
                        "events": len(upcoming_events),
                        "recent_docs": len(recent_docs),
                        "open_cases": len(open_cases),
                        "pending_drafts": len(pending_corr)
                    }
                }
            else:
                return {"success": False, "raw_response": response}
                
        except Exception as e:
            logger.error(f"Daily briefing error: {e}")
            return {"success": False, "error": str(e)}
