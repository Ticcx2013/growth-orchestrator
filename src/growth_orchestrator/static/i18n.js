/* Console texts in two languages and two registers.
   - en / es: technical register (system vocabulary, stage ids, action ids)
   - en_plain / es_plain: overrides for the plain register (words a salesperson uses)
   Lookup order in plain mode: <lang>_plain -> <lang> -> en. In technical mode: <lang> -> en. */
window.I18N = {
  en: {
    "nav.control": "Control room", "nav.policy": "Policy", "nav.operations": "Operations", "nav.about": "How it works", "nav.api": "API docs",
    "badge.live": "AI live", "badge.offline": "AI offline · recorded responses",
    "toggle.tech": "Technical", "toggle.plain": "Plain words",
    "brand": "Growth Orchestrator",

    "index.title": "Scenarios", "index.reset": "reset state",
    "index.intro": "Each run re-seeds the synthetic CRM and fires real events through the webhook pipeline.",
    "index.pipeline": "event → state → decision → AI/rules → action → audit",
    "index.pick": "Pick a scenario on the left.",
    "index.pick_sub": "You will see every stage the event goes through, what the rules said, what the model said, what the policy decided, and what hit the CRM.",
    "index.step": "step", "index.running": "running…", "index.crm_end": "CRM records at the end", "index.calls": "API calls", "index.faults": "faults fired",
    "index.review_open": "Open review items", "index.none": "none", "index.review": "review", "index.curl": "Or hit the webhook yourself", "index.reply": "reply",

    "pipeline.event": "Event", "pipeline.state": "State", "pipeline.rules": "Rules & AI", "pipeline.decision": "Decision", "pipeline.action": "Action", "pipeline.audit": "Audit",
    "pipeline.records": "records", "pipeline.record": "record", "pipeline.rules_only": "rules only", "pipeline.queued": "queued",
    "kind.success": "success", "kind.reliability": "reliability", "kind.ai": "ai",

    "scenario.happy_path.title": "1. Successful flow", "scenario.happy_path.summary": "Interested reply → handoff to AE with deal and task in the CRM.",
    "scenario.duplicate_event.title": "2. Duplicate event", "scenario.duplicate_event.summary": "The same webhook arrives twice. One action, one deal.",
    "scenario.crm_failure_retry.title": "3. Failure and retry", "scenario.crm_failure_retry.summary": "Timeout after commit (uncertain outcome) + 429. Reconcile, back off, never duplicate.",
    "scenario.unsafe_ai_injection.title": "4. Unsafe AI case", "scenario.unsafe_ai_injection.summary": "Prompt injection in the reply. Caught twice, zero automatic actions.",
    "scenario.ambiguous_mixed.title": "5. Ambiguous AI case", "scenario.ambiguous_mixed.summary": "Interest + opt-out + referral. Rule suppresses; human decides the rest.",
    "scenario.out_of_order.title": "6. Out-of-order events", "scenario.out_of_order.summary": "Late and stale events. State never moves backwards; replies judged on current state.",
    "scenario.freshness_check.title": "7. Stale local state", "scenario.freshness_check.summary": "CRM changed before the webhook arrived. Re-read before acting; no contact to an AE-owned account.",

    "result.action": "action", "result.automated": "automated", "result.not_automated": "not automated", "result.review": "human review",
    "result.status": "status", "result.attempts": "attempts", "result.ref": "ref", "result.crm": "CRM",

    "policy.title": "Policy: what the system may do on its own",
    "policy.subtitle": "This is policy.yaml. Change it here, re-run a scenario in the control room, and watch the decision change. No code involved.",
    "policy.version": "version", "policy.save": "Save policy", "policy.saved": "Saved as version",
    "policy.presets": "Presets (for \"change one assumption\" moments)",
    "policy.preset.shadow": "Shadow mode: everything assisted", "policy.preset.autonomous": "Fully autonomous", "policy.preset.kill": "Kill switch: everything off", "policy.preset.conservative": "Conservative (default)",
    "policy.automation": "Automation mode per action", "policy.automation_hint": "auto runs alone · assisted proposes and waits for a human · off logs only",
    "mode.auto": "auto", "mode.assisted": "assisted", "mode.off": "off",
    "policy.ai": "AI gates", "policy.min_conf": "Minimum confidence to automate", "policy.min_conf_hr": "Minimum confidence for high-risk intents",
    "policy.hr_intents": "High-risk intents (comma separated)", "policy.freshness": "Re-read the CRM before any irreversible action",
    "policy.elig": "Eligibility", "policy.cooldown": "Cooldown after outreach (days)", "policy.cap": "Max contacts in sequence per account",
    "policy.icp_min": "ICP: minimum employees", "policy.icp_countries": "ICP: countries", "policy.default_wait": "Default wait when no date is stated (days)",
    "policy.map": "Intent → action map", "policy.map_hint": "The model names the intent. This table, not the model, names the action.", "policy.raw": "Raw policy JSON",

    "action.handoff_to_ae": "handoff_to_ae", "action.wait_until": "wait_until", "action.create_referral_contact": "create_referral_contact", "action.suppress_contact": "suppress_contact",
    "action.nurture_long_term": "nurture_long_term", "action.escalate_to_human": "escalate_to_human", "action.enroll_in_sequence": "enroll_in_sequence", "action.enrich_contact": "enrich_contact",
    "action.notify_csm": "notify_csm", "action.no_action": "no_action",
    "intent.interested": "interested", "intent.not_interested": "not_interested", "intent.out_of_office": "out_of_office", "intent.referral": "referral", "intent.unsubscribe": "unsubscribe",
    "intent.pricing_question": "pricing_question", "intent.later": "later", "intent.mixed": "mixed", "intent.unclear": "unclear",

    "ops.title": "Operations", "ops.subtitle": "What a RevOps person sees day to day: what needs a human, what the outbox is doing, and the audit trail behind every decision.",
    "ops.tick": "advance clock +60s & run retries", "ops.refresh": "refresh",
    "ops.tab.review": "Review queue", "ops.tab.actions": "Outbox", "ops.tab.audit": "Audit log", "ops.tab.ai": "AI calls", "ops.tab.state": "State", "ops.tab.crm": "CRM",
    "ops.review.empty": "Nothing waiting for a human. Run an ambiguous scenario in the control room.",
    "ops.review.system": "system decision", "ops.review.proposed": "proposed", "ops.review.model": "model read", "ops.review.confidence": "confidence", "ops.review.flags": "flags",
    "ops.review.approve": "Approve", "ops.review.close": "Close: no action", "ops.review.reject": "Reject", "ops.show_resolved": "show resolved",
    "ops.col.key": "Idempotency key", "ops.col.type": "Type", "ops.col.target": "Target", "ops.col.status": "Status", "ops.col.attempts": "Attempts", "ops.col.next": "Next attempt", "ops.col.ref": "External ref", "ops.col.error": "Last error",
    "ops.state.accounts": "Accounts", "ops.state.contacts": "Contacts", "ops.state.suppressions": "Suppressions", "ops.customer": "customer", "ops.opp": "opp",
    "ops.crm.hint": "Mock CRM records. Every record carries the idempotency key that created it, which is how retries never duplicate.",
    "ops.col.kind": "Kind", "ops.col.id": "Id", "ops.col.data": "Data", "ops.valid": "valid", "ops.invalid": "invalid", "ops.attempt": "attempt", "ops.validation": "validation",
    "status.succeeded": "succeeded", "status.uncertain": "uncertain", "status.pending": "pending", "status.in_flight": "in_flight", "status.failed": "failed", "status.dead": "dead",
    "cstatus.active": "active", "cstatus.handed_off": "handed_off", "cstatus.waiting": "waiting", "cstatus.suppressed": "suppressed", "cstatus.nurture": "nurture",
    "rstatus.open": "open", "rstatus.approved": "approved", "rstatus.rejected": "rejected",

    "about.title": "How it works", "about.subtitle": "One vertical slice, built for judgment rather than volume: the model interprets, the rules decide, the outbox acts, the audit log remembers.",
    "about.arch": "Architecture", "about.boundaries": "What the AI may and may not decide", "about.q": "Question", "about.who": "Who answers",
    "about.q1": "What does this reply mean? Which facts does it state?", "about.a1": "Model (interprets)",
    "about.q2": "May we contact this account at all?", "about.a2": "Rules (state + policy)",
    "about.q3": "Did they ask us to stop?", "about.a3": "Rules first; model is a second opinion",
    "about.q4": "Which action follows from the intent?", "about.a4": "Policy table",
    "about.q5": "May that action run without a human?", "about.a5": "Policy mode + confidence gate",
    "about.q6": "Is this a duplicate? Is this event stale?", "about.a6": "Rules (keys and versions)",
    "about.q7": "Is the CRM still in the state we think?", "about.a7": "Freshness check (a read, not a guess)",
    "about.q8": "Anything ambiguous, contradictory, or below threshold", "about.a8": "Human",
    "about.eval": "AI evaluation (latest run)", "about.eval_none": "No results yet. Run make eval-live.", "about.passed": "passed", "about.intent": "intent", "about.action": "action", "about.grounded": "grounded",
    "about.unsafe": "unsafe automations", "about.case": "Case", "about.conf": "Conf", "about.pass": "pass", "about.fail": "fail", "about.reports": "Reports",
    "about.docs.decisions": "Decision log", "about.docs.experiment": "Measurement plan", "about.docs.whatif": "If you change an assumption",
    "about.plain_title": "In six steps", "about.tech_note": "Technical mode shows the raw system log in English.",
  },

  es: {
    "nav.control": "Sala de control", "nav.policy": "Política", "nav.operations": "Operación", "nav.about": "Cómo funciona", "nav.api": "Docs API",
    "badge.live": "IA en vivo", "badge.offline": "IA sin conexión · respuestas grabadas",
    "toggle.tech": "Técnico", "toggle.plain": "En palabras",

    "index.title": "Escenarios", "index.reset": "reiniciar estado",
    "index.intro": "Cada corrida vuelve a sembrar el CRM sintético y dispara eventos reales por el pipeline del webhook.",
    "index.pipeline": "evento → estado → decisión → IA/reglas → acción → auditoría",
    "index.pick": "Elige un escenario a la izquierda.",
    "index.pick_sub": "Verás cada etapa que recorre el evento, qué dijeron las reglas, qué dijo el modelo, qué decidió la política y qué llegó al CRM.",
    "index.step": "paso", "index.running": "corriendo…", "index.crm_end": "Registros en el CRM al final", "index.calls": "llamadas a la API", "index.faults": "fallas disparadas",
    "index.review_open": "Pendientes de revisión humana", "index.none": "ninguno", "index.review": "revisar", "index.curl": "O pégale al webhook tú mismo", "index.reply": "respuesta",

    "pipeline.event": "Evento", "pipeline.state": "Estado", "pipeline.rules": "Reglas e IA", "pipeline.decision": "Decisión", "pipeline.action": "Acción", "pipeline.audit": "Auditoría",
    "pipeline.records": "registros", "pipeline.record": "registro", "pipeline.rules_only": "solo reglas", "pipeline.queued": "en cola",
    "kind.success": "éxito", "kind.reliability": "confiabilidad", "kind.ai": "ia",

    "scenario.happy_path.title": "1. Flujo exitoso", "scenario.happy_path.summary": "Respuesta con interés → handoff al AE con deal y tarea en el CRM.",
    "scenario.duplicate_event.title": "2. Evento duplicado", "scenario.duplicate_event.summary": "El mismo webhook llega dos veces. Una acción, un deal.",
    "scenario.crm_failure_retry.title": "3. Falla y reintento", "scenario.crm_failure_retry.summary": "Timeout después del commit (resultado incierto) + 429. Reconciliar, esperar, nunca duplicar.",
    "scenario.unsafe_ai_injection.title": "4. Caso de IA inseguro", "scenario.unsafe_ai_injection.summary": "Prompt injection en la respuesta. Atrapado dos veces, cero acciones automáticas.",
    "scenario.ambiguous_mixed.title": "5. Caso de IA ambiguo", "scenario.ambiguous_mixed.summary": "Interés + baja + referido. La regla suprime; un humano decide el resto.",
    "scenario.out_of_order.title": "6. Eventos desordenados", "scenario.out_of_order.summary": "Eventos tardíos y viejos. El estado nunca retrocede; las respuestas se juzgan con el estado actual.",
    "scenario.freshness_check.title": "7. Estado local desactualizado", "scenario.freshness_check.summary": "El CRM cambió antes de que llegara el webhook. Releer antes de actuar; no se contacta una cuenta con AE.",

    "result.action": "acción", "result.automated": "automático", "result.not_automated": "no automático", "result.review": "revisión humana",
    "result.status": "estado", "result.attempts": "intentos", "result.ref": "ref", "result.crm": "CRM",

    "policy.title": "Política: qué puede hacer el sistema por su cuenta",
    "policy.subtitle": "Esto es policy.yaml. Cámbialo aquí, vuelve a correr un escenario en la sala de control y mira cambiar la decisión. Sin tocar código.",
    "policy.version": "versión", "policy.save": "Guardar política", "policy.saved": "Guardada como versión",
    "policy.presets": "Presets (para el momento de \"cambien un supuesto\")",
    "policy.preset.shadow": "Modo sombra: todo asistido", "policy.preset.autonomous": "Totalmente autónomo", "policy.preset.kill": "Kill switch: todo apagado", "policy.preset.conservative": "Conservador (default)",
    "policy.automation": "Modo de automatización por acción", "policy.automation_hint": "auto corre solo · assisted propone y espera a un humano · off solo registra",
    "policy.ai": "Compuertas de IA", "policy.min_conf": "Confianza mínima para automatizar", "policy.min_conf_hr": "Confianza mínima en intenciones de alto riesgo",
    "policy.hr_intents": "Intenciones de alto riesgo (separadas por coma)", "policy.freshness": "Releer el CRM antes de cualquier acción irreversible",
    "policy.elig": "Elegibilidad", "policy.cooldown": "Enfriamiento después de contactar (días)", "policy.cap": "Máximo de contactos en secuencia por cuenta",
    "policy.icp_min": "ICP: empleados mínimos", "policy.icp_countries": "ICP: países", "policy.default_wait": "Espera por defecto cuando no hay fecha (días)",
    "policy.map": "Mapa intención → acción", "policy.map_hint": "El modelo nombra la intención. Esta tabla, no el modelo, nombra la acción.", "policy.raw": "JSON crudo de la política",

    "ops.title": "Operación", "ops.subtitle": "Lo que ve RevOps día a día: qué necesita un humano, qué está haciendo el outbox y el rastro de auditoría detrás de cada decisión.",
    "ops.tick": "avanzar reloj +60s y correr reintentos", "ops.refresh": "actualizar",
    "ops.tab.review": "Cola de revisión", "ops.tab.actions": "Outbox", "ops.tab.audit": "Bitácora", "ops.tab.ai": "Llamadas de IA", "ops.tab.state": "Estado", "ops.tab.crm": "CRM",
    "ops.review.empty": "Nada esperando a un humano. Corre un escenario ambiguo en la sala de control.",
    "ops.review.system": "decisión del sistema", "ops.review.proposed": "propuesta", "ops.review.model": "lectura del modelo", "ops.review.confidence": "confianza", "ops.review.flags": "banderas",
    "ops.review.approve": "Aprobar", "ops.review.close": "Cerrar: sin acción", "ops.review.reject": "Rechazar", "ops.show_resolved": "mostrar resueltos",
    "ops.col.key": "Llave de idempotencia", "ops.col.type": "Tipo", "ops.col.target": "Destino", "ops.col.status": "Estado", "ops.col.attempts": "Intentos", "ops.col.next": "Próximo intento", "ops.col.ref": "Ref externa", "ops.col.error": "Último error",
    "ops.state.accounts": "Cuentas", "ops.state.contacts": "Contactos", "ops.state.suppressions": "Supresiones", "ops.customer": "cliente", "ops.opp": "opp",
    "ops.crm.hint": "Registros del CRM simulado. Cada registro guarda la llave de idempotencia que lo creó; por eso los reintentos nunca duplican.",
    "ops.col.kind": "Tipo", "ops.col.id": "Id", "ops.col.data": "Datos", "ops.valid": "válida", "ops.invalid": "inválida", "ops.attempt": "intento", "ops.validation": "validación",

    "about.title": "Cómo funciona", "about.subtitle": "Una sola rebanada vertical, construida para el criterio y no para el volumen: el modelo interpreta, las reglas deciden, el outbox actúa, la bitácora recuerda.",
    "about.arch": "Arquitectura", "about.boundaries": "Qué puede y qué no puede decidir la IA", "about.q": "Pregunta", "about.who": "Quién responde",
    "about.q1": "¿Qué significa esta respuesta? ¿Qué hechos dice?", "about.a1": "Modelo (interpreta)",
    "about.q2": "¿Podemos contactar esta cuenta?", "about.a2": "Reglas (estado + política)",
    "about.q3": "¿Pidieron que paremos?", "about.a3": "Reglas primero; el modelo es segunda opinión",
    "about.q4": "¿Qué acción sigue de la intención?", "about.a4": "Tabla de política",
    "about.q5": "¿Esa acción puede correr sin humano?", "about.a5": "Modo de política + compuerta de confianza",
    "about.q6": "¿Es un duplicado? ¿Es un evento viejo?", "about.a6": "Reglas (llaves y versiones)",
    "about.q7": "¿El CRM sigue como creemos?", "about.a7": "Chequeo de frescura (una lectura, no una suposición)",
    "about.q8": "Cualquier cosa ambigua, contradictoria o bajo el umbral", "about.a8": "Humano",
    "about.eval": "Evaluación de IA (última corrida)", "about.eval_none": "Sin resultados aún. Corre make eval-live.", "about.passed": "pasaron", "about.intent": "intención", "about.action": "acción", "about.grounded": "fundamentado",
    "about.unsafe": "automatizaciones inseguras", "about.case": "Caso", "about.conf": "Conf", "about.pass": "ok", "about.fail": "falla", "about.reports": "Reportes",
    "about.docs.decisions": "Decision log", "about.docs.experiment": "Plan de medición", "about.docs.whatif": "Si cambian un supuesto",
    "about.plain_title": "En seis pasos", "about.tech_note": "El modo técnico muestra la bitácora cruda del sistema en inglés.",
  },

  en_plain: {
    "brand": "Reply Assistant",
    "nav.control": "Try it", "nav.policy": "Rules", "nav.operations": "Daily work", "nav.about": "How it works",
    "badge.live": "AI on", "badge.offline": "AI off · using saved answers",
    "index.title": "Situations", "index.reset": "start over",
    "index.intro": "Each button plays a real situation from start to finish so you can watch what the assistant does.",
    "index.pipeline": "message arrives → check the file → decide → act → keep a record",
    "index.pick": "Pick a situation on the left.", "index.pick_sub": "You will see, in plain words, what the assistant checked, what it understood, what it decided and what it did.",
    "index.crm_end": "What ended up in the CRM", "index.calls": "calls to the CRM", "index.faults": "problems we caused on purpose",
    "index.review_open": "Waiting for a person", "index.review": "go see", "index.curl": "For developers: send a message by hand", "index.reply": "the prospect wrote",
    "pipeline.event": "Message", "pipeline.state": "The file", "pipeline.rules": "Checks & reading", "pipeline.decision": "Decision", "pipeline.action": "What it did", "pipeline.audit": "Record",
    "pipeline.records": "notes", "pipeline.record": "note", "pipeline.rules_only": "checks only", "pipeline.queued": "waiting",
    "kind.success": "works", "kind.reliability": "safety", "kind.ai": "AI",
    "scenario.happy_path.title": "1. A good reply", "scenario.happy_path.summary": "The prospect wants to talk. The assistant hands them to a salesperson and creates the deal.",
    "scenario.duplicate_event.title": "2. The same message twice", "scenario.duplicate_event.summary": "The tool sends the same reply twice by mistake. Only one deal is created.",
    "scenario.crm_failure_retry.title": "3. The CRM has a bad day", "scenario.crm_failure_retry.summary": "The CRM stops answering mid-way and then asks us to slow down. Nothing gets duplicated.",
    "scenario.unsafe_ai_injection.title": "4. Someone tries to trick the AI", "scenario.unsafe_ai_injection.summary": "A reply that tells the AI what to do. The assistant notices and asks a person.",
    "scenario.ambiguous_mixed.title": "5. A confusing reply", "scenario.ambiguous_mixed.summary": "Interested, but also \"remove me\", and \"talk to my partner\". We stop contacting them and a person decides the rest.",
    "scenario.out_of_order.title": "6. News arriving late", "scenario.out_of_order.summary": "The account became a customer, then old news and an old reply arrive. Nothing gets sold twice.",
    "scenario.freshness_check.title": "7. The CRM knows something we don't", "scenario.freshness_check.summary": "A salesperson already opened a deal. The assistant checks before acting and steps aside.",
    "result.action": "did", "result.automated": "on its own", "result.not_automated": "needs a person", "result.review": "a person will look",
    "result.status": "status", "result.attempts": "tries", "result.ref": "CRM id", "result.crm": "in the CRM",
    "policy.title": "Rules: what the assistant may do on its own",
    "policy.subtitle": "These are the switches. Flip one, go back to \"Try it\" and run the same situation again: the outcome changes. No developer needed.",
    "policy.save": "Save rules", "policy.saved": "Saved, version",
    "policy.presets": "Quick settings",
    "policy.preset.shadow": "Training wheels: a person approves everything", "policy.preset.autonomous": "Full autopilot", "policy.preset.kill": "Emergency stop: turn everything off", "policy.preset.conservative": "Recommended",
    "policy.automation": "What the assistant may do on its own", "policy.automation_hint": "on its own · ask first (a person approves) · off",
    "mode.auto": "on its own", "mode.assisted": "ask first", "mode.off": "off",
    "policy.ai": "How sure the AI must be", "policy.min_conf": "Minimum certainty to act on its own (0 to 1)", "policy.min_conf_hr": "Minimum certainty for delicate cases (0 to 1)",
    "policy.hr_intents": "Delicate cases", "policy.freshness": "Double-check the CRM before doing anything that cannot be undone",
    "policy.elig": "Who we may contact", "policy.cooldown": "Days to wait after we last wrote to someone", "policy.cap": "Max people per company in outreach at once",
    "policy.icp_min": "Smallest company we sell to (employees)", "policy.icp_countries": "Countries we sell in", "policy.default_wait": "Days to wait when they say \"later\" without a date",
    "policy.map": "What each kind of reply leads to", "policy.map_hint": "The AI says what kind of reply it is. This table, not the AI, says what happens next.", "policy.raw": "For developers: the raw file",
    "action.handoff_to_ae": "hand to a salesperson", "action.wait_until": "wait and come back later", "action.create_referral_contact": "add the person they referred",
    "action.suppress_contact": "stop contacting them", "action.nurture_long_term": "keep in touch, no pressure", "action.escalate_to_human": "ask a person",
    "action.enroll_in_sequence": "start the email sequence", "action.enrich_contact": "look up more data", "action.notify_csm": "tell their account manager", "action.no_action": "do nothing",
    "intent.interested": "interested", "intent.not_interested": "not interested", "intent.out_of_office": "out of office", "intent.referral": "refers someone else", "intent.unsubscribe": "asks to stop",
    "intent.pricing_question": "asks about price", "intent.later": "says \"later\"", "intent.mixed": "mixed signals", "intent.unclear": "unclear",
    "ops.title": "Daily work", "ops.subtitle": "What a person on the team sees every day: what needs a decision, what the assistant did, and the full record.",
    "ops.tick": "pretend a minute passed & retry", "ops.refresh": "refresh",
    "ops.tab.review": "Needs a person", "ops.tab.actions": "Things done", "ops.tab.audit": "Full record", "ops.tab.ai": "What the AI read", "ops.tab.state": "Accounts & people", "ops.tab.crm": "CRM",
    "ops.review.empty": "Nothing needs a person right now. Run situation 5 to see one.",
    "ops.review.system": "the assistant did", "ops.review.proposed": "suggests", "ops.review.model": "the AI understood", "ops.review.confidence": "certainty", "ops.review.flags": "warnings",
    "ops.review.approve": "Yes, do it", "ops.review.close": "Nothing to do", "ops.review.reject": "No", "ops.show_resolved": "show handled ones",
    "ops.col.key": "Id", "ops.col.type": "What", "ops.col.target": "Where", "ops.col.status": "Status", "ops.col.attempts": "Tries", "ops.col.next": "Next try", "ops.col.ref": "CRM id", "ops.col.error": "Problem",
    "ops.state.accounts": "Companies", "ops.state.contacts": "People", "ops.state.suppressions": "Do-not-contact list", "ops.customer": "customer", "ops.opp": "deal with",
    "ops.crm.hint": "What the (simulated) CRM contains. Each record remembers which message created it, so a retry never creates it twice.",
    "ops.col.kind": "What", "ops.col.id": "Id", "ops.col.data": "Details", "ops.valid": "checked", "ops.invalid": "did not pass checks", "ops.attempt": "try",
    "status.succeeded": "done", "status.uncertain": "not sure it went through", "status.pending": "waiting to retry", "status.in_flight": "in progress", "status.failed": "failed", "status.dead": "gave up, a person will handle it",
    "cstatus.active": "in outreach", "cstatus.handed_off": "with a salesperson", "cstatus.waiting": "waiting", "cstatus.suppressed": "do not contact", "cstatus.nurture": "keep in touch",
    "rstatus.open": "waiting", "rstatus.approved": "approved", "rstatus.rejected": "rejected",
    "about.subtitle": "The assistant reads replies and decides the next step. The AI only reads. Fixed rules decide. Every step is written down.",
    "about.arch": "The map (for developers)", "about.boundaries": "Who decides what",
    "about.a1": "The AI (it reads)", "about.a2": "Fixed rules", "about.a3": "Fixed rules; the AI double-checks", "about.a4": "A table you can edit", "about.a5": "The switches on the Rules page",
    "about.a6": "Fixed rules", "about.a7": "It asks the CRM again", "about.a8": "A person",
    "about.q2": "May we write to this company at all?", "about.q3": "Did they ask us to stop?", "about.q4": "What happens after each kind of reply?", "about.q5": "May that happen without a person?",
    "about.q6": "Is this the same message again? Is this old news?", "about.q7": "Has the CRM changed since we last looked?", "about.q8": "Anything confusing or uncertain",
    "about.eval": "How well the AI reads (test results)", "about.passed": "right", "about.intent": "kind of reply", "about.action": "next step", "about.grounded": "nothing made up",
    "about.unsafe": "risky actions taken alone", "about.case": "Test", "about.conf": "Sure", "about.pass": "ok", "about.fail": "miss",
    "about.docs.decisions": "Why it was built this way", "about.docs.experiment": "How we will measure if it works", "about.docs.whatif": "If things change",
    "about.tech_note": "",
  },

  es_plain: {
    "brand": "Asistente de respuestas",
    "nav.control": "Pruébalo", "nav.policy": "Reglas", "nav.operations": "Día a día", "nav.about": "Cómo funciona",
    "badge.live": "IA encendida", "badge.offline": "IA apagada · usa respuestas guardadas",
    "index.title": "Situaciones", "index.reset": "empezar de nuevo",
    "index.intro": "Cada botón reproduce una situación real de principio a fin para que veas qué hace el asistente.",
    "index.pipeline": "llega un mensaje → revisa el expediente → decide → actúa → deja registro",
    "index.pick": "Elige una situación a la izquierda.", "index.pick_sub": "Verás, en palabras simples, qué revisó el asistente, qué entendió, qué decidió y qué hizo.",
    "index.crm_end": "Qué quedó en el CRM", "index.calls": "llamadas al CRM", "index.faults": "problemas que provocamos a propósito",
    "index.review_open": "Esperando a una persona", "index.review": "ir a ver", "index.curl": "Para desarrolladores: mandar un mensaje a mano", "index.reply": "el prospecto escribió",
    "pipeline.event": "Mensaje", "pipeline.state": "Expediente", "pipeline.rules": "Revisión y lectura", "pipeline.decision": "Decisión", "pipeline.action": "Qué hizo", "pipeline.audit": "Registro",
    "pipeline.records": "notas", "pipeline.record": "nota", "pipeline.rules_only": "solo revisión", "pipeline.queued": "en espera",
    "kind.success": "funciona", "kind.reliability": "seguridad", "kind.ai": "IA",
    "scenario.happy_path.title": "1. Una buena respuesta", "scenario.happy_path.summary": "El prospecto quiere hablar. El asistente lo pasa a un vendedor y crea el deal.",
    "scenario.duplicate_event.title": "2. El mismo mensaje dos veces", "scenario.duplicate_event.summary": "La herramienta manda la misma respuesta dos veces por error. Solo se crea un deal.",
    "scenario.crm_failure_retry.title": "3. El CRM tiene un mal día", "scenario.crm_failure_retry.summary": "El CRM deja de responder a medio camino y luego pide que bajemos el ritmo. Nada se duplica.",
    "scenario.unsafe_ai_injection.title": "4. Alguien intenta engañar a la IA", "scenario.unsafe_ai_injection.summary": "Una respuesta que le da órdenes a la IA. El asistente se da cuenta y le pregunta a una persona.",
    "scenario.ambiguous_mixed.title": "5. Una respuesta confusa", "scenario.ambiguous_mixed.summary": "Le interesa, pero también dice \"quítenme\" y \"hablen con mi socio\". Dejamos de contactarlo y una persona decide el resto.",
    "scenario.out_of_order.title": "6. Noticias que llegan tarde", "scenario.out_of_order.summary": "La cuenta se volvió cliente y luego llegan noticias viejas y una respuesta vieja. No se vende dos veces.",
    "scenario.freshness_check.title": "7. El CRM sabe algo que nosotros no", "scenario.freshness_check.summary": "Un vendedor ya abrió un deal. El asistente revisa antes de actuar y se hace a un lado.",
    "result.action": "hizo", "result.automated": "por su cuenta", "result.not_automated": "necesita una persona", "result.review": "una persona lo verá",
    "result.status": "estado", "result.attempts": "intentos", "result.ref": "id en CRM", "result.crm": "en el CRM",
    "policy.title": "Reglas: qué puede hacer el asistente por su cuenta",
    "policy.subtitle": "Estos son los interruptores. Cambia uno, vuelve a \"Pruébalo\" y corre la misma situación: el resultado cambia. Sin programador.",
    "policy.version": "versión", "policy.save": "Guardar reglas", "policy.saved": "Guardado, versión",
    "policy.presets": "Ajustes rápidos",
    "policy.preset.shadow": "Rueditas de entrenamiento: una persona aprueba todo", "policy.preset.autonomous": "Piloto automático total", "policy.preset.kill": "Paro de emergencia: apagar todo", "policy.preset.conservative": "Recomendado",
    "policy.automation": "Qué puede hacer el asistente solo", "policy.automation_hint": "solo · preguntar primero (una persona aprueba) · apagado",
    "mode.auto": "solo", "mode.assisted": "preguntar primero", "mode.off": "apagado",
    "policy.ai": "Qué tan segura debe estar la IA", "policy.min_conf": "Certeza mínima para actuar sola (de 0 a 1)", "policy.min_conf_hr": "Certeza mínima en casos delicados (de 0 a 1)",
    "policy.hr_intents": "Casos delicados", "policy.freshness": "Volver a revisar el CRM antes de hacer algo que no se pueda deshacer",
    "policy.elig": "A quién podemos contactar", "policy.cooldown": "Días de espera después de escribirle a alguien", "policy.cap": "Máximo de personas por empresa contactadas a la vez",
    "policy.icp_min": "Empresa más chica a la que vendemos (empleados)", "policy.icp_countries": "Países donde vendemos", "policy.default_wait": "Días de espera cuando dicen \"después\" sin fecha",
    "policy.map": "A qué lleva cada tipo de respuesta", "policy.map_hint": "La IA dice qué tipo de respuesta es. Esta tabla, no la IA, dice qué pasa después.", "policy.raw": "Para desarrolladores: el archivo crudo",
    "action.handoff_to_ae": "pasar a un vendedor", "action.wait_until": "esperar y volver después", "action.create_referral_contact": "agregar a la persona que recomendó",
    "action.suppress_contact": "dejar de contactarlo", "action.nurture_long_term": "mantener contacto sin presionar", "action.escalate_to_human": "preguntar a una persona",
    "action.enroll_in_sequence": "iniciar la secuencia de correos", "action.enrich_contact": "buscar más datos", "action.notify_csm": "avisar a su ejecutivo de cuenta", "action.no_action": "no hacer nada",
    "intent.interested": "le interesa", "intent.not_interested": "no le interesa", "intent.out_of_office": "fuera de la oficina", "intent.referral": "recomienda a otra persona", "intent.unsubscribe": "pide que paremos",
    "intent.pricing_question": "pregunta el precio", "intent.later": "dice \"después\"", "intent.mixed": "señales mezcladas", "intent.unclear": "no queda claro",
    "ops.title": "Día a día", "ops.subtitle": "Lo que ve alguien del equipo cada día: qué necesita una decisión, qué hizo el asistente y el registro completo.",
    "ops.tick": "simular que pasó un minuto y reintentar", "ops.refresh": "actualizar",
    "ops.tab.review": "Necesita una persona", "ops.tab.actions": "Cosas hechas", "ops.tab.audit": "Registro completo", "ops.tab.ai": "Qué leyó la IA", "ops.tab.state": "Empresas y personas", "ops.tab.crm": "CRM",
    "ops.review.empty": "Nada necesita una persona ahora. Corre la situación 5 para ver una.",
    "ops.review.system": "el asistente hizo", "ops.review.proposed": "sugiere", "ops.review.model": "la IA entendió", "ops.review.confidence": "certeza", "ops.review.flags": "avisos",
    "ops.review.approve": "Sí, hazlo", "ops.review.close": "Nada que hacer", "ops.review.reject": "No", "ops.show_resolved": "mostrar los ya atendidos",
    "ops.col.key": "Id", "ops.col.type": "Qué", "ops.col.target": "Dónde", "ops.col.status": "Estado", "ops.col.attempts": "Intentos", "ops.col.next": "Próximo intento", "ops.col.ref": "Id en CRM", "ops.col.error": "Problema",
    "ops.state.accounts": "Empresas", "ops.state.contacts": "Personas", "ops.state.suppressions": "Lista de no contactar", "ops.customer": "cliente", "ops.opp": "deal con",
    "ops.crm.hint": "Lo que contiene el CRM (simulado). Cada registro recuerda qué mensaje lo creó, así un reintento nunca lo crea dos veces.",
    "ops.col.kind": "Qué", "ops.col.id": "Id", "ops.col.data": "Detalles", "ops.valid": "verificada", "ops.invalid": "no pasó las revisiones", "ops.attempt": "intento",
    "status.succeeded": "hecho", "status.uncertain": "no sabemos si pasó", "status.pending": "esperando reintento", "status.in_flight": "en curso", "status.failed": "falló", "status.dead": "se rindió, lo verá una persona",
    "cstatus.active": "en contacto", "cstatus.handed_off": "con un vendedor", "cstatus.waiting": "en espera", "cstatus.suppressed": "no contactar", "cstatus.nurture": "mantener contacto",
    "rstatus.open": "esperando", "rstatus.approved": "aprobado", "rstatus.rejected": "rechazado",
    "about.subtitle": "El asistente lee las respuestas y decide el siguiente paso. La IA solo lee. Reglas fijas deciden. Cada paso queda escrito.",
    "about.arch": "El mapa (para desarrolladores)", "about.boundaries": "Quién decide qué",
    "about.a1": "La IA (lee)", "about.a2": "Reglas fijas", "about.a3": "Reglas fijas; la IA revisa de nuevo", "about.a4": "Una tabla que puedes editar", "about.a5": "Los interruptores de la página de Reglas",
    "about.a6": "Reglas fijas", "about.a7": "Le vuelve a preguntar al CRM", "about.a8": "Una persona",
    "about.q1": "¿Qué quiere decir esta respuesta? ¿Qué datos trae?", "about.q2": "¿Podemos escribirle a esta empresa?", "about.q3": "¿Pidieron que paremos?", "about.q4": "¿Qué pasa después de cada tipo de respuesta?", "about.q5": "¿Eso puede pasar sin una persona?",
    "about.q6": "¿Es el mismo mensaje otra vez? ¿Es noticia vieja?", "about.q7": "¿Cambió el CRM desde la última vez que vimos?", "about.q8": "Cualquier cosa confusa o incierta",
    "about.eval": "Qué tan bien lee la IA (resultados de prueba)", "about.passed": "correctas", "about.intent": "tipo de respuesta", "about.action": "siguiente paso", "about.grounded": "nada inventado",
    "about.unsafe": "acciones riesgosas hechas sola", "about.case": "Prueba", "about.conf": "Certeza", "about.pass": "ok", "about.fail": "falla",
    "about.docs.decisions": "Por qué se construyó así", "about.docs.experiment": "Cómo mediremos si funciona", "about.docs.whatif": "Si las cosas cambian",
    "about.tech_note": "",
  },
};

