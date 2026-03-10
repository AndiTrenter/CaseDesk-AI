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
    """AI Chat Assistant for document and case queries"""
    
    def __init__(self, ai_service: AIService):
        self.ai = ai_service
    
    async def chat(
        self, 
        message: str, 
        context: Dict[str, Any] = None,
        language: str = "de"
    ) -> str:
        """
        Process chat message with context awareness
        """
        
        lang_instruction = "Antworte auf Deutsch." if language == "de" else "Answer in English."
        
        system_prompt = f"""Du bist CaseDesk AI, ein hilfreicher Assistent für Dokumenten- und Fallverwaltung.

{lang_instruction}

Deine Aufgaben:
- Fragen zu Dokumenten, Fällen, E-Mails und Aufgaben beantworten
- Zusammenfassungen erstellen
- Bei der Formulierung von Antwortschreiben helfen
- Fristen und wichtige Termine hervorheben
- Bei Behördenangelegenheiten den besten legitimen Weg aufzeigen

WICHTIGE REGELN:
- NIEMALS Fakten erfinden
- NIEMALS falsche Angaben machen
- Bei Unsicherheit nachfragen
- Nur auf Basis der vorhandenen Daten arbeiten
- Quellen und Dokumente referenzieren"""

        # Add context if available
        context_text = ""
        if context:
            if context.get("case"):
                case = context["case"]
                context_text += f"\n\nAktueller Fall: {case.get('title')}\nBeschreibung: {case.get('description')}\nStatus: {case.get('status')}"
            
            if context.get("documents"):
                context_text += "\n\nVerknüpfte Dokumente:"
                for doc in context["documents"][:5]:
                    context_text += f"\n- {doc.get('display_name', doc.get('original_filename'))}"
                    if doc.get("ocr_text"):
                        context_text += f"\n  Inhalt (Auszug): {doc['ocr_text'][:500]}..."
            
            if context.get("tasks"):
                context_text += "\n\nOffene Aufgaben:"
                for task in context["tasks"][:5]:
                    context_text += f"\n- {task.get('title')} (Fällig: {task.get('due_date', 'nicht gesetzt')})"

        prompt = message
        if context_text:
            prompt = f"Kontext:{context_text}\n\nFrage: {message}"

        return await self.ai.generate(prompt, system_prompt)


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
