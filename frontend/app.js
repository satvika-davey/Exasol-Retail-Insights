// app.js — talks to the FastAPI backend and renders KPIs/charts.

const API_BASE = "http://localhost:8000";

let trendChart, topProductsChart, askChart;

async function fetchJSON(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

async function loadKpis() {
  try {
    const data = await fetchJSON("/kpis");
    document.getElementById("kpi-revenue").textContent =
      data.total_revenue != null ? `$${data.total_revenue.toLocaleString()}` : "—";
    document.getElementById("kpi-orders").textContent =
      data.total_orders != null ? data.total_orders.toLocaleString() : "—";
    document.getElementById("kpi-top-product").textContent = data.top_product || "—";
    document.getElementById("kpi-growth").textContent =
      data.growth_pct != null ? `${data.growth_pct > 0 ? "+" : ""}${data.growth_pct}%` : "—";
  } catch (e) {
    console.error("KPI load failed:", e);
  }
}

async function loadTrend() {
  try {
    const data = await fetchJSON("/trend?metric=revenue&groupby=month");
    const ctx = document.getElementById("trendChart");
    trendChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [{ label: "Revenue", data: data.values, borderColor: "#2f6fed", tension: 0.3, fill: false }],
      },
      options: { responsive: true, plugins: { legend: { display: false } } },
    });
  } catch (e) {
    console.error("Trend load failed:", e);
  }
}

async function loadTopProducts() {
  try {
    const data = await fetchJSON("/top-products?n=5");
    const ctx = document.getElementById("topProductsChart");
    topProductsChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [{ label: "Revenue", data: data.values, backgroundColor: "#2f6fed" }],
      },
      options: { responsive: true, plugins: { legend: { display: false } } },
    });
  } catch (e) {
    console.error("Top products load failed:", e);
  }
}

async function loadRestockAlerts() {
  const container = document.getElementById("restock-list");
  try {
    const data = await fetchJSON("/restock-alerts");
    if (!data.alerts.length) {
      container.textContent = "No restock alerts right now.";
      return;
    }
    container.innerHTML = data.alerts
      .slice(0, 8)
      .map(
        (a) => `
        <div class="restock-item">
          <span>${a.description || a.stock_code}</span>
          <span>+${a.pct_above_avg}% vs avg</span>
        </div>`
      )
      .join("");
  } catch (e) {
    container.textContent = "Couldn't load restock alerts.";
  }
}

async function runBenchmark() {
  const resultEl = document.getElementById("benchmark-result");
  resultEl.textContent = "Running…";
  try {
    const data = await fetchJSON("/benchmark");
    resultEl.textContent =
      `Scanned ${data.rows_scanned.toLocaleString()} rows, ` +
      `${data.unique_customers.toLocaleString()} customers, ` +
      `${data.unique_products.toLocaleString()} products — in ${data.elapsed_ms} ms.`;
  } catch (e) {
    resultEl.textContent = "Benchmark failed — is the backend running?";
  }
}

async function askQuestion(question) {
  const answerEl = document.getElementById("ask-answer");
  const sqlDetails = document.getElementById("sql-details");
  const sqlText = document.getElementById("sql-text");
  const askChartCanvas = document.getElementById("askChart");

  answerEl.textContent = "Thinking…";
  sqlDetails.style.display = "none";
  askChartCanvas.style.display = "none";

  try {
    const data = await fetchJSON("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    answerEl.textContent = data.answer;

    if (data.sql) {
      sqlText.textContent = data.sql;
      sqlDetails.style.display = "block";
    }

    if (data.chartData && data.chartData.labels && data.chartData.labels.length > 1) {
      askChartCanvas.style.display = "block";
      if (askChart) askChart.destroy();
      askChart = new Chart(askChartCanvas, {
        type: "bar",
        data: {
          labels: data.chartData.labels,
          datasets: [{ label: question, data: data.chartData.values, backgroundColor: "#2f6fed" }],
        },
        options: { responsive: true, plugins: { legend: { display: false } } },
      });
    }
  } catch (e) {
    answerEl.textContent = `Sorry, that question hit an error: ${e.message}`;
  }
}

document.getElementById("ask-btn").addEventListener("click", () => {
  const q = document.getElementById("question-input").value.trim();
  if (q) askQuestion(q);
});

document.getElementById("question-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") document.getElementById("ask-btn").click();
});

document.querySelectorAll(".example-q").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.getElementById("question-input").value = btn.textContent;
    askQuestion(btn.textContent);
  });
});

document.getElementById("benchmark-btn").addEventListener("click", runBenchmark);

// Initial load
loadKpis();
loadTrend();
loadTopProducts();
loadRestockAlerts();