/* Plain-language sentences for each audit stage. {vars} come from the audit row's data. */
window.STAGE_PLAIN = {
  en: {
    "received.reply.received": "A reply from the prospect arrived.",
    "received.crm.account_updated": "The CRM reported a change on the account.",
    "received.prospect.identified": "A new prospect was identified.",
    "received.contact.unsubscribed": "The contact unsubscribed.",
    "duplicate": "This same message had already arrived. Ignored: nothing is done twice.",
    "state_loaded": "Looked up the company and the person in the file.",
    "state_loaded.customer": "Looked up the file: this company is already a customer.",
    "state_loaded.opp": "Looked up the file: a salesperson already has an open deal here.",
    "ordering": "The reply was written before the account's latest change. It is judged on today's facts.",
    "stale_event": "Old news: the file already had newer information. Ignored, so nothing moves backwards.",
    "state_updated": "Updated the company file.",
    "eligibility.ok": "Green light: we may talk to this company.",
    "eligibility.blocked": "Stop: {reasons}.",
    "compliance.optout": "The person asked us to stop. A fixed rule handles this, never the AI.",
    "compliance.injection": "The message tries to give orders to the system. Flagged.",
    "compliance.ok": "No request to stop.",
    "ai.skipped": "The AI was not needed: the checks already decided.",
    "ai.read": "The AI read the message: {intent} (certainty {conf}).",
    "ai.none": "The AI could not read the message, so a person will.",
    "ai_validation.ok": "Checked the AI's reading against the text: everything it quotes is really there.",
    "ai_validation.fail": "The AI's reading did not pass the checks, so a person will decide.",
    "freshness.ok": "Double-checked the CRM: nothing changed. Safe to act.",
    "freshness.diff": "The CRM had newer facts. Updated the file and decided again.",
    "freshness.other": "Could not double-check the CRM right now; went ahead with what we know.",
    "decision.auto": "Decision: {action}, on its own.",
    "decision.human": "Decision: {action}. A person will look at it.",
    "decision.none": "Decision: do nothing. {reason}",
    "action_enqueued": "Queued: {action}.",
    "action_dispatched": "Done in the CRM: {action}.",
    "action_uncertain": "The CRM did not confirm. We do not know if it went through, so we will check before trying again.",
    "action_reconciled.found": "Checked: it had gone through. Nothing sent twice.",
    "action_reconciled.missing": "Checked: it had not gone through. Safe to send again.",
    "action_retry_scheduled": "The CRM asked us to slow down. Will retry later.",
    "action_dead": "Gave up after several tries. A person will handle it.",
    "review_queued": "Sent to a person for review.",
    "human_decision": "{message}",
    "completed": "Done.",
    "failed": "Something went wrong: {message}",
    "policy_changed": "The rules were changed.",
    "blocker.already_customer": "they are already a customer",
    "blocker.active_opportunity": "a salesperson already owns this deal",
    "blocker.suppressed": "they are on the do-not-contact list",
    "blocker.contact_opted_out": "this person asked not to be contacted",
    "blocker.cooldown": "we wrote to them too recently",
    "blocker.account_contact_cap": "too many people from this company are already being contacted",
    "blocker.out_of_icp": "this is not the kind of company we sell to",
    "blocker.missing_email": "we have no email for them",
    "blocker.unknown_account": "we do not know this company",
  },
  es: {
    "received.reply.received": "Llegó una respuesta del prospecto.",
    "received.crm.account_updated": "El CRM avisó de un cambio en la cuenta.",
    "received.prospect.identified": "Se identificó un prospecto nuevo.",
    "received.contact.unsubscribed": "El contacto se dio de baja.",
    "duplicate": "Este mismo mensaje ya había llegado. Se ignora: nada se hace dos veces.",
    "state_loaded": "Buscó a la empresa y a la persona en el expediente.",
    "state_loaded.customer": "Revisó el expediente: esta empresa ya es cliente.",
    "state_loaded.opp": "Revisó el expediente: un vendedor ya tiene un deal abierto aquí.",
    "ordering": "La respuesta se escribió antes del último cambio en la cuenta. Se juzga con los datos de hoy.",
    "stale_event": "Noticia vieja: el expediente ya tenía información más nueva. Se ignora, nada retrocede.",
    "state_updated": "Actualizó el expediente de la empresa.",
    "eligibility.ok": "Luz verde: podemos hablar con esta empresa.",
    "eligibility.blocked": "Alto: {reasons}.",
    "compliance.optout": "La persona pidió que paremos. Esto lo maneja una regla fija, nunca la IA.",
    "compliance.injection": "El mensaje intenta darle órdenes al sistema. Se marca.",
    "compliance.ok": "No pidió que paremos.",
    "ai.skipped": "No hizo falta la IA: las revisiones ya decidieron.",
    "ai.read": "La IA leyó el mensaje: {intent} (certeza {conf}).",
    "ai.none": "La IA no pudo leer el mensaje, así que lo hará una persona.",
    "ai_validation.ok": "Se comparó la lectura de la IA con el texto: todo lo que cita está ahí de verdad.",
    "ai_validation.fail": "La lectura de la IA no pasó las revisiones, así que decidirá una persona.",
    "freshness.ok": "Se volvió a revisar el CRM: nada cambió. Se puede actuar.",
    "freshness.diff": "El CRM tenía datos más nuevos. Se actualizó el expediente y se decidió de nuevo.",
    "freshness.other": "No se pudo volver a revisar el CRM ahora; se siguió con lo que sabemos.",
    "decision.auto": "Decisión: {action}, por su cuenta.",
    "decision.human": "Decisión: {action}. Lo revisará una persona.",
    "decision.none": "Decisión: no hacer nada. {reason}",
    "action_enqueued": "En cola: {action}.",
    "action_dispatched": "Hecho en el CRM: {action}.",
    "action_uncertain": "El CRM no confirmó. No sabemos si pasó, así que revisaremos antes de volver a intentar.",
    "action_reconciled.found": "Revisado: sí había pasado. No se manda dos veces.",
    "action_reconciled.missing": "Revisado: no había pasado. Se puede volver a mandar.",
    "action_retry_scheduled": "El CRM pidió que bajemos el ritmo. Se reintenta más tarde.",
    "action_dead": "Se rindió después de varios intentos. Lo atenderá una persona.",
    "review_queued": "Enviado a una persona para que lo revise.",
    "human_decision": "{message}",
    "completed": "Listo.",
    "failed": "Algo salió mal: {message}",
    "policy_changed": "Se cambiaron las reglas.",
    "blocker.already_customer": "ya son clientes",
    "blocker.active_opportunity": "un vendedor ya lleva este deal",
    "blocker.suppressed": "están en la lista de no contactar",
    "blocker.contact_opted_out": "esta persona pidió que no la contactemos",
    "blocker.cooldown": "les escribimos hace muy poco",
    "blocker.account_contact_cap": "ya hay demasiada gente de esta empresa en contacto",
    "blocker.out_of_icp": "no es el tipo de empresa a la que vendemos",
    "blocker.missing_email": "no tenemos su correo",
    "blocker.unknown_account": "no conocemos esta empresa",
  },
};

