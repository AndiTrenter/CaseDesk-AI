// CaseDesk AI - Internationalization
const translations = {
  en: {
    // Setup Wizard
    setup: {
      title: "Welcome to CaseDesk AI",
      subtitle: "Let's set up your private document management system",
      selectLanguage: "Select Language",
      continue: "Continue",
      back: "Back",
      finish: "Complete Setup",
      step: "Step",
      of: "of",
      // Step 1
      languageTitle: "Language Selection",
      languageDesc: "Choose your preferred language for the interface",
      // Step 2
      adminTitle: "Create Administrator",
      adminDesc: "Set up your admin account to manage the system",
      email: "Email Address",
      username: "Username",
      password: "Password",
      confirmPassword: "Confirm Password",
      fullName: "Full Name (optional)",
      // Step 3
      aiTitle: "AI Configuration",
      aiDesc: "Configure AI features (can be changed later)",
      aiProvider: "AI Provider",
      aiDisabled: "Disabled (Local only)",
      aiOpenai: "OpenAI (ChatGPT)",
      aiLocal: "Local AI",
      apiKey: "OpenAI API Key",
      apiKeyPlaceholder: "sk-...",
      // Step 4
      privacyTitle: "Privacy Settings",
      privacyDesc: "Control how your data is processed",
      internetAccess: "Internet Access",
      internetAllowed: "Allow external connections",
      internetDenied: "Block all external connections",
      privacyNote: "When disabled, all features work offline. No data leaves your server.",
      // Step 5
      completeTitle: "Setup Complete",
      completeDesc: "Your CaseDesk AI instance is ready to use",
      startUsing: "Start Using CaseDesk AI"
    },
    // Auth
    auth: {
      login: "Login",
      logout: "Logout",
      email: "Email",
      password: "Password",
      loginButton: "Sign In",
      loginError: "Invalid credentials"
    },
    // Navigation
    nav: {
      dashboard: "Dashboard",
      documents: "Documents",
      cases: "Cases",
      emails: "Emails",
      calendar: "Calendar",
      tasks: "Tasks",
      drafts: "Drafts",
      aiChat: "AI Assistant",
      settings: "Settings",
      users: "Users"
    },
    // Dashboard
    dashboard: {
      welcome: "Welcome back",
      overview: "Overview",
      openCases: "Open Cases",
      totalDocuments: "Documents",
      pendingTasks: "Pending Tasks",
      upcomingEvents: "Upcoming Events",
      recentDocuments: "Recent Documents",
      urgentTasks: "Urgent Tasks",
      noData: "No data yet"
    },
    // Documents
    documents: {
      title: "Documents",
      upload: "Upload Document",
      search: "Search documents...",
      filter: "Filter",
      noDocuments: "No documents found",
      uploadFirst: "Upload your first document to get started",
      processing: "Processing...",
      ocr: "Run OCR",
      delete: "Delete",
      view: "View",
      type: "Type",
      date: "Date",
      size: "Size"
    },
    // Cases
    cases: {
      title: "Cases",
      create: "New Case",
      search: "Search cases...",
      noCases: "No cases found",
      createFirst: "Create your first case",
      status: "Status",
      open: "Open",
      inProgress: "In Progress",
      waiting: "Waiting",
      closed: "Closed",
      documents: "Documents",
      emails: "Emails",
      tasks: "Tasks"
    },
    // Tasks
    tasks: {
      title: "Tasks",
      create: "New Task",
      noTasks: "No tasks found",
      priority: "Priority",
      low: "Low",
      medium: "Medium",
      high: "High",
      urgent: "Urgent",
      dueDate: "Due Date",
      status: "Status",
      todo: "To Do",
      inProgress: "In Progress",
      done: "Done"
    },
    // Calendar
    calendar: {
      title: "Calendar",
      today: "Today",
      month: "Month",
      week: "Week",
      day: "Day",
      newEvent: "New Event",
      noEvents: "No events"
    },
    // AI Chat
    ai: {
      title: "AI Assistant",
      placeholder: "Ask me about your documents, cases, or tasks...",
      send: "Send",
      thinking: "Thinking...",
      disabled: "AI is currently disabled",
      enableHint: "Enable AI in Settings to use this feature"
    },
    // Settings
    settings: {
      title: "Settings",
      system: "System",
      user: "User Preferences",
      ai: "AI Configuration",
      privacy: "Privacy",
      email: "Email Accounts",
      save: "Save Changes",
      saved: "Settings saved",
      theme: "Theme",
      dark: "Dark",
      light: "Light",
      language: "Language",
      notifications: "Notifications"
    },
    // Common
    common: {
      save: "Save",
      cancel: "Cancel",
      delete: "Delete",
      edit: "Edit",
      create: "Create",
      close: "Close",
      confirm: "Confirm",
      loading: "Loading...",
      error: "Error",
      success: "Success",
      warning: "Warning",
      noResults: "No results found",
      search: "Search",
      actions: "Actions"
    }
  },
  de: {
    // Setup Wizard
    setup: {
      title: "Willkommen bei CaseDesk AI",
      subtitle: "Richten Sie Ihr privates Dokumentenmanagementsystem ein",
      selectLanguage: "Sprache wählen",
      continue: "Weiter",
      back: "Zurück",
      finish: "Einrichtung abschließen",
      step: "Schritt",
      of: "von",
      // Step 1
      languageTitle: "Sprachauswahl",
      languageDesc: "Wählen Sie Ihre bevorzugte Sprache für die Oberfläche",
      // Step 2
      adminTitle: "Administrator erstellen",
      adminDesc: "Richten Sie Ihr Admin-Konto ein",
      email: "E-Mail-Adresse",
      username: "Benutzername",
      password: "Passwort",
      confirmPassword: "Passwort bestätigen",
      fullName: "Vollständiger Name (optional)",
      // Step 3
      aiTitle: "KI-Konfiguration",
      aiDesc: "Konfigurieren Sie KI-Funktionen (kann später geändert werden)",
      aiProvider: "KI-Anbieter",
      aiDisabled: "Deaktiviert (nur lokal)",
      aiOpenai: "OpenAI (ChatGPT)",
      aiLocal: "Lokale KI",
      apiKey: "OpenAI API-Schlüssel",
      apiKeyPlaceholder: "sk-...",
      // Step 4
      privacyTitle: "Datenschutz-Einstellungen",
      privacyDesc: "Kontrollieren Sie, wie Ihre Daten verarbeitet werden",
      internetAccess: "Internetzugriff",
      internetAllowed: "Externe Verbindungen erlauben",
      internetDenied: "Alle externen Verbindungen blockieren",
      privacyNote: "Bei Deaktivierung funktionieren alle Funktionen offline. Keine Daten verlassen Ihren Server.",
      // Step 5
      completeTitle: "Einrichtung abgeschlossen",
      completeDesc: "Ihre CaseDesk AI-Instanz ist einsatzbereit",
      startUsing: "CaseDesk AI starten"
    },
    // Auth
    auth: {
      login: "Anmelden",
      logout: "Abmelden",
      email: "E-Mail",
      password: "Passwort",
      loginButton: "Anmelden",
      loginError: "Ungültige Anmeldedaten"
    },
    // Navigation
    nav: {
      dashboard: "Übersicht",
      documents: "Dokumente",
      cases: "Fälle",
      emails: "E-Mails",
      calendar: "Kalender",
      tasks: "Aufgaben",
      drafts: "Entwürfe",
      aiChat: "KI-Assistent",
      settings: "Einstellungen",
      users: "Benutzer"
    },
    // Dashboard
    dashboard: {
      welcome: "Willkommen zurück",
      overview: "Übersicht",
      openCases: "Offene Fälle",
      totalDocuments: "Dokumente",
      pendingTasks: "Offene Aufgaben",
      upcomingEvents: "Anstehende Termine",
      recentDocuments: "Neueste Dokumente",
      urgentTasks: "Dringende Aufgaben",
      noData: "Noch keine Daten"
    },
    // Documents
    documents: {
      title: "Dokumente",
      upload: "Dokument hochladen",
      search: "Dokumente durchsuchen...",
      filter: "Filter",
      noDocuments: "Keine Dokumente gefunden",
      uploadFirst: "Laden Sie Ihr erstes Dokument hoch",
      processing: "Wird verarbeitet...",
      ocr: "OCR ausführen",
      delete: "Löschen",
      view: "Anzeigen",
      type: "Typ",
      date: "Datum",
      size: "Größe"
    },
    // Cases
    cases: {
      title: "Fälle",
      create: "Neuer Fall",
      search: "Fälle durchsuchen...",
      noCases: "Keine Fälle gefunden",
      createFirst: "Erstellen Sie Ihren ersten Fall",
      status: "Status",
      open: "Offen",
      inProgress: "In Bearbeitung",
      waiting: "Wartend",
      closed: "Geschlossen",
      documents: "Dokumente",
      emails: "E-Mails",
      tasks: "Aufgaben"
    },
    // Tasks
    tasks: {
      title: "Aufgaben",
      create: "Neue Aufgabe",
      noTasks: "Keine Aufgaben gefunden",
      priority: "Priorität",
      low: "Niedrig",
      medium: "Mittel",
      high: "Hoch",
      urgent: "Dringend",
      dueDate: "Fälligkeitsdatum",
      status: "Status",
      todo: "Zu erledigen",
      inProgress: "In Bearbeitung",
      done: "Erledigt"
    },
    // Calendar
    calendar: {
      title: "Kalender",
      today: "Heute",
      month: "Monat",
      week: "Woche",
      day: "Tag",
      newEvent: "Neuer Termin",
      noEvents: "Keine Termine"
    },
    // AI Chat
    ai: {
      title: "KI-Assistent",
      placeholder: "Fragen Sie mich zu Ihren Dokumenten, Fällen oder Aufgaben...",
      send: "Senden",
      thinking: "Denkt nach...",
      disabled: "KI ist derzeit deaktiviert",
      enableHint: "Aktivieren Sie KI in den Einstellungen"
    },
    // Settings
    settings: {
      title: "Einstellungen",
      system: "System",
      user: "Benutzereinstellungen",
      ai: "KI-Konfiguration",
      privacy: "Datenschutz",
      email: "E-Mail-Konten",
      save: "Speichern",
      saved: "Einstellungen gespeichert",
      theme: "Design",
      dark: "Dunkel",
      light: "Hell",
      language: "Sprache",
      notifications: "Benachrichtigungen"
    },
    // Common
    common: {
      save: "Speichern",
      cancel: "Abbrechen",
      delete: "Löschen",
      edit: "Bearbeiten",
      create: "Erstellen",
      close: "Schließen",
      confirm: "Bestätigen",
      loading: "Wird geladen...",
      error: "Fehler",
      success: "Erfolgreich",
      warning: "Warnung",
      noResults: "Keine Ergebnisse",
      search: "Suchen",
      actions: "Aktionen"
    }
  }
};

export default translations;
