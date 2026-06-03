const questionInput = document.querySelector("#question");
const generateButton = document.querySelector("#generate-button");
const executeButton = document.querySelector("#execute-button");
const exampleButtons = document.querySelectorAll(".example-button");
const sqlOutput = document.querySelector("#sql-output");
const validationStatus = document.querySelector("#validation-status");
const explanation = document.querySelector("#explanation");
const modelSource = document.querySelector("#model-source");
const results = document.querySelector("#results");
const rowCount = document.querySelector("#row-count");

let currentSql = "";

exampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question || "";
    questionInput.focus();
  });
});

function setBusy(button, label, busy) {
  button.disabled = busy;
  button.textContent = busy ? "Working..." : label;
}

function setValidation(validation) {
  validationStatus.classList.remove("neutral", "valid", "invalid");
  if (!validation) {
    validationStatus.classList.add("neutral");
    validationStatus.textContent = "Not validated";
    return;
  }

  validationStatus.classList.add(validation.valid ? "valid" : "invalid");
  validationStatus.textContent = validation.valid ? "Valid SQL" : "Needs review";
}

function renderError(message) {
  results.innerHTML = `<p class="error">${escapeHtml(message)}</p>`;
  rowCount.textContent = "Error";
}

function renderTable(columns, rows) {
  if (!rows.length) {
    results.innerHTML = '<p class="empty">The query ran successfully and returned no rows.</p>';
    rowCount.textContent = "0 rows";
    return;
  }

  const header = columns.map((column) => `<th scope="col">${escapeHtml(column)}</th>`).join("");
  const body = rows
    .map((row) => {
      const cells = columns
        .map((column) => `<td>${escapeHtml(String(row[column] ?? ""))}</td>`)
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  results.innerHTML = `<table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
  rowCount.textContent = `${rows.length} ${rows.length === 1 ? "row" : "rows"}`;
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[char];
  });
}

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    const detail = payload.detail?.reason || payload.detail || "Request failed";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

generateButton.addEventListener("click", async () => {
  const question = questionInput.value.trim();
  if (!question) {
    renderError("Enter a question before generating SQL.");
    return;
  }

  setBusy(generateButton, "Generate SQL", true);
  executeButton.disabled = true;
  setValidation(null);
  rowCount.textContent = "No rows yet";
  results.innerHTML = '<p class="empty">Run a generated query to preview read-only SQLite results.</p>';

  try {
    const payload = await postJson("/generate", { question });
    currentSql = payload.sql.trim();
    sqlOutput.textContent = currentSql;
    explanation.textContent = payload.explanation;
    modelSource.textContent = payload.source || "rules";
    setValidation(payload.validation);
    executeButton.disabled = !payload.validation.valid;
  } catch (error) {
    currentSql = "";
    sqlOutput.textContent = "SQL generation failed.";
    explanation.textContent = "SchemaSage could not generate SQL for that question.";
    renderError(error.message);
  } finally {
    setBusy(generateButton, "Generate SQL", false);
  }
});

executeButton.addEventListener("click", async () => {
  if (!currentSql) {
    renderError("Generate SQL before executing.");
    return;
  }

  setBusy(executeButton, "Execute", true);
  try {
    const payload = await postJson("/execute", { sql: currentSql, max_rows: 100 });
    setValidation(payload.validation);
    renderTable(payload.columns, payload.rows);
  } catch (error) {
    renderError(error.message);
  } finally {
    executeButton.disabled = false;
    executeButton.textContent = "Execute";
  }
});
