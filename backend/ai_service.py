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