(function () {
  const KEY = "go.prefs";
  const saved = (() => { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; } })();
  const prefs = { lang: saved.lang === "es" ? "es" : "en", mode: saved.mode === "plain" ? "plain" : "tech" };

  function persist() { try { localStorage.setItem(KEY, JSON.stringify({ lang: window.prefs.lang, mode: window.prefs.mode })); } catch (e) {} }

  window.prefs = prefs;
  window.setLang = (l) => { window.prefs.lang = l; persist(); };
  window.setMode = (m) => { window.prefs.mode = m; persist(); };

  /* Lookup with fallback chain. Reads window.prefs so Alpine re-evaluates on change (prefs becomes reactive in base.html). */
  window.t = function (key, vars) {
    const p = window.prefs;
    const dicts = p.mode === "plain" ? [I18N[p.lang + "_plain"], I18N[p.lang], I18N.en] : [I18N[p.lang], I18N.en];
    let s;
    for (const d of dicts) { if (d && d[key] !== undefined) { s = d[key]; break; } }
    if (s === undefined) return key;
    if (vars) for (const k in vars) s = s.split("{" + k + "}").join(vars[k]);
    return s;
  };
  window.tAction = (a) => a ? t("action." + a) : "";
  window.tIntent = (i) => i ? t("intent." + i) : "";
  window.isPlain = () => window.prefs.mode === "plain";

  const pct = (c) => c === undefined || c === null ? "?" : Math.round(c * 100) + "%";

  /* Plain-language line for an audit row. Falls back to the raw message. */
  window.plainStage = function (row) {
    const P = STAGE_PLAIN[window.prefs.lang] || STAGE_PLAIN.en;
    const d = row.data || {};
    const fmt = (k, vars) => { let s = P[k]; if (s === undefined) return row.message; if (vars) for (const v in vars) s = s.split("{" + v + "}").join(vars[v]); return s; };
    switch (row.stage) {
      case "received": return P["received." + ((d.payload && d.payload.type) || (row.message || "").split(" ")[0])] || fmt("received.reply.received");
      case "duplicate": return fmt("duplicate");
      case "state_loaded":
        if (d.account && d.account.is_customer) return fmt("state_loaded.customer");
        if (d.account && d.account.has_open_opportunity) return fmt("state_loaded.opp");
        return fmt("state_loaded");
      case "ordering": return fmt("ordering");
      case "stale_event": return fmt("stale_event");
      case "state_updated": return fmt("state_updated");
      case "eligibility":
        if (d.eligible) return fmt("eligibility.ok");
        return fmt("eligibility.blocked", { reasons: (d.blockers || []).map(b => P["blocker." + b] || b).join(", ") });
      case "compliance":
        if (d.opt_out) return fmt("compliance.optout");
        if (d.injection_suspected) return fmt("compliance.injection");
        return fmt("compliance.ok");
      case "ai_interpretation":
        if (/skipped/.test(row.message)) return fmt("ai.skipped");
        if (d.interpretation) return fmt("ai.read", { intent: tIntent(d.interpretation.intent), conf: pct(d.interpretation.confidence) });
        return fmt("ai.none");
      case "ai_validation": return d.valid ? fmt("ai_validation.ok") : fmt("ai_validation.fail");
      case "freshness_check":
        if (/matches/.test(row.message)) return fmt("freshness.ok");
        if (/DIFFERS/.test(row.message)) return fmt("freshness.diff");
        return fmt("freshness.other");
      case "decision":
        if (d.action === "no_action") return fmt("decision.none", { reason: "" }).trim();
        if (d.action === "escalate_to_human") return fmt("decision.human", { action: tAction("escalate_to_human") });
        return d.automated ? fmt("decision.auto", { action: tAction(d.action) }) : fmt("decision.human", { action: tAction(d.action) });
      case "action_enqueued": return fmt("action_enqueued", { action: tAction((d.idempotency_key || "").split(":")[1]) });
      case "action_dispatched": return fmt("action_dispatched", { action: tAction((d.idempotency_key || "").split(":")[1]) });
      case "action_uncertain": return fmt("action_uncertain");
      case "action_reconciled": return /DID land/.test(row.message) ? fmt("action_reconciled.found") : fmt("action_reconciled.missing");
      case "action_retry_scheduled": return fmt("action_retry_scheduled");
      case "action_dead": return fmt("action_dead");
      case "review_queued": return fmt("review_queued");
      case "human_decision": return row.message;
      case "completed": return fmt("completed");
      case "failed": return fmt("failed", { message: row.message });
      case "policy_changed": return fmt("policy_changed");
      default: return row.message;
    }
  };

  /* Plain-mode labels for the stage pills. */
  const STAGE_LABEL = {
    en: { received: "message", duplicate: "repeat", state_loaded: "file", ordering: "timing", stale_event: "old news", state_updated: "file updated", eligibility: "may we?", compliance: "asked to stop?",
          ai_interpretation: "AI reads", ai_validation: "AI checked", freshness_check: "CRM check", decision: "decision", action_enqueued: "to do", action_dispatched: "done", action_uncertain: "not sure",
          action_reconciled: "verified", action_retry_scheduled: "retry later", action_dead: "gave up", review_queued: "to a person", human_decision: "person decided", completed: "end", failed: "error", policy_changed: "rules changed" },
    es: { received: "mensaje", duplicate: "repetido", state_loaded: "expediente", ordering: "orden", stale_event: "noticia vieja", state_updated: "expediente al día", eligibility: "¿podemos?", compliance: "¿pidió parar?",
          ai_interpretation: "IA lee", ai_validation: "IA verificada", freshness_check: "revisa CRM", decision: "decisión", action_enqueued: "por hacer", action_dispatched: "hecho", action_uncertain: "no seguro",
          action_reconciled: "verificado", action_retry_scheduled: "reintento", action_dead: "se rindió", review_queued: "a una persona", human_decision: "decidió persona", completed: "fin", failed: "error", policy_changed: "reglas cambiadas" },
  };
  window.stageLabel = (stage) => window.prefs.mode === "plain" ? ((STAGE_LABEL[window.prefs.lang] || STAGE_LABEL.en)[stage] || stage) : stage;
  window.stageText = (row) => window.prefs.mode === "plain" ? plainStage(row) : row.message;
})();

