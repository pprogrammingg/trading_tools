(function () {
  const JSON_FILE = "deposite_cad_usd_2023_2025.json";

  const fmtMoney = (n, currency) =>
    new Intl.NumberFormat("en-CA", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(n);

  const fmtDate = (iso) => {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("en-CA", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  function aggregateByDate(transactions) {
    const map = new Map();
    for (const t of transactions) {
      const usd = Number(t.usd_equivalent ?? t.usd_credited ?? 0);
      const cad = Number(t.cad_credited ?? 0);
      const cur = map.get(t.date) || { usd: 0, cad: 0 };
      cur.usd += usd;
      cur.cad += cad;
      map.set(t.date, cur);
    }
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }

  function renderSums(root, data) {
    const { sums, summary } = data;
    root.innerHTML = `
      <div class="sum-card cad">
        <div class="label">Total CAD credited</div>
        <div class="value">${fmtMoney(sums.cad, "CAD")}</div>
      </div>
      <div class="sum-card usd">
        <div class="label">Total USD (equiv. + USD deposit)</div>
        <div class="value">${fmtMoney(sums.usd, "USD")}</div>
      </div>
      <div class="sum-card meta">
        <div class="label">Completed deposits</div>
        <div class="value">${summary.total_completed_rows}</div>
      </div>
      <p class="sum-note">${sums.note}</p>
    `;
  }

  function renderChart(container, transactions) {
    const rows = aggregateByDate(transactions);
    const maxCad = Math.max(...rows.map(([, v]) => v.cad), 1);
    const maxUsd = Math.max(...rows.map(([, v]) => v.usd), 1);
    const h = 200;

    container.innerHTML = rows
      .map(([date, v]) => {
        const hCad = v.cad > 0 ? Math.max((v.cad / maxCad) * h, 3) : 0;
        const hUsd = v.usd > 0 ? Math.max((v.usd / maxUsd) * h, 3) : 0;
        const title = `${date}\nCAD ${v.cad.toFixed(2)}\nUSD ${v.usd.toFixed(2)}`;
        return `
          <div class="chart-col" title="${title.replace(/\n/g, " — ")}">
            <div class="bars">
              <div class="bar cad" style="height:${hCad}px" title="CAD ${fmtMoney(v.cad, "CAD")}"></div>
              <div class="bar usd" style="height:${hUsd}px" title="USD ${fmtMoney(v.usd, "USD")}"></div>
            </div>
            <div class="col-label">${fmtDate(date)}</div>
          </div>
        `;
      })
      .join("");
  }

  function renderTable(tbody, transactions) {
    const sorted = [...transactions].sort((a, b) => b.date.localeCompare(a.date));
    tbody.innerHTML = sorted
      .map((t) => {
        const usd = t.usd_equivalent ?? t.usd_credited ?? null;
        const cad = t.cad_credited;
        const type = t.deposit_currency === "USD" ? "USD" : "CAD";
        return `
        <tr>
          <td>${fmtDate(t.date)}</td>
          <td><span class="badge ${type.toLowerCase()}">${type}</span></td>
          <td class="num">${usd != null ? fmtMoney(usd, "USD") : "—"}</td>
          <td class="num">${cad != null ? fmtMoney(cad, "CAD") : "—"}</td>
        </tr>`;
      })
      .join("");
  }

  function loadEmbedded() {
    const el = document.getElementById("deposit-data");
    const raw = el?.textContent?.trim();
    if (!raw) return null;
    return JSON.parse(raw);
  }

  async function loadData() {
    if (location.protocol === "file:") {
      const data = loadEmbedded();
      if (!data) throw new Error("No embedded data");
      return data;
    }
    try {
      const res = await fetch(JSON_FILE);
      if (res.ok) return res.json();
    } catch (_) {
      /* network / CORS */
    }
    const data = loadEmbedded();
    if (!data) throw new Error("No embedded data");
    return data;
  }

  async function load() {
    const titleEl = document.getElementById("title");
    const sumsEl = document.getElementById("sums");
    const chartEl = document.getElementById("chart");
    const tbody = document.querySelector("#txn-table tbody");
    const errEl = document.getElementById("error");

    try {
      const data = await loadData();

      errEl.hidden = true;
      titleEl.textContent = data.document_title || "Deposits";
      renderSums(sumsEl, data);
      renderChart(chartEl, data.transactions);
      renderTable(tbody, data.transactions);
    } catch (e) {
      errEl.hidden = false;
      errEl.innerHTML =
        "<strong>Could not load data.</strong> Ensure <code>deposite_cad_usd_2023_2025.json</code> is beside this HTML or the embedded <code>#deposit-data</code> block is valid JSON.";
      console.error(e);
    }
  }

  load();
})();
