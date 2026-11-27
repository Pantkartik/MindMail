const chatForm = document.querySelector("#chatForm");
const questionInput = document.querySelector("#question");
const sendButton = document.querySelector("#sendButton");
const answerPanel = document.querySelector("#answer");
const answerText = document.querySelector("#answerText");
const answerState = document.querySelector("#answerState");
const citations = document.querySelector("#citations");
const apiState = document.querySelector("#apiState");
const apiLabel = document.querySelector("#sidebarStatus");
const sidebarLight = document.querySelector("#sidebarLight");
const statusOrb = document.querySelector("#statusOrb");
const connectionNote = document.querySelector("#connectionNote");
const footerApi = document.querySelector("#footerApi");

document.querySelector("#todayLabel").textContent = new Intl.DateTimeFormat(
  undefined,
  { weekday: "short", month: "short", day: "numeric" },
).format(new Date());

function setApiStatus(online, message) {
  const state = online ? "ONLINE" : "OFFLINE";
  apiState.textContent = state;
  apiLabel.textContent = online ? "Local API available" : "Local API unavailable";
  footerApi.textContent = `API STATUS: ${state}`;
  connectionNote.textContent = message;
  sidebarLight.classList.toggle("is-online", online);
  sidebarLight.classList.toggle("is-offline", !online);
  statusOrb.classList.toggle("is-online", online);
  statusOrb.classList.toggle("is-offline", !online);
}

function makeElement(tag, className, content) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (content !== undefined) element.textContent = content;
  return element;
}

function formatDate(value, options) {
  if (!value) return "DATE NOT SET";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(
    undefined,
    options ?? { month: "short", day: "numeric" },
  ).format(date);
}

function showMessage(container, message, isError = false) {
  container.replaceChildren(
    makeElement("div", isError ? "error-row" : "empty-row", message),
  );
}

function renderMail(emails) {
  const container = document.querySelector("#mailRows");
  container.replaceChildren();
  document.querySelector("#mailCount").textContent =
    `${emails.length} ${emails.length === 1 ? "RECORD" : "RECORDS"}`;

  if (!emails.length) {
    showMessage(container, "No sample messages are available.");
    return;
  }

  emails.forEach((email) => {
    const row = makeElement("div", "board-row mail-row");
    row.setAttribute("role", "row");
    const sender = makeElement("div");
    sender.setAttribute("role", "cell");
    sender.append(
      makeElement("span", "row-primary", email.sender || "Sample sender"),
      makeElement("span", "sample-mark", "SAMPLE"),
      makeElement("span", "row-secondary mobile-date", formatDate(email.date)),
    );

    const subject = makeElement("div");
    subject.setAttribute("role", "cell");
    subject.append(
      makeElement("span", "row-primary", email.subject || "Sample message"),
      makeElement("span", "row-secondary", email.snippet || "No preview available."),
    );

    const date = makeElement("div", "row-date", formatDate(email.date));
    date.setAttribute("role", "cell");
    row.append(sender, subject, date);
    container.append(row);
  });
}

function renderEvents(events) {
  const container = document.querySelector("#eventRows");
  container.replaceChildren();
  document.querySelector("#eventCount").textContent =
    `${events.length} ${events.length === 1 ? "EVENT" : "EVENTS"}`;

  if (!events.length) {
    showMessage(container, "No sample events are available.");
    return;
  }

  events.forEach((event) => {
    const row = makeElement("div", "board-row event-row");
    row.setAttribute("role", "row");

    const when = makeElement("div", "row-date");
    when.setAttribute("role", "cell");
    when.append(
      makeElement("span", "row-primary", formatDate(event.start, {
        weekday: "short",
        month: "short",
        day: "numeric",
      })),
      makeElement("span", "row-secondary", formatDate(event.start, {
        hour: "numeric",
        minute: "2-digit",
      })),
    );

    const title = makeElement("div");
    title.setAttribute("role", "cell");
    title.append(
      makeElement("span", "row-primary", event.summary || "Sample event"),
      makeElement("span", "sample-mark", "SAMPLE"),
    );

    const detail = makeElement(
      "span",
      "row-secondary event-detail",
      event.description || "No details provided.",
    );
    detail.setAttribute("role", "cell");
    row.append(when, title, detail);
    container.append(row);
  });
}

