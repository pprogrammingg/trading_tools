(function () {
  const DATA_BASE = "data";
  const YEARS = ["2026", "2027", "2028", "2029", "2030"];

  let summary = {};
  let categories = {};
  let currentYear = "2026";

  function getCategory(ticker) {
    return categories[ticker] || "other";
  }

  function groupByCategory(transactions) {
    const byCat = {};
    for (const t of transactions) {
      const cat = getCategory(t.ticker);
      if (!byCat[cat]) byCat[cat] = [];
      byCat[cat].push(t);
    }
    for (const cat of Object.keys(byCat)) {
      byCat[cat].sort((a, b) => a.date.localeCompare(b.date));
    }
    return byCat;
  }

  function renderTabs() {
    const container = document.querySelector(".tabs");
    container.innerHTML = "";
    for (const year of YEARS) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.role = "tab";
      btn.setAttribute("aria-selected", year === currentYear);
      btn.textContent = year;
      btn.addEventListener("click", () => selectYear(year));
      container.appendChild(btn);
    }
  }

  function renderSummary() {
    const s = summary[currentYear];
    if (!s) {
      document.querySelector(".pnl-section").innerHTML = "<h3>PnL</h3><p>No data</p>";
      document.querySelector(".tax-section").innerHTML = "<h3>Tax (excl. TFSA)</h3><p>No data</p>";
      return;
    }
    const pnlEl = document.querySelector(".pnl-section");
    const overall = s.overall_pnl;
    const pnlClass = overall >= 0 ? "positive" : "negative";
    let byCat = "";
    for (const [cat, val] of Object.entries(s.pnl_by_category || {})) {
      byCat += `${cat}: ${val >= 0 ? "" : ""}${Number(val).toLocaleString("en", { minimumFractionDigits: 2 })}<br>`;
    }
    pnlEl.innerHTML =
      "<h3>PnL</h3>" +
      `<div class=\"overall ${pnlClass}\">${Number(overall).toLocaleString("en", { minimumFractionDigits: 2 })}</div>` +
      (byCat ? `<div class=\"by-category\">${byCat}</div>` : "");

    const taxEl = document.querySelector(".tax-section");
    taxEl.innerHTML =
      "<h3>Tax (excl. TFSA)</h3>" +
      "<div class=\"by-method\">" +
      `FIFO: ${Number(s.tax_fifo).toLocaleString("en", { minimumFractionDigits: 2 })}<br>` +
      `LIFO: ${Number(s.tax_lifo).toLocaleString("en", { minimumFractionDigits: 2 })}<br>` +
      `Avg cost: ${Number(s.tax_average_cost).toLocaleString("en", { minimumFractionDigits: 2 })}` +
      "</div>";
  }

  function renderTransactions() {
    const container = document.querySelector(".transactions-by-category");
    container.innerHTML = "";
    fetch(`${DATA_BASE}/${currentYear}.json`)
      .then((r) => (r.ok ? r.json() : []))
      .then((txList) => {
        if (!Array.isArray(txList) || txList.length === 0) {
          container.innerHTML = "<p class=\"muted\">No transactions for this year.</p>";
          return;
        }
        const byCat = groupByCategory(txList);
        const order = Object.keys(byCat).sort();
        for (const cat of order) {
          const block = document.createElement("div");
          block.className = "category-block";
          block.innerHTML = `<h4>${cat}</h4>`;
          const table = document.createElement("table");
          table.className = "transaction-table";
          table.innerHTML =
            "<thead><tr>" +
            "<th>Date</th><th>Account</th><th>Ticker</th><th>Action</th>" +
            "<th class=\"num\">Qty</th><th class=\"num\">Price</th><th class=\"num\">Fees</th>" +
            "</tr></thead><tbody></tbody>";
          const tbody = table.querySelector("tbody");
          for (const t of byCat[cat]) {
            const action = (t.action || "").toLowerCase();
            const row = document.createElement("tr");
            row.innerHTML =
              `<td>${t.date}</td>` +
              `<td>${escapeHtml(t.account_name || "")}</td>` +
              `<td>${escapeHtml(t.ticker)}</td>` +
              `<td class="${action}">${action}</td>` +
              `<td class="num">${Number(t.quantity)}</td>` +
              `<td class="num">${Number(t.price)}</td>` +
              `<td class="num">${Number(t.fees || 0)}</td>`;
            tbody.appendChild(row);
          }
          block.appendChild(table);
          container.appendChild(block);
        }
      })
      .catch(() => {
        container.innerHTML = "<p class=\"muted\">No transactions for this year.</p>";
      });
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function selectYear(year) {
    currentYear = year;
    document.querySelectorAll(".tabs button").forEach((btn, i) => {
      btn.setAttribute("aria-selected", YEARS[i] === year);
    });
    renderSummary();
    renderTransactions();
  }

  function init() {
    Promise.all([
      fetch(`${DATA_BASE}/summary.json`).then((r) => r.json()),
      fetch(`${DATA_BASE}/ticker_categories.json`).then((r) => r.json()),
    ])
      .then(([s, c]) => {
        summary = s || {};
        categories = c || {};
        renderTabs();
        renderSummary();
        renderTransactions();
      })
      .catch((e) => {
        document.querySelector("main").innerHTML =
          "<p>Load data first: run <code>python3 transactions/scripts/generate_summary.py</code> from the repo root, then open this page (or serve transactions/ui/ with a local server).</p>";
        console.error(e);
      });
  }

  init();
})();
