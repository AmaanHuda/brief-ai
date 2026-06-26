// ── CONFIG — change this to your deployed backend URL ──────────────────────
const API_BASE = "https://brief-ai-xh6b.onrender.com";

// ── SCAN ANIMATION ──────────────────────────────────────────────────────────
const chips = document.querySelectorAll("#scanChips .chip");
let scanIdx = 0;
function runScan() {
  if (scanIdx > 0) {
    const prev = chips[scanIdx - 1];
    prev.classList.remove("active");
    prev.classList.add("done");
    prev.textContent = "✓ " + prev.dataset.label;
  }
  if (scanIdx < chips.length) {
    const chip = chips[scanIdx];
    chip.classList.add("active");
    const sweep = document.createElement("span");
    sweep.className = "chip-sweep";
    chip.appendChild(sweep);
    scanIdx++;
    setTimeout(runScan, 700);
  } else {
    setTimeout(() => {
      chips.forEach((c) => {
        c.classList.remove("active", "done");
        c.textContent = c.dataset.label;
      });
      scanIdx = 0;
      setTimeout(runScan, 800);
    }, 1800);
  }
}
setTimeout(runScan, 600);

// ── STATE ───────────────────────────────────────────────────────────────────
let rawMarkdown = "";

// ── STEP HELPERS ────────────────────────────────────────────────────────────
function setStep(n, state) {
  const el = document.getElementById("step" + n);
  const icon = document.getElementById("step" + n + "-icon");
  el.className = "step " + state;
  if (state === "active") {
    icon.innerHTML = '<span class="spinner"></span>';
  } else if (state === "done") {
    icon.textContent = "✓";
  } else if (state === "error") {
    icon.textContent = "!";
  } else {
    icon.textContent = n;
  }
}

// ── GENERATE ────────────────────────────────────────────────────────────────
async function generate() {
  const company = document.getElementById("companyInput").value.trim();
  const url = document.getElementById("urlInput").value.trim();
  if (!company || !url) {
    document.getElementById("companyInput").focus();
    return;
  }

  const btn = document.getElementById("generateBtn");
  const progressArea = document.getElementById("progressArea");
  const errorBox = document.getElementById("errorBox");
  const outputSection = document.getElementById("outputSection");

  btn.disabled = true;
  document.getElementById("btnLabel").textContent = "Generating…";
  progressArea.classList.remove("hidden");
  errorBox.classList.add("hidden");
  outputSection.classList.add("hidden");

  setStep(1, "active");
  setStep(2, "inactive");
  setStep(3, "inactive");
  setTimeout(
    () =>
      document
        .getElementById("generator")
        .scrollIntoView({ behavior: "smooth", block: "start" }),
    100,
  );

  // Animate steps while request runs (backend handles all three phases)
  const step2Timer = setTimeout(() => {
    setStep(1, "done");
    setStep(2, "active");
  }, 2500);
  const step3Timer = setTimeout(() => {
    setStep(2, "done");
    setStep(3, "active");
  }, 6000);

  try {
    const resp = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_name: company, url }),
    });

    clearTimeout(step2Timer);
    clearTimeout(step3Timer);

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${resp.status}`);
    }

    const data = await resp.json();
    rawMarkdown = data.brochure;

    setStep(1, "done");
    setStep(2, "done");
    setStep(3, "done");

    document.getElementById("outputTitle").textContent =
      company + " — Brochure";
    document.getElementById("brochureBody").innerHTML =
      marked.parse(rawMarkdown);
    outputSection.classList.remove("hidden");
    setTimeout(
      () =>
        outputSection.scrollIntoView({
          behavior: "smooth",
          block: "start",
        }),
      200,
    );
  } catch (e) {
    clearTimeout(step2Timer);
    clearTimeout(step3Timer);
    setStep(1, "inactive");
    setStep(2, "inactive");
    setStep(3, "error");
    errorBox.textContent =
      e.message || "Something went wrong. Is the backend running?";
    errorBox.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    document.getElementById("btnLabel").textContent = "Generate brochure";
  }
}

// ── COPY ────────────────────────────────────────────────────────────────────
function copyMarkdown() {
  if (!rawMarkdown) return;
  navigator.clipboard.writeText(rawMarkdown).then(() => {
    const btn = document.getElementById("copyMdBtn");
    btn.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = "Copy markdown";
      btn.classList.remove("copied");
    }, 2000);
  });
}

// ── RESET ───────────────────────────────────────────────────────────────────
function resetForm() {
  document.getElementById("companyInput").value = "";
  document.getElementById("urlInput").value = "";
  document.getElementById("outputSection").classList.add("hidden");
  document.getElementById("progressArea").classList.add("hidden");
  rawMarkdown = "";
  setStep(1, "inactive");
  setStep(2, "inactive");
  setStep(3, "inactive");
  document.getElementById("generator").scrollIntoView({ behavior: "smooth" });
  document.getElementById("companyInput").focus();
}

// ── KEYBOARD ────────────────────────────────────────────────────────────────
document.getElementById("companyInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") document.getElementById("urlInput").focus();
});
document.getElementById("urlInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") generate();
});