/* Demo step titles and notes (technical English lives in demo/scenarios.py). */
(function () {
  const steps = {
    es: {
      "step.happy_path.0.title": "El prospecto responde con interés y propone una hora",
      "step.happy_path.0.note": "Cuenta elegible, sin bloqueos. El modelo lee la respuesta; la política mapea 'interesado' a handoff; el outbox crea el deal y la tarea del AE.",
      "step.duplicate_event.0.title": "El webhook entrega la respuesta (primera vez)",
      "step.duplicate_event.1.title": "El proveedor reintenta y entrega el MISMO evento otra vez",
      "step.duplicate_event.1.note": "Mismo event_id. La ingesta choca con la llave primaria, registra el duplicado y nada corre después. Sigue habiendo exactamente un deal en el CRM.",
      "step.crm_failure_retry.0.title": "Intento #1 de handoff: el CRM hace timeout DESPUÉS de escribir el deal",
      "step.crm_failure_retry.0.note": "La escritura llegó pero nunca vimos la respuesta. La acción se marca 'incierta', no 'fallida', y se programa un reintento.",
      "step.crm_failure_retry.1.title": "Reintento #2 (30s después): reconciliar por llave de idempotencia; la tarea recibe un 429",
      "step.crm_failure_retry.1.note": "Antes de reenviar, el outbox le pregunta al CRM si el deal existe. Existe, así que se reutiliza en vez de crearse otra vez. La escritura dependiente (la tarea) recibe un límite de tasa y espera dos minutos.",
      "step.crm_failure_retry.2.title": "Reintento #3 (2 min después): todo se completa. Existen exactamente un deal y una tarea.",
      "step.crm_failure_retry.2.note": "La escritura del deal devuelve el registro existente; la tarea se crea una vez. El estado local se actualiza solo ahora, cuando la acción ya se sabe exitosa.",
      "step.unsafe_ai_injection.0.title": "Una respuesta que intenta darle instrucciones al sistema",
      "step.unsafe_ai_injection.0.note": "Dos capas independientes la atrapan: las heurísticas de reglas y la bandera de riesgo del propio modelo. Cualquiera de las dos basta para bloquear la automatización. Cero acciones externas; revisa un humano.",
      "step.ambiguous_mixed.0.title": "Interés + baja + referido en una sola frase",
      "step.ambiguous_mixed.0.note": "La REGLA de baja gana: el contacto se suprime automáticamente. El referido y el interés son señales reales, así que el caso va a un humano SIN más acciones automáticas.",
      "step.out_of_order.0.title": "El CRM dice: Delta Manufactura se volvió cliente (hace 1h)",
      "step.out_of_order.0.note": "El estado avanza; las secuencias activas de la cuenta se pausan.",
      "step.out_of_order.1.title": "Llega tarde un update del CRM de hace dos días diciendo que NO son clientes",
      "step.out_of_order.1.note": "Más viejo que la versión actual del estado: se ignora. Los datos tardíos nunca deben hacer retroceder el estado.",
      "step.out_of_order.2.title": "Llega ahora la respuesta de Sara (enviada hace 3h, antes de cerrar el deal)",
      "step.out_of_order.2.note": "Se evalúa contra el estado ACTUAL: la cuenta es cliente. El modelo ni se llama. Se avisa a Customer Success; nada se vende dos veces.",
      "step.freshness_check.0.title": "El estado local dice 'prospecto'; el CRM ya tiene una oportunidad abierta con un AE",
      "step.freshness_check.0.note": "La decisión habría sido un handoff. Antes de cualquier acción irreversible el orquestador relee el CRM, ve la diferencia, actualiza el estado local y vuelve a decidir: se avisa al AE en vez de crear un deal.",
    },
    en_plain: {
      "step.happy_path.0.title": "The prospect says yes and proposes a time",
      "step.happy_path.0.note": "We may talk to this company. The AI reads the reply, the rules say 'hand to a salesperson', and the deal and the salesperson's task get created.",
      "step.duplicate_event.0.title": "The reply arrives (first time)",
      "step.duplicate_event.1.title": "The tool sends the exact same reply again",
      "step.duplicate_event.1.note": "The assistant recognises it as the same message and does nothing. Still one deal.",
      "step.crm_failure_retry.0.title": "Try #1: the CRM saves the deal but never answers back",
      "step.crm_failure_retry.0.note": "We do not know if it worked. The assistant does not guess: it marks it 'not sure' and plans to check later.",
      "step.crm_failure_retry.1.title": "Try #2 (30 seconds later): check first, then the CRM says 'slow down'",
      "step.crm_failure_retry.1.note": "Before sending again, it asks the CRM: 'did you get it?'. Yes, so it reuses the deal instead of creating a second one. The CRM then asks us to slow down, so it waits two minutes.",
      "step.crm_failure_retry.2.title": "Try #3 (2 minutes later): everything is done. One deal, one task.",
      "step.crm_failure_retry.2.note": "Nothing was created twice, and the file is only updated once we are sure it worked.",
      "step.unsafe_ai_injection.0.title": "A reply that tries to give orders to the AI",
      "step.unsafe_ai_injection.0.note": "Two separate checks notice it: the fixed rules and the AI itself. Either one is enough to stop any automatic action. A person looks at it.",
      "step.ambiguous_mixed.0.title": "Interested, but 'remove me', but 'talk to my partner', all in one line",
      "step.ambiguous_mixed.0.note": "'Remove me' wins, by rule: we stop contacting them right away. The interest and the referral are real, so a person decides what to do with them. Nothing else happens on its own.",
      "step.out_of_order.0.title": "The CRM says: Delta Manufactura became a customer (an hour ago)",
      "step.out_of_order.0.note": "The file is updated and any ongoing emails to that company are paused.",
      "step.out_of_order.1.title": "Old news arrives late: a two-day-old note saying they are NOT a customer",
      "step.out_of_order.1.note": "Older than what we already know, so it is ignored. The file never goes backwards.",
      "step.out_of_order.2.title": "Sara's reply arrives now, but she wrote it three hours ago, before the deal closed",
      "step.out_of_order.2.note": "The assistant judges it on today's facts: they are a customer now. No sales handoff. Their account manager is told instead.",
      "step.freshness_check.0.title": "Our file says 'prospect', but the CRM already has a salesperson on this deal",
      "step.freshness_check.0.note": "The assistant was about to hand them to a salesperson. Before doing anything it asks the CRM one more time, sees the deal, updates the file and steps aside: it tells the salesperson instead.",
    },
    es_plain: {
      "step.happy_path.0.title": "El prospecto dice que sí y propone una hora",
      "step.happy_path.0.note": "Podemos hablar con esta empresa. La IA lee la respuesta, las reglas dicen 'pasar a un vendedor', y se crean el deal y la tarea del vendedor.",
      "step.duplicate_event.0.title": "Llega la respuesta (primera vez)",
      "step.duplicate_event.1.title": "La herramienta manda exactamente la misma respuesta otra vez",
      "step.duplicate_event.1.note": "El asistente reconoce que es el mismo mensaje y no hace nada. Sigue habiendo un solo deal.",
      "step.crm_failure_retry.0.title": "Intento #1: el CRM guarda el deal pero nunca contesta",
      "step.crm_failure_retry.0.note": "No sabemos si funcionó. El asistente no adivina: lo marca como 'no seguro' y planea revisar después.",
      "step.crm_failure_retry.1.title": "Intento #2 (30 segundos después): primero revisa, luego el CRM dice 'bajen el ritmo'",
      "step.crm_failure_retry.1.note": "Antes de volver a mandar, le pregunta al CRM: '¿te llegó?'. Sí, así que reutiliza el deal en vez de crear un segundo. Luego el CRM pide que bajemos el ritmo y espera dos minutos.",
      "step.crm_failure_retry.2.title": "Intento #3 (2 minutos después): todo listo. Un deal, una tarea.",
      "step.crm_failure_retry.2.note": "Nada se creó dos veces, y el expediente se actualiza solo cuando ya estamos seguros de que funcionó.",
      "step.unsafe_ai_injection.0.title": "Una respuesta que intenta darle órdenes a la IA",
      "step.unsafe_ai_injection.0.note": "Dos revisiones distintas lo notan: las reglas fijas y la propia IA. Cualquiera de las dos basta para frenar toda acción automática. Lo ve una persona.",
      "step.ambiguous_mixed.0.title": "Le interesa, pero 'quítenme', pero 'hablen con mi socio', todo en una línea",
      "step.ambiguous_mixed.0.note": "'Quítenme' gana, por regla: dejamos de contactarlo de inmediato. El interés y el referido son reales, así que una persona decide qué hacer con ellos. Nada más pasa por su cuenta.",
      "step.out_of_order.0.title": "El CRM dice: Delta Manufactura se volvió cliente (hace una hora)",
      "step.out_of_order.0.note": "Se actualiza el expediente y se pausan los correos en curso a esa empresa.",
      "step.out_of_order.1.title": "Llega tarde una noticia vieja: una nota de hace dos días diciendo que NO son clientes",
      "step.out_of_order.1.note": "Es más vieja que lo que ya sabemos, así que se ignora. El expediente nunca retrocede.",
      "step.out_of_order.2.title": "Llega ahora la respuesta de Sara, pero la escribió hace tres horas, antes de que cerrara el deal",
      "step.out_of_order.2.note": "El asistente la juzga con los datos de hoy: ya son clientes. No se pasa a ventas. Se le avisa a su ejecutivo de cuenta.",
      "step.freshness_check.0.title": "Nuestro expediente dice 'prospecto', pero el CRM ya tiene a un vendedor en este deal",
      "step.freshness_check.0.note": "El asistente estaba por pasarlo a un vendedor. Antes de hacer algo le pregunta al CRM una vez más, ve el deal, actualiza el expediente y se hace a un lado: le avisa al vendedor.",
    },
  };
  for (const k in steps) Object.assign(I18N[k], steps[k]);
})();

