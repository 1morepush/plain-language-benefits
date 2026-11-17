/*
 * app.js — draws the Plain Path screens and moves between them.
 *
 * The screens, in order:
 *   welcome -> intake (yes/no) -> documents (pause and gather) -> walkthrough -> done
 *
 * Privacy notes:
 *   - Intake answers and ticks never leave the browser. They are kept in
 *     sessionStorage, which the browser deletes when the tab is closed.
 *   - Only the language choice is remembered longer (localStorage).
 *   - All text is added with textContent, never innerHTML, so text from the data
 *     files can never run as code.
 */

const main = document.getElementById("main");

let content = null; // filled from /api/content
let state = {
  lang: "en",
  screen: "welcome",
  answers: {},       // intake key -> true / false
  docsChecked: {},   // checklist id -> true
  sectionIndex: 0,   // which visible section is open
  furthest: 0,       // how far the user has got (for the progress list)
};

/* ---------- small helpers ---------- */

// Look up a piece of website text in the current language.
function t(key, values) {
  let text = STRINGS[state.lang][key] || STRINGS.en[key] || key;
  for (const name in values || {}) text = text.replace("{" + name + "}", values[name]);
  return text;
}

// Pick the English or Spanish field from a data item, e.g. pick(section, "title").
function pick(item, field) {
  return item[field + "_" + state.lang] || item[field + "_en"];
}

