# 🤖 CaseDesk AI - KI-Assistent Anleitung

## 📋 Übersicht

Der CaseDesk KI-Assistent kann automatisch **Termine, Aufgaben, Fälle und E-Mails** erstellen, basierend auf natürlicher Sprache oder Dokumenten-Inhalten.

---

## 📅 **Termine automatisch erstellen**

### **Via Chat-Assistent:**

Öffnen Sie den **KI-Assistenten** und sagen Sie zum Beispiel:

```
"Erstelle einen Termin am 15. April um 14:00 Uhr für Zahnarzt"
```

```
"Termin morgen um 10 Uhr: Meeting mit Anwalt"
```

```
"Geburtstag von Maria am 20. Mai" (wird als Ganztags-Termin erstellt)
```

**Der Assistent wird:**
1. Das Datum und die Uhrzeit erkennen
2. Einen Termin-Vorschlag erstellen
3. Sie um Bestätigung bitten
4. Den Termin im Kalender speichern

---

### **Aus Dokumenten/E-Mails automatisch:**

Wenn Sie ein Dokument oder eine E-Mail hochladen, die Termine enthält, wird der KI-Assistent automatisch:

1. **Termine erkennen** (z.B. "Gerichtstermin am 20.04.2026 um 10:00 Uhr")
2. **Kalendereinträge vorschlagen**
3. **Sie fragen, ob Sie die Termine übernehmen möchten**

**Beispiel E-Mail:**
```
Sehr geehrter Herr Trenter,

Ihr Gerichtstermin findet am 20. April 2026 um 10:00 Uhr
im Amtsgericht Köln, Raum 302 statt.

Mit freundlichen Grüßen
```

**→ KI erstellt automatisch:**
- **Titel:** "Gerichtstermin"
- **Datum:** 20.04.2026
- **Uhrzeit:** 10:00 - 11:00 Uhr
- **Ort:** Amtsgericht Köln, Raum 302

---

## ✅ **Aufgaben automatisch erstellen**

### **Via Chat:**

```
"Erstelle eine Aufgabe: Steuererklärung bis 31. Mai"
```

```
"Aufgabe mit hoher Priorität: Versicherung kontaktieren"
```

**Der Assistent erstellt:**
- Aufgabe mit erkannter Frist
- Priorität (basierend auf Kontext)
- Optional: Verknüpfung mit Fall

---

## 📁 **Fälle automatisch erstellen**

```
"Erstelle einen Fall: Verkehrsunfall vom 12.03.2026"
```

```
"Neuer Fall: Mietstreit mit Vermieter Müller"
```

---

## 📧 **E-Mails schreiben lassen**

```
"Schreibe eine E-Mail an die Krankenkasse wegen Kostenübernahme"
```

```
"Antworte auf die E-Mail von Anwalt Schmidt"
```

**Der Assistent:**
1. Erstellt einen Entwurf basierend auf Ihrem Profil
2. Nutzt Informationen aus verknüpften Dokumenten
3. Schlägt Betreff und Text vor
4. Sie können den Entwurf bearbeiten und versenden

---

## 🧠 **Was der KI-Assistent alles weiß:**

### ✅ **Vollständiger Zugriff auf:**
- **Alle Dokumente** (mit Inhalt)
- **Alle E-Mails** (Betreff + Body)
- **Alle Fälle** (Beschreibungen, Aktenzeichen)
- **Alle Aufgaben** (offene Fristen)
- **Alle Termine** (kommende Events)
- **Ihr Profil** (Name, Adresse, Arbeitgeber, etc.)

### 🔍 **Kann:**
- Informationen aus Dokumenten extrahieren
- Verbindungen zwischen E-Mails/Dokumenten/Fällen herstellen
- Termine und Fristen erkennen
- Zusammenfassungen erstellen
- Dokumente zu Fällen vorschlagen
- Budgetpläne aus Kontoauszügen erstellen
- Versicherungspolicen analysieren

---

## 💡 **Beispiel-Konversationen:**

### **Termine aus E-Mail extrahieren:**

**Sie:**
> "Ich habe gerade eine E-Mail von meinem Arzt bekommen. Kannst du einen Termin daraus erstellen?"

**Assistent:**
> "Ich habe die E-Mail gefunden: 'Terminbestätigung Dr. Schmidt'. Darin steht ein Termin am 18. April 2026 um 15:30 Uhr. Soll ich diesen Termin im Kalender eintragen?"

**Sie:**
> "Ja, bitte!"

**Assistent:**
> "✓ Termin 'Dr. Schmidt' am 18.04.2026 um 15:30 Uhr wurde erstellt. Möchtest du eine Erinnerung 1 Tag vorher?"

---

### **Dokument-Analyse:**

**Sie:**
> "Was steht in meinem Versicherungsvertrag?"

**Assistent:**
> "In deinem Versicherungsvertrag 'Haftpflichtversicherung_2024.pdf' sind folgende wichtige Punkte:
> - Versicherungssumme: 10 Mio. €
> - Jahresbeitrag: 89,50 €
> - Laufzeit bis: 31.12.2026
> - Kündigungsfrist: 3 Monate zum Jahresende
> 
> Soll ich eine Erinnerung für die Kündigungsfrist erstellen?"

---

### **Frist-Überwachung:**

**Sie:**
> "Welche Fristen habe ich diese Woche?"

**Assistent:**
> "Diese Woche hast du folgende Fristen:
> 1. **Steuererklärung** - Fällig: Freitag, 11.04.2026 (in 3 Tagen)
> 2. **Versicherung kontaktieren** - Fällig: Montag, 08.04.2026 (heute!)
> 
> Möchtest du, dass ich dir morgen eine Erinnerung für die Steuererklärung sende?"

---

## ⚙️ **Einstellungen:**

### **KI-Provider wählen:**

1. Gehen Sie zu **Einstellungen** → **AI**
2. Wählen Sie:
   - **OpenAI** (benötigt API-Key) - Beste Qualität
   - **Ollama (Lokal)** - Kostenlos, läuft auf Ihrem Server

---

## 🔒 **Datenschutz:**

- **Ollama (Lokal):** Alle Daten bleiben auf Ihrem Server
- **OpenAI:** Daten werden an OpenAI gesendet (verschlüsselt)
- **Ihre Dokumente:** Werden NIEMALS ohne Ihre Zustimmung weitergegeben

---

## 🆘 **Probleme?**

### **"KI antwortet nicht":**
1. Prüfen Sie Einstellungen → AI → API-Key ist korrekt
2. Prüfen Sie Backend-Logs: `docker logs casedesk-backend --tail 50`

### **"Termine werden nicht automatisch erstellt":**
1. Öffnen Sie Browser-Konsole (F12)
2. Schauen Sie nach Fehlermeldungen
3. Prüfen Sie, ob die Events-API funktioniert: `/api/events`

---

**Viel Erfolg mit Ihrem KI-Assistenten! 🚀**