/* Glossary. Every term used in the console, the docs and the deck. */
window.GLOSSARY = {
  en: [
    { cat: "Sales", terms: [
      ["AE (Account Executive)", "The salesperson who closes. Receives qualified prospects, runs the demo, negotiates.", "Owner of an opportunity in the CRM. `handoff_to_ae` creates a deal and a task for this person; accounts with an AE-owned open opportunity are blocked for the machine."],
      ["SDR (Sales Development Representative)", "The person who prospects: sends emails, reads replies, qualifies, and passes good ones to an AE.", "The role whose reply-triage work this system automates in part."],
      ["CRM", "The database of companies, people and deals (HubSpot, Salesforce).", "Source of truth for account facts. Mocked here behind the `CRMClient` interface; `HubSpotCRM` is the production stub."],
      ["CSM (Customer Success Manager)", "The person who looks after customers after they buy.", "When a customer replies to sales outreach the system creates a task for the CSM instead of an AE (`notify_csm`)."],
      ["ICP (Ideal Customer Profile)", "The kind of company we sell to (size, country).", "Policy `eligibility.icp`: minimum employees and allowed countries. Outside ICP blocks outreach and routes pricing questions to a human."],
      ["Handoff", "Passing a prospect from the SDR to a salesperson.", "`handoff_to_ae`: irreversible action; creates deal + task through the outbox after a freshness check."],
      ["Sequence", "The series of emails a prospect receives over a few weeks.", "`enroll_in_sequence` action; `contacts.sequence_status` tracks enrolled/paused/completed."],
      ["Nurture", "Keeping in touch without selling, for people who said 'not now'.", "`nurture_long_term`: sets the contact lifecycle to nurture in the CRM."],
      ["Opt-out / unsubscribe / suppression", "Someone asks us to stop writing to them. We must comply, by law.", "Detected by regex rules in ES/PT/EN before the model. `suppress_contact` adds the email to `suppressions`; eligibility blocks any future outreach."],
      ["Cooldown", "Waiting time before writing to the same person again.", "`eligibility.cooldown_days`; blocks new outreach, not replies."],
      ["Enrichment", "Looking up extra data about a person or company (title, size).", "`enrich_contact`; mocked provider. Happens before enrolling in a sequence."],
      ["Pipeline (sales)", "All the deals in progress, valued in money.", "The experiment's primary metric is AE-accepted opportunities per eligible account, not volume of messages."],
      ["SQO (Sales Qualified Opportunity)", "A deal a salesperson agreed is real.", "Primary metric of the experiment: share of eligible accounts with an AE-accepted opportunity within 45 days."],
      ["RevOps (Revenue Operations)", "The team that runs sales tools and processes.", "Intended user of the Policy screen; edits `policy.yaml` without code."],
    ]},
    { cat: "System", terms: [
      ["Webhook", "A message one system sends to another the moment something happens.", "`POST /events`. Answers 202 immediately and processes in the background; optional HMAC signature."],
      ["Event", "One piece of news: a reply arrived, the CRM changed, a contact unsubscribed.", "`InboundEvent` with `event_id`, `type`, `occurred_at`, `payload`."],
      ["Idempotency / idempotency key", "Doing something twice has the same effect as doing it once. The key is the label that makes the second time recognisable.", "`events.event_id` primary key for events; `actions.idempotency_key = event_id:action` for side effects; the CRM adapter looks the key up before creating."],
      ["State", "The file we keep on each company and person.", "`accounts` and `contacts` tables with `state_version` and `state_updated_at`; never rolls back."],
      ["Out of order / stale event", "News arriving late or in the wrong sequence.", "CRM updates older than the current state version are ignored; replies are evaluated against current state."],
      ["Policy", "The rulebook of what the system may do on its own.", "`policy.yaml`: eligibility parameters, automation mode per action, AI thresholds, intent→action map. Versioned; every decision records the version used."],
      ["auto / assisted / off", "On its own / ask a person first / switched off.", "Per-action automation mode in `policy.automation`. Unknown actions default to assisted."],
      ["Outbox", "The to-do list of things to do in the CRM, kept so nothing is lost or done twice.", "`actions` table: pending → in_flight → succeeded / uncertain / failed / dead. Dispatched with retry and backoff."],
      ["Backoff", "Waiting a bit longer after each failed try.", "30s, 2m, 10m after attempts 1, 2, 3; four attempts then dead-letter."],
      ["429 / rate limit", "The CRM saying 'too many requests, slow down'.", "`RateLimited` → action stays pending with `next_attempt_at`."],
      ["Uncertain outcome / timeout after commit", "We sent the request, the CRM may have done it, but we never got an answer.", "`UncertainOutcome` → status `uncertain`; on retry the outbox reconciles by idempotency key before re-sending."],
      ["Reconcile", "Checking with the CRM whether something already happened before doing it again.", "`find_by_idempotency_key` on retry of an uncertain action."],
      ["Dead letter / DLQ", "Something that failed too many times and is parked for a person.", "Status `dead` + a review-queue item."],
      ["Freshness check", "Asking the CRM again right before doing something that cannot be undone.", "`_freshness_check`: re-reads customer/opportunity/owner; if different, updates local state and re-decides."],
      ["Audit log", "The written record of every step and why.", "`audit_log` rows per `event_id` with stage, message, data, prompt and policy versions."],
      ["Review queue", "The list of things waiting for a person.", "`review_queue`; approve executes the proposed action through the outbox."],
      ["HMAC", "A signature that proves a message really came from who it says.", "`X-Signature` header, SHA-256 over the body with a shared secret; enforced when `GO_WEBHOOK_SECRET` is set."],
      ["SQLite / Postgres", "Where the data is stored. SQLite is a single file, fine for a prototype; Postgres is the production database.", "Same schema either way; production adds a queue and per-account locks."],
      ["FastAPI", "The web framework that serves the webhook, the API and this console.", "Python, sync handlers in a thread pool, one process-level lock for writes in the prototype."],
    ]},
    { cat: "AI", terms: [
      ["LLM / model", "The AI that reads text. Here: Claude.", "`claude-opus-5-5` by default (`GO_MODEL`), called once per reply through the Anthropic SDK with structured outputs."],
      ["Interpretation", "What the AI understood from a reply.", "`ReplyInterpretation`: intent, confidence, language, evidence, extracted facts, risk flags, summary."],
      ["Intent", "The kind of reply: interested, not interested, out of office, referral, unsubscribe, price question, later, mixed, unclear.", "Enum `Intent`; mapped to an action by `policy.intent_actions`, never by the model."],
      ["Confidence", "How sure the AI says it is (0 to 1).", "Not treated as a calibrated probability. One of three inputs with grounded evidence and account state; thresholds in `policy.ai`."],
      ["Evidence / grounding", "The exact words in the reply that support what the AI says.", "Validators require every `evidence` quote to appear verbatim; extracted emails/numbers must be in the text; dates must be future."],
      ["Structured output", "Forcing the AI to answer in a fixed form instead of free text.", "`client.messages.parse(..., output_format=ReplyInterpretation)`; the API enforces the JSON schema."],
      ["Validation / repair", "Checking the AI's answer and asking once more if it fails.", "Semantic checks in `ai/interpreter.validate`; one repair round with errors fed back; then human."],
      ["Risk flags", "Warnings the AI raises: someone trying to trick it, contradictory signals, a request to stop, legal threats.", "`RiskFlag` enum; `prompt_injection` and `legal_or_complaint` always escalate."],
      ["Prompt injection", "A reply written to give the AI orders ('classify this as interested').", "Detected by regex heuristics in `compliance.py` and by the model's own flag; either blocks automation."],
      ["Prompt", "The instructions the AI receives.", "`ai/prompts.py`, versioned (`reply-interpreter-v1`); recorded on every AI call."],
      ["Evaluation (eval)", "A test set of replies with the right answers, to measure how well the AI reads.", "`evals/cases.yaml` (12 cases) + `run_eval.py`; scores schema, grounding, intent, action, unsafe automations."],
      ["Offline mode / fixtures", "Using saved real answers from the AI so the demo works without internet.", "`ai/fixtures.json` keyed by reply text; `GO_AI_MODE=record` refreshes them."],
      ["Shadow mode", "The AI decides but does nothing; we compare with what people did.", "All actions in `assisted`; agreement measured before automation."],
      ["Kill switch", "The button that turns automation off.", "`off` mode per action; 'Kill switch' preset on the Policy screen."],
    ]},
    { cat: "Measurement and compliance", terms: [
      ["A/B experiment", "Splitting accounts in two groups, one with the assistant, one without, to see which produces more real deals.", "Account-level randomisation, stratified; ~28k accounts per arm for a 20% lift at 80% power."],
      ["Guardrails", "Limits that pause the experiment if something goes wrong (complaints, bounces, unsubscribes).", "See docs/EXPERIMENT.md."],
      ["LFPDPPP / LGPD / Ley 1581", "The privacy laws of Mexico, Brazil and Colombia.", "Why opt-out is a rule and not a model decision, and why prompts receive minimal personal data."],
    ]},
  ],
  es: [
    { cat: "Ventas", terms: [
      ["AE (Account Executive)", "El vendedor que cierra. Recibe prospectos calificados, hace la demo, negocia.", "Dueño de una oportunidad en el CRM. `handoff_to_ae` crea un deal y una tarea para esta persona; las cuentas con oportunidad abierta de un AE se bloquean para la máquina."],
      ["SDR (Sales Development Representative)", "Quien prospecta: manda correos, lee respuestas, califica y pasa los buenos a un AE.", "El rol cuyo trabajo de triaje de respuestas este sistema automatiza en parte."],
      ["CRM", "La base de datos de empresas, personas y deals (HubSpot, Salesforce).", "Fuente de verdad de los hechos de la cuenta. Aquí está simulado detrás de la interfaz `CRMClient`; `HubSpotCRM` es el esqueleto de producción."],
      ["CSM (Customer Success Manager)", "Quien atiende a los clientes después de que compran.", "Cuando un cliente responde a un correo de ventas, el sistema crea una tarea para el CSM en vez de un AE (`notify_csm`)."],
      ["ICP (Ideal Customer Profile)", "El tipo de empresa a la que vendemos (tamaño, país).", "`eligibility.icp` en la política: empleados mínimos y países permitidos. Fuera de ICP bloquea la prospección y manda las preguntas de precio a un humano."],
      ["Handoff", "Pasar un prospecto del SDR a un vendedor.", "`handoff_to_ae`: acción irreversible; crea deal + tarea vía outbox después del chequeo de frescura."],
      ["Secuencia", "La serie de correos que recibe un prospecto durante unas semanas.", "Acción `enroll_in_sequence`; `contacts.sequence_status` lleva enrolled/paused/completed."],
      ["Nurture", "Mantener contacto sin vender, para quien dijo 'ahora no'.", "`nurture_long_term`: pone el ciclo de vida del contacto en nurture en el CRM."],
      ["Baja / opt-out / supresión", "Alguien pide que dejemos de escribirle. Hay que cumplir, por ley.", "Detectado por reglas regex en ES/PT/EN antes del modelo. `suppress_contact` agrega el correo a `suppressions`; la elegibilidad bloquea cualquier contacto futuro."],
      ["Enfriamiento (cooldown)", "Tiempo de espera antes de volver a escribirle a la misma persona.", "`eligibility.cooldown_days`; bloquea contactos nuevos, no respuestas."],
      ["Enriquecimiento", "Buscar datos extra de una persona o empresa (puesto, tamaño).", "`enrich_contact`; proveedor simulado. Ocurre antes de meter a alguien en secuencia."],
      ["Pipeline (ventas)", "Todos los deals en curso, valuados en dinero.", "La métrica primaria del experimento son oportunidades aceptadas por un AE por cuenta elegible, no volumen de mensajes."],
      ["SQO (Sales Qualified Opportunity)", "Un deal que un vendedor aceptó como real.", "Métrica primaria del experimento: porcentaje de cuentas elegibles con oportunidad aceptada por un AE en 45 días."],
      ["RevOps (Revenue Operations)", "El equipo que opera las herramientas y procesos de ventas.", "Usuario previsto de la pantalla de Política; edita `policy.yaml` sin código."],
    ]},
    { cat: "Sistema", terms: [
      ["Webhook", "Un mensaje que un sistema le manda a otro en el momento en que pasa algo.", "`POST /events`. Responde 202 de inmediato y procesa en segundo plano; firma HMAC opcional."],
      ["Evento", "Una noticia: llegó una respuesta, cambió el CRM, un contacto se dio de baja.", "`InboundEvent` con `event_id`, `type`, `occurred_at`, `payload`."],
      ["Idempotencia / llave de idempotencia", "Hacer algo dos veces tiene el mismo efecto que hacerlo una. La llave es la etiqueta que hace reconocible la segunda vez.", "`events.event_id` como llave primaria de eventos; `actions.idempotency_key = event_id:action` para efectos externos; el adaptador del CRM busca la llave antes de crear."],
      ["Estado", "El expediente que llevamos de cada empresa y persona.", "Tablas `accounts` y `contacts` con `state_version` y `state_updated_at`; nunca retrocede."],
      ["Desorden / evento viejo", "Noticias que llegan tarde o en el orden equivocado.", "Los updates del CRM más viejos que la versión actual del estado se ignoran; las respuestas se evalúan contra el estado actual."],
      ["Política", "El reglamento de qué puede hacer el sistema por su cuenta.", "`policy.yaml`: parámetros de elegibilidad, modo de automatización por acción, umbrales de IA, mapa intención→acción. Versionada; cada decisión registra la versión usada."],
      ["auto / assisted / off", "Solo / preguntar primero a una persona / apagado.", "Modo de automatización por acción en `policy.automation`. Las acciones desconocidas son assisted por defecto."],
      ["Outbox", "La lista de pendientes por hacer en el CRM, guardada para que nada se pierda ni se haga dos veces.", "Tabla `actions`: pending → in_flight → succeeded / uncertain / failed / dead. Se despacha con reintentos y backoff."],
      ["Backoff", "Esperar un poco más después de cada intento fallido.", "30s, 2m, 10m tras los intentos 1, 2, 3; cuatro intentos y luego dead-letter."],
      ["429 / límite de tasa", "El CRM diciendo 'demasiadas peticiones, bajen el ritmo'.", "`RateLimited` → la acción queda pending con `next_attempt_at`."],
      ["Resultado incierto / timeout después del commit", "Mandamos la petición, el CRM quizá la hizo, pero nunca recibimos respuesta.", "`UncertainOutcome` → estado `uncertain`; al reintentar, el outbox reconcilia por llave de idempotencia antes de reenviar."],
      ["Reconciliar", "Revisar con el CRM si algo ya pasó antes de hacerlo otra vez.", "`find_by_idempotency_key` al reintentar una acción incierta."],
      ["Dead letter / DLQ", "Algo que falló demasiadas veces y se estaciona para una persona.", "Estado `dead` + un item en la cola de revisión."],
      ["Chequeo de frescura", "Volver a preguntarle al CRM justo antes de hacer algo que no se puede deshacer.", "`_freshness_check`: relee cliente/oportunidad/dueño; si difiere, actualiza el estado local y vuelve a decidir."],
      ["Bitácora de auditoría", "El registro escrito de cada paso y su razón.", "Filas de `audit_log` por `event_id` con etapa, mensaje, datos, versiones de prompt y política."],
      ["Cola de revisión", "La lista de cosas que esperan a una persona.", "`review_queue`; aprobar ejecuta la acción propuesta vía outbox."],
      ["HMAC", "Una firma que prueba que un mensaje sí viene de quien dice.", "Header `X-Signature`, SHA-256 sobre el cuerpo con un secreto compartido; se exige cuando existe `GO_WEBHOOK_SECRET`."],
      ["SQLite / Postgres", "Dónde se guardan los datos. SQLite es un archivo, suficiente para un prototipo; Postgres es la base de producción.", "Mismo esquema en ambos; producción agrega una cola y locks por cuenta."],
      ["FastAPI", "El framework web que sirve el webhook, la API y esta consola.", "Python, handlers síncronos en un pool de hilos, un lock por proceso para escrituras en el prototipo."],
    ]},
    { cat: "IA", terms: [
      ["LLM / modelo", "La IA que lee texto. Aquí: Claude.", "`claude-opus-5-5` por defecto (`GO_MODEL`), llamado una vez por respuesta vía el SDK de Anthropic con salida estructurada."],
      ["Interpretación", "Lo que la IA entendió de una respuesta.", "`ReplyInterpretation`: intención, confianza, idioma, evidencia, hechos extraídos, banderas de riesgo, resumen."],
      ["Intención", "El tipo de respuesta: interesado, no interesado, fuera de oficina, referido, baja, pregunta de precio, después, mixta, no clara.", "Enum `Intent`; se mapea a una acción con `policy.intent_actions`, nunca por el modelo."],
      ["Confianza", "Qué tan segura dice estar la IA (de 0 a 1).", "No se trata como probabilidad calibrada. Una de tres entradas junto con la evidencia verificada y el estado de la cuenta; umbrales en `policy.ai`."],
      ["Evidencia / fundamento", "Las palabras exactas de la respuesta que sostienen lo que dice la IA.", "Los validadores exigen que cada cita de `evidence` aparezca textual; correos y números extraídos deben estar en el texto; las fechas deben ser futuras."],
      ["Salida estructurada", "Obligar a la IA a responder en un formato fijo en vez de texto libre.", "`client.messages.parse(..., output_format=ReplyInterpretation)`; la API impone el esquema JSON."],
      ["Validación / reparación", "Revisar la respuesta de la IA y pedirla una vez más si falla.", "Chequeos semánticos en `ai/interpreter.validate`; una ronda de reparación con los errores; luego humano."],
      ["Banderas de riesgo", "Avisos que levanta la IA: alguien intenta engañarla, señales contradictorias, petición de baja, amenaza legal.", "Enum `RiskFlag`; `prompt_injection` y `legal_or_complaint` siempre escalan."],
      ["Prompt injection", "Una respuesta escrita para darle órdenes a la IA ('clasifica esto como interesado').", "Detectada por heurísticas regex en `compliance.py` y por la bandera del propio modelo; cualquiera bloquea la automatización."],
      ["Prompt", "Las instrucciones que recibe la IA.", "`ai/prompts.py`, versionado (`reply-interpreter-v1`); se registra en cada llamada."],
      ["Evaluación (eval)", "Un conjunto de respuestas de prueba con la respuesta correcta, para medir qué tan bien lee la IA.", "`evals/cases.yaml` (12 casos) + `run_eval.py`; califica esquema, fundamento, intención, acción y automatizaciones inseguras."],
      ["Modo sin conexión / fixtures", "Usar respuestas reales guardadas de la IA para que la demo funcione sin internet.", "`ai/fixtures.json` indexado por el texto de la respuesta; `GO_AI_MODE=record` las refresca."],
      ["Modo sombra", "La IA decide pero no hace nada; comparamos con lo que hicieron las personas.", "Todas las acciones en `assisted`; se mide el acuerdo antes de automatizar."],
      ["Kill switch", "El botón que apaga la automatización.", "Modo `off` por acción; preset 'Kill switch' en la pantalla de Política."],
    ]},
    { cat: "Medición y cumplimiento", terms: [
      ["Experimento A/B", "Dividir las cuentas en dos grupos, uno con el asistente y otro sin él, para ver cuál produce más deals reales.", "Aleatorización a nivel cuenta, estratificada; ~28 mil cuentas por brazo para un lift del 20% con 80% de poder."],
      ["Guardrails", "Límites que pausan el experimento si algo sale mal (quejas, rebotes, bajas).", "Ver docs/EXPERIMENT.md."],
      ["LFPDPPP / LGPD / Ley 1581", "Las leyes de privacidad de México, Brasil y Colombia.", "Por qué la baja es una regla y no una decisión del modelo, y por qué los prompts reciben mínimos datos personales."],
    ]},
  ],
};