async function loadOverview() {
  try {
    const [healthResponse, overviewResponse] = await Promise.all([
      fetch("/health"),
      fetch("/api/v1/demo/overview"),
    ]);
    if (!healthResponse.ok || !overviewResponse.ok) {
      throw new Error("The local API returned an error. Retry when it is available.");
    }

    const health = await healthResponse.json();
    const overview = await overviewResponse.json();
    if (health.mode !== "local_demo" || overview.sample_data !== true) {
      throw new Error("The API did not confirm local demo mode.");
    }

    renderMail(Array.isArray(overview.emails) ? overview.emails : []);
    renderEvents(Array.isArray(overview.events) ? overview.events : []);
    setApiStatus(true, "Connected to the local demo API. Workspace records are sample fixtures.");
  } catch (error) {
    const message = error instanceof Error ? error.message : "The local API could not be reached.";
    setApiStatus(false, message);
    showMessage(document.querySelector("#mailRows"), "Could not load messages. Start the API, then reload this page.", true);
    showMessage(document.querySelector("#eventRows"), "Could not load events. Start the API, then reload this page.", true);
  }
}

function addCitation(citation) {
  const source = citation.source || "Sample source";
  const title = citation.title || "Untitled sample";
  const item = makeElement("div", "citation");
  item.append(
    makeElement("span", "citation-source", source.toUpperCase()),
    makeElement("span", "citation-title", title),
  );
  citations.append(item);
}

function handleServerEvent(payload) {
  if (!payload || payload === "[DONE]") return;
  let event;
  try {
    event = JSON.parse(payload);
  } catch {
    throw new Error("The local API returned an unreadable event.");
  }

  if (event.type === "trace") {
    answerState.textContent = "LOCAL DEMO";
    answerText.textContent = event.message || "Preparing the local demo response.";
  } else if (event.type === "content") {
    answerState.textContent = "SAMPLE RESPONSE";
    answerText.textContent = event.text || "The demo returned no response text.";
    for (const citation of event.citations || []) addCitation(citation);
  } else if (event.type === "error") {
    throw new Error(event.message || "The local demo could not answer this question.");
  }
}

async function readEventStream(response) {
  if (!response.body) {
    throw new Error("Streaming is unavailable in this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const events = buffer.split(/\r?\n\r?\n/);
    buffer = events.pop() || "";

    for (const rawEvent of events) {
      for (const line of rawEvent.split(/\r?\n/)) {
        if (line.startsWith("data:")) handleServerEvent(line.slice(5).trimStart());
      }
    }
    if (done) break;
  }

  if (buffer.startsWith("data:")) handleServerEvent(buffer.slice(5).trimStart());
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = questionInput.value.trim();
  if (!message) {
    questionInput.focus();
    return;
  }

  answerPanel.hidden = false;
  answerText.textContent = "Connecting to the local demo...";
  answerState.textContent = "SENDING";
  citations.replaceChildren();
  sendButton.disabled = true;
  sendButton.querySelector("span").textContent = "Sending";

  try {
    const response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      throw new Error(errorBody?.detail || "The local API could not accept this question.");
    }
    await readEventStream(response);
    answerState.textContent = "DEMO ONLY";
  } catch (error) {
    answerState.textContent = "NOT SENT";
    answerText.textContent = error instanceof Error
      ? error.message
      : "The question could not reach the local demo. Check that the API is running.";
    citations.replaceChildren();
  } finally {
    sendButton.disabled = false;
    sendButton.querySelector("span").textContent = "Send question";
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.prompt || "";
    questionInput.focus();
  });
});

const sectionObserver = new IntersectionObserver(
  (entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    document.querySelectorAll(".station-link").forEach((link) => {
      const current = link.hash === `#${visible.target.id}`;
      link.classList.toggle("is-current", current);
      if (current) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  },
  { rootMargin: "-20% 0px -65% 0px", threshold: [0, 0.1, 0.5] },
);

document.querySelectorAll(".section-anchor").forEach((section) => sectionObserver.observe(section));
loadOverview();
