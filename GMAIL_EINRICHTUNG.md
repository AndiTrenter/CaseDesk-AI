# 📧 Gmail-Konto in CaseDesk einrichten

## 🎯 Ziel

Verbinden Sie Ihr Gmail-Konto mit CaseDesk, um E-Mails automatisch abzurufen und zu versenden.

---

## ⚠️ **WICHTIG: Gmail App-Passwort erstellen**

Gmail erlaubt **keine normalen Passwörter** für Drittanbieter-Apps mehr. Sie müssen ein **App-Passwort** erstellen.

---

## 📋 **Schritt 1: Google App-Passwort erstellen**

### **Voraussetzung:**
- Sie müssen **2-Faktor-Authentifizierung (2FA)** in Ihrem Google-Konto aktiviert haben

### **Anleitung:**

1. **Öffnen Sie:** [https://myaccount.google.com/security](https://myaccount.google.com/security)

2. **Scrollen Sie zu:** "Bei Google anmelden"

3. **Klicken Sie auf:** "App-Passwörter" (unten in der Sektion)
   - Falls Sie "App-Passwörter" nicht sehen, aktivieren Sie zuerst **2-Faktor-Authentifizierung**

4. **Geben Sie ein:**
   - **App:** "Mail"
   - **Gerät:** "CaseDesk" (oder einen anderen Namen)

5. **Klicken Sie auf:** "Generieren"

6. **Kopieren Sie das 16-stellige Passwort** (z.B. `abcd efgh ijkl mnop`)
   - ⚠️ **Wichtig:** Notieren Sie sich dieses Passwort, es wird nur einmal angezeigt!

---

## 📋 **Schritt 2: Gmail-Konto in CaseDesk hinzufügen**

### **In CaseDesk:**

1. **Öffnen Sie:** CaseDesk AI

2. **Navigieren Sie zu:** Einstellungen (Zahnrad-Symbol unten links)

3. **Klicken Sie auf den Tab:** "E-Mail-Konten"

4. **Klicken Sie auf:** "+ E-Mail-Konto hinzufügen"

5. **Füllen Sie die Felder aus:**

   **Allgemeine Einstellungen:**
   - **E-Mail-Adresse:** `ihr.name@gmail.com`
   - **Anzeigename:** `Ihr Name` (wird als Absender angezeigt)

   **IMAP (Empfang):**
   - **IMAP-Server:** `imap.gmail.com`
   - **IMAP-Port:** `993`
   - **SSL verwenden:** ✅ (aktiviert)
   - **Passwort:** *Fügen Sie hier das 16-stellige App-Passwort ein (OHNE Leerzeichen)*

   **SMTP (Versand):**
   - **SMTP-Server:** `smtp.gmail.com`
   - **SMTP-Port:** `587`
   - **TLS verwenden:** ✅ (aktiviert)

   **Synchronisation:**
   - **Auto-Sync:** ✅ (aktiviert)
   - **Sync-Intervall:** `5` Minuten (empfohlen)

6. **Klicken Sie auf:** "Verbindung testen"
   - ✅ Sollte "Verbindungstest erfolgreich" anzeigen

7. **Klicken Sie auf:** "Speichern"

---

## 📧 **Schritt 3: E-Mails abrufen**

Nach dem Hinzufügen des Kontos:

1. **Gehen Sie zu:** "E-Mails" (linke Seitenleiste)

2. **Klicken Sie auf:** 🔄 "E-Mails abrufen" (oben rechts)

3. **CaseDesk wird:**
   - Alle neuen E-Mails von Gmail abrufen
   - E-Mails in der Übersicht anzeigen
   - Anhänge automatisch als Dokumente speichern (optional)

---

## 🎯 **Was CaseDesk mit Ihren E-Mails macht:**

### ✅ **Automatisch:**
- **E-Mails abrufen** alle 5 Minuten (konfigurierbar)
- **Anhänge extrahieren** und als Dokumente speichern
- **KI-Analyse:** Termine, Aufgaben und wichtige Informationen erkennen
- **Verknüpfung mit Fällen:** E-Mails können Fällen zugeordnet werden
- **Volltextsuche:** Alle E-Mail-Inhalte durchsuchbar

### 📧 **E-Mails versenden:**
- Direkt aus CaseDesk antworten
- KI kann E-Mail-Entwürfe schreiben
- Vorlagen nutzen
- Anhänge hinzufügen

---

## 🔧 **Troubleshooting**

### **Problem: "IMAP-Authentifizierung fehlgeschlagen"**

**Lösung:**
1. Prüfen Sie, ob Sie das **App-Passwort** verwendet haben (nicht Ihr normales Gmail-Passwort)
2. Entfernen Sie **alle Leerzeichen** aus dem App-Passwort
3. Stellen Sie sicher, dass **2-Faktor-Authentifizierung** aktiviert ist
4. Erstellen Sie ein neues App-Passwort

---

### **Problem: "IMAP-Verbindungsfehler"**

**Lösung:**
1. Prüfen Sie Ihre Internetverbindung
2. Stellen Sie sicher, dass Port `993` (IMAP) nicht durch eine Firewall blockiert wird
3. Versuchen Sie, Gmail in einem Browser zu öffnen (gmail.com), um sicherzustellen, dass Ihr Konto nicht gesperrt ist

---

### **Problem: "SMTP-Authentifizierung fehlgeschlagen"**

**Lösung:**
1. SMTP verwendet **dasselbe App-Passwort** wie IMAP
2. Prüfen Sie, dass `smtp.gmail.com` und Port `587` korrekt sind
3. TLS muss aktiviert sein

---

### **Problem: "E-Mails werden nicht automatisch abgerufen"**

**Lösung:**
1. Prüfen Sie, ob **Auto-Sync** aktiviert ist (Einstellungen → E-Mail-Konten)
2. Prüfen Sie Backend-Logs:
   ```bash
   docker logs casedesk-backend --tail 100 | grep -i "mail\|imap"
   ```
3. Starten Sie den Backend-Container neu:
   ```bash
   docker restart casedesk-backend
   ```

---

## 🔒 **Sicherheit & Datenschutz**

### **Ist mein Gmail-Passwort sicher?**
- ✅ CaseDesk speichert **nur das App-Passwort**, nicht Ihr Haupt-Gmail-Passwort
- ✅ App-Passwörter haben **eingeschränkte Berechtigungen** (nur E-Mail-Zugriff)
- ✅ Sie können App-Passwörter jederzeit in Ihrem Google-Konto **widerrufen**
- ✅ Passwörter werden in der Datenbank gespeichert (MongoDB)

### **Kann CaseDesk alle meine E-Mails lesen?**
- CaseDesk ruft standardmäßig nur **neue E-Mails** ab (seit Installation)
- Alte E-Mails werden **nicht** automatisch importiert
- Sie haben volle Kontrolle über die Synchronisation

---

## 📋 **Übersicht: Gmail-Einstellungen für CaseDesk**

| Einstellung | Wert |
|-------------|------|
| **E-Mail** | `ihr.name@gmail.com` |
| **App-Passwort** | 16-stelliges Passwort von Google |
| **IMAP-Server** | `imap.gmail.com` |
| **IMAP-Port** | `993` |
| **IMAP SSL** | ✅ Ja |
| **SMTP-Server** | `smtp.gmail.com` |
| **SMTP-Port** | `587` |
| **SMTP TLS** | ✅ Ja |
| **Auto-Sync** | ✅ Ja (empfohlen) |
| **Sync-Intervall** | `5` Minuten |

---

## 🎉 **Fertig!**

Ihr Gmail-Konto ist jetzt mit CaseDesk verbunden!

**Nächste Schritte:**
1. Gehen Sie zu "E-Mails" und rufen Sie Ihre ersten Nachrichten ab
2. Nutzen Sie den KI-Assistenten, um E-Mail-Inhalte zu analysieren
3. Verknüpfen Sie E-Mails mit Fällen
4. Lassen Sie die KI automatisch Termine aus E-Mails extrahieren

---

## 💡 **Weitere E-Mail-Provider:**

### **Outlook/Office 365:**
- **IMAP:** `outlook.office365.com:993`
- **SMTP:** `smtp.office365.com:587`
- **App-Passwort:** Nicht nötig, normales Passwort verwenden

### **Yahoo Mail:**
- **IMAP:** `imap.mail.yahoo.com:993`
- **SMTP:** `smtp.mail.yahoo.com:587`
- **App-Passwort:** Erforderlich (ähnlich wie Gmail)

### **Custom Domain (z.B. eigene Domain):**
- Fragen Sie Ihren E-Mail-Provider nach IMAP/SMTP-Einstellungen

---

**Viel Erfolg! 📧**