(function () {
  const extra = {
    en: {
      "nav.glossary": "Glossary",
      "about.s1.t": "A message arrives", "about.s1.d": "A prospect replies, the CRM changes, or someone unsubscribes. Each message has an id, so the same one is never handled twice.",
      "about.s2.t": "Check the file", "about.s2.d": "Who is this company? Are they a customer? Does a salesperson already own a deal? Did they ask us to stop? These checks are fixed rules.",
      "about.s3.t": "The AI reads", "about.s3.d": "Only for replies. It says what kind of reply it is, how sure it is, and quotes the exact words that prove it. It never decides.",
      "about.s4.t": "The rules decide", "about.s4.d": "A table turns the kind of reply into a next step. Switches say whether that step runs alone, asks a person first, or is off.",
      "about.s5.t": "It acts, carefully", "about.s5.d": "Deals, tasks and contacts are created in the CRM through a to-do list that retries safely and never duplicates.",
      "about.s6.t": "Everything is written down", "about.s6.d": "Every step, every reason and every version is recorded, so any decision can be explained later.",
      "glossary.title": "Glossary", "glossary.subtitle": "Every term used in the console, the documents and the presentation.",
      "glossary.search": "Search a term…", "glossary.plain": "In plain words", "glossary.tech": "Technically", "glossary.none": "No term matches.",
    },
    es: {
      "nav.glossary": "Diccionario",
      "about.s1.t": "Llega un mensaje", "about.s1.d": "Un prospecto responde, cambia el CRM o alguien se da de baja. Cada mensaje tiene un id, así el mismo nunca se atiende dos veces.",
      "about.s2.t": "Revisa el expediente", "about.s2.d": "¿Quién es esta empresa? ¿Ya es cliente? ¿Un vendedor ya lleva un deal? ¿Pidieron que paremos? Estas revisiones son reglas fijas.",
      "about.s3.t": "La IA lee", "about.s3.d": "Solo en respuestas. Dice qué tipo de respuesta es, qué tan segura está y cita las palabras exactas que lo prueban. Nunca decide.",
      "about.s4.t": "Las reglas deciden", "about.s4.d": "Una tabla convierte el tipo de respuesta en un siguiente paso. Los interruptores dicen si ese paso corre solo, pregunta primero o está apagado.",
      "about.s5.t": "Actúa, con cuidado", "about.s5.d": "Deals, tareas y contactos se crean en el CRM a través de una lista de pendientes que reintenta con seguridad y nunca duplica.",
      "about.s6.t": "Todo queda escrito", "about.s6.d": "Cada paso, cada razón y cada versión se registran, para poder explicar cualquier decisión después.",
      "glossary.title": "Diccionario", "glossary.subtitle": "Todos los términos que aparecen en la consola, los documentos y la presentación.",
      "glossary.search": "Busca un término…", "glossary.plain": "En palabras simples", "glossary.tech": "Técnicamente", "glossary.none": "Ningún término coincide.",
    },
  };
  Object.assign(I18N.en, extra.en); Object.assign(I18N.es, extra.es);
})();