// Build an HTML element: el("p", { class: "note" }, "some text")
function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const name in attrs || {}) {
    // onclick, onchange, onsubmit ... become event listeners.
    if (name.startsWith("on")) node.addEventListener(name.slice(2), attrs[name]);
    else if (attrs[name] !== false && attrs[name] != null) node.setAttribute(name, attrs[name]);
  }
  for (const child of children.flat(Infinity)) {
    if (child == null || child === false) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

function button(label, onclick, secondary) {
  return el("button", { type: "button", class: secondary ? "btn secondary" : "btn", onclick }, label);
}

// A link that opens in a new tab and says so (for screen reader users too).
function externalLink(label, url) {
  return el("a", { href: url, target: "_blank", rel: "noopener noreferrer" }, label, " ", t("newTab"));
}

// A section or checklist item with "show_if" only appears if that intake answer was Yes.
function isVisible(item) {
  return !item.show_if || state.answers[item.show_if] === true;
}
function visibleSections() {
  return content.sections.filter(isVisible);
}

/* ---------- remembering where the user is ---------- */

function save() {
  try {
    sessionStorage.setItem("plainpath", JSON.stringify(state));
    localStorage.setItem("plainpath-lang", state.lang);
  } catch (e) { /* storage can be blocked (private mode). The app still works. */ }
}

function restore() {
  try {
    const saved = JSON.parse(sessionStorage.getItem("plainpath") || "null");
    if (saved) state = Object.assign(state, saved);
    const lang = localStorage.getItem("plainpath-lang");
    if (lang === "en" || lang === "es") state.lang = lang;
  } catch (e) { /* ignore */ }
}

function go(screen) {
  state.screen = screen;
  render(true);
}

/* ---------- drawing ---------- */

function render(moveFocus) {
  // Text that lives in index.html (header, footer, skip link).
  document.documentElement.lang = state.lang;
  for (const node of document.querySelectorAll("[data-i18n]")) node.textContent = t(node.dataset.i18n);
  for (const btn of document.querySelectorAll("[data-lang]")) {
    btn.setAttribute("aria-pressed", String(btn.dataset.lang === state.lang));
  }

  const screens = { welcome, intake, documents, walkthrough, done };
  main.replaceChildren(...screens[state.screen]().flat());
  save();

  // After changing screens, start at the top and tell screen readers where we are.
  if (moveFocus) {
    window.scrollTo(0, 0);
    main.focus();
  }
}

function welcome() {
  const list = (keys) => el("ul", {}, keys.map((k) => el("li", {}, t(k))));
  return [
    el("h1", {}, t("welcomeTitle")),
    el("p", {}, t("welcomeIntro")),
    el("h2", {}, t("doesTitle")),
    list(["does1", "does2", "does3", "does4"]),
    el("h2", {}, t("doesNotTitle")),
    list(["doesNot1", "doesNot2", "doesNot3", "doesNot4"]),
    el("div", { class: "btn-row" }, button(t("start"), () => go("intake"))),
  ];
}

function intake() {
  const error = el("p", { class: "error", role: "alert" });

  const questions = content.intake.map((item) => {
    const radio = (value, label) =>
      el("label", { class: "choice" },
        el("input", {
          type: "radio", name: item.key, value: String(value),
          checked: state.answers[item.key] === value ? "" : false,
          onchange: () => { state.answers[item.key] = value; error.textContent = ""; save(); },
        }),
        label);
    return el("fieldset", {},
      el("legend", {}, pick(item, "text")),
      el("div", { class: "choices" }, radio(true, t("yes")), radio(false, t("no"))));
  });

  const onContinue = () => {
    const allAnswered = content.intake.every((item) => typeof state.answers[item.key] === "boolean");
    if (!allAnswered) { error.textContent = t("intakeError"); return; }
    // The answers may have changed which sections exist, so start from the first one.
    state.sectionIndex = 0;
    state.furthest = 0;
    go("documents");
  };

  return [
    el("h1", {}, t("intakeTitle")),
    el("p", {}, t("intakeIntro")),
    el("form", { novalidate: "" }, questions),
    error,
    el("div", { class: "btn-row" },
      button(t("back"), () => go("welcome"), true),
      button(t("next"), onContinue)),
  ];
}

function documents() {
  const items = content.checklist.filter(isVisible).map((item) =>
    el("li", {},
      el("label", { class: "tick" },
        el("input", {
          type: "checkbox",
          checked: state.docsChecked[item.id] ? "" : false,
          onchange: (e) => { state.docsChecked[item.id] = e.target.checked; save(); },
        }),
        pick(item, "text"))));

  return [
    el("h1", {}, t("docsTitle")),
    el("p", {}, t("docsIntro")),
    el("ul", { class: "ticks" }, items),
    el("div", { class: "btn-row" },
      button(t("back"), () => go("intake"), true),
      button(t("docsContinue"), () => go("walkthrough"))),
  ];
}

function walkthrough() {
  const sections = visibleSections();
  if (state.sectionIndex >= sections.length) state.sectionIndex = 0;
  const section = sections[state.sectionIndex];
  const isLast = state.sectionIndex === sections.length - 1;
  state.furthest = Math.max(state.furthest, state.sectionIndex);

  const progress = el("ol", { class: "progress" }, sections.map((s, i) => {
    const current = i === state.sectionIndex;
    const status = current ? "statusCurrent" : i <= state.furthest ? "statusDone" : "statusTodo";
    return el("li", { class: current ? "current" : false, "aria-current": current ? "step" : false },
      pick(s, "title"), " ", el("span", { class: "status" }, "(" + t(status) + ")"));
  }));

  const questions = content.questions.filter((q) => q.section === section.id);
  const cards = questions.map((q, i) => questionCard(q, i + 1, questions.length));

  const move = (step) => { state.sectionIndex += step; render(true); };

  return [
    el("p", { class: "note" }, t("stepOf", { n: state.sectionIndex + 1, total: sections.length })),
    el("h1", {}, pick(section, "title")),
    el("h2", {}, t("progressTitle")),
    progress,
    cards.length ? cards : el("p", {}, t("noQuestions")),
    el("p", { class: "note" }, t("notListed"), " ",
      externalLink(pick(content.help.official_instructions, "name"), content.help.official_instructions.url)),
    el("div", { class: "btn-row" },
      state.sectionIndex === 0
        ? button(t("back"), () => go("documents"), true)
        : button(t("prevSection"), () => move(-1), true),
      isLast
        ? button(t("finish"), () => go("done"))
        : button(t("nextSection"), () => move(1))),
  ];
}

function questionCard(q, number, total) {
  // Official wording: always shown, never changed. In Spanish, use the official
  // Spanish wording if we have it. Otherwise show the English and say so.
  const hasSpanish = state.lang === "es" && q.official_text_es;
  const official = el("blockquote", { class: "official", lang: hasSpanish ? "es" : "en" },
    el("p", {}, hasSpanish ? q.official_text_es : q.official_text_en));

  // The server only sends explanations a person has reviewed. null = not reviewed yet.
  const explanation = q.explanation[state.lang];

  const parts = [
    el("h2", {}, t("questionN", { n: number, total })),
    el("p", { class: "label" }, t("officialLabel")),
    official,
    state.lang === "es" && !q.official_text_es && el("p", { class: "note" }, t("officialOnlyEnglish")),
    el("p", { class: "label" }, t("plainLabel")),
  ];

  if (explanation) {
    parts.push(el("p", {}, explanation.text));
    if (explanation.you_will_need.length) {
      parts.push(el("p", { class: "label" }, t("needLabel")));
      parts.push(el("ul", {}, explanation.you_will_need.map((item) => el("li", {}, item))));
    }
  } else {
    parts.push(el("p", { class: "coming-soon" }, t("comingSoon"), " ",
      externalLink(pick(content.help.official_instructions, "name"), content.help.official_instructions.url)));
  }

  // High-risk questions always get the "Check with a person" box, reviewed or not.
  if (q.high_risk) parts.push(checkWithPerson(explanation));

  parts.push(el("p", { class: "source" }, t("sourceLabel"), ": ", q.source));

  // The chat box only appears when the server has an API key to answer with.
  if (content.chat_enabled) parts.push(askBox(q));
  return el("article", { class: "card" }, parts);
}

// The DES help line and the legal aid links, as a list.
function helpLinks() {
  const agency = content.help.agency;
  return el("ul", {},
    el("li", {},
      externalLink(pick(agency, "name"), agency.url), ". ", t("callLabel"), " ",
      el("a", { href: "tel:" + agency.phone.replace(/[^0-9+]/g, "") }, agency.phone)),
    content.help.legal_aid.map((org) => el("li", {}, externalLink(pick(org, "name"), org.url))));
}

/*
 * "Ask about this question": one message in, one reply out, about this question only.
 * Nothing typed here is saved. Each message is sent on its own, with no history.
 */
function askBox(q) {
  const inputId = "ask-" + q.id;
  const input = el("textarea", { id: inputId, rows: "3", maxlength: "500" });
  const warning = el("p", { class: "error", role: "alert" });
  const thread = el("div", { class: "thread", "aria-live": "polite" });
  const send = el("button", { type: "submit", class: "btn" }, t("askSend"));

  const onsubmit = async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    warning.textContent = "";
    if (!message) { warning.textContent = t("askEmpty"); return; }

    // SSN check in the browser: stop here, so the message never leaves this device.
    // (The server checks again in case this check is bypassed.)
    if (looksLikeSsn(message)) { warning.textContent = t("ssnWarning"); return; }

    const waiting = el("p", { class: "note" }, t("askWaiting"));
    thread.append(el("p", { class: "asked" }, el("strong", {}, t("askYou")), " ", message), waiting);
    input.value = "";
    send.disabled = true;

    let reply = t("askError");
    let writtenByAi = false;
    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_id: q.id, message, lang: state.lang }),
      });
      const data = await response.json();
      // A normal reply is in "reply". Problems come back as "message" (or message_en/_es).
      reply = data.reply || data["message_" + state.lang] || data.message || reply;
      writtenByAi = data.source === "ai";
    } catch (e) { /* network trouble: keep the "could not send" text */ }

    waiting.remove();
    thread.append(el("div", { class: "reply" },
      el("p", {}, el("strong", {}, t("askReplyLabel")), " ", reply),
      writtenByAi && el("p", { class: "note" }, t("askAiNote")),
      el("p", { class: "note" }, t("askHelp")),
      helpLinks()));
    send.disabled = false;
  };

  return el("form", { class: "ask", onsubmit, novalidate: "" },
    el("h3", {}, t("askTitle")),
    el("p", { class: "note" }, t("askHint")),
    el("label", { for: inputId, class: "label" }, t("askLabel")),
    input,
    warning,
    el("div", { class: "btn-row" }, send),
    thread);
}

function checkWithPerson(explanation) {
  return el("div", { class: "check" },
    el("h3", {}, t("checkTitle")),
    el("p", {}, (explanation && explanation.check_reason) || t("checkDefault")),
    helpLinks());
}

function done() {
  const official = content.help.official_instructions;
  const startOver = () => {
    state = Object.assign(state, { answers: {}, docsChecked: {}, sectionIndex: 0, furthest: 0 });
    go("welcome");
  };
  return [
    el("h1", {}, t("doneTitle")),
    el("p", {}, t("doneIntro")),
    el("p", {}, externalLink(pick(official, "name"), official.url)),
    el("div", { class: "btn-row" },
      button(t("review"), () => go("walkthrough"), true),
      button(t("startOver"), startOver, true)),
  ];
}

/* ---------- start ---------- */

for (const btn of document.querySelectorAll("[data-lang]")) {
  btn.addEventListener("click", () => { state.lang = btn.dataset.lang; render(false); });
}

restore();
fetch("/api/content")
  .then((response) => {
    if (!response.ok) throw new Error("bad response");
    return response.json();
  })
  .then((data) => { content = data; render(false); })
  .catch(() => { main.replaceChildren(el("p", { class: "error", role: "alert" }, t("loadError"))); });
