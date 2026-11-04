const OWNER = "mornavapon", REPO = "earnings-alert", BRANCH = "main", PATH = "config/watchlist.json";
const $ = id => document.getElementById(id);
let watchlist = [];
let earnings = {};
let dirty = false;
let sortMode = "date"; // date = upcoming first, ticker = A-Z
const tokenKey = "earnings_alert_github_token";

function token() { return $("token").value.trim() || localStorage.getItem(tokenKey) || ""; }
function setStatus(msg, ok = false) {
  $("connection").textContent = msg;
  $("connection").style.color = ok ? "#3fb950" : "#d29922";
  $("connection").style.borderColor = ok ? "#238636" : "#6e5700";
}
function render() {
  $("count").textContent = watchlist.length;
  const container = $("stocks");
  container.innerHTML = "";
  if (!watchlist.length) {
    container.innerHTML = '<p class="muted small">ยังไม่มีหุ้นใน Watchlist — เพิ่ม Ticker ด้านบนได้เลย</p>';
  }
  const sortedWatchlist = [...watchlist].sort((a, b) => {
    if (sortMode === "ticker") return a.localeCompare(b);
    const dateA = earnings[a]?.date || "";
    const dateB = earnings[b]?.date || "";
    if (dateA && dateB) return dateA.localeCompare(dateB) || a.localeCompare(b);
    if (dateA) return -1;
    if (dateB) return 1;
    return a.localeCompare(b);
  });
  watchlist.forEach; // keep saved watchlist unchanged
  sortedWatchlist.forEach(ticker => {
    const row = document.createElement("div");
    row.className = "stock";
    const details = document.createElement("div");
    details.className = "stock-details";
    const name = document.createElement("span");
    name.className = "symbol";
    name.textContent = ticker;
    const info = earnings[ticker] || { status: "pending", message: "รอข้อมูลวันประกาศงบจากระบบ" };
    const status = document.createElement("span");
    status.className = "earnings-status " + (info.status || "pending");
    if (info.status === "scheduled" && info.date) {
      status.textContent = `📅 หุ้น ${ticker} จะประกาศงบวันที่ ${formatDate(info.date)}`;
    } else if (info.status === "no_date") {
      status.textContent = `⏳ หุ้น ${ticker}: ยังไม่มีข้อมูลกำหนดวันประกาศจาก Yahoo`;
    } else if (info.status === "error") {
      status.textContent = `⚠️ หุ้น ${ticker}: ดึงข้อมูลไม่สำเร็จ`;
    } else {
      status.textContent = info.message || "รอข้อมูลวันประกาศงบจากระบบ";
    }
    details.append(name, status);

    const previous = document.createElement("span");
    previous.className = "previous-earnings";
    previous.textContent = info.previous_date
      ? `ไตรมาสก่อน ประกาศวันที่ ${formatDate(info.previous_date)}`
      : "ไตรมาสก่อน: ยังไม่มีข้อมูล";

    const del = document.createElement("button");
    del.className = "remove";
    del.textContent = "ลบ";
    del.onclick = () => { watchlist = watchlist.filter(x => x !== ticker); changed(); };
    row.append(details, previous, del);
    container.append(row);
  });
  $("save").disabled = !dirty || !token();
  $("dirty-note").textContent = dirty ? "มีรายการที่แก้ไขแล้วยังไม่ได้บันทึกลง GitHub" : "รายการตรงกับข้อมูลที่บันทึกไว้ใน GitHub";
  $("dirty-note").className = dirty ? "save-warning small" : "muted small";
}
$("sort-mode").onchange = event => {
  sortMode = event.target.value;
  render();
};
function formatDate(iso) {
  const [year, month, day] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("th-TH", { day: "numeric", month: "short", year: "numeric" })
    .format(new Date(year, month - 1, day));
}
function changed() {
  dirty = true;
  $("save-status").textContent = "ยังไม่ได้บันทึก — กดปุ่มบันทึกเพื่อเก็บรายการถาวร";
  render();
}
async function api(path, opts = {}) {
  const response = await fetch("https://api.github.com" + path, {
    ...opts,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: "Bearer " + token(),
      "X-GitHub-Api-Version": "2022-11-28",
      ...(opts.headers || {})
    }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw Error(data.message || ("GitHub API error " + response.status));
  return data;
}
async function loadEarnings() {
  try {
    const response = await fetch(`data/earnings.json?ts=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw Error("ยังไม่มีไฟล์ข้อมูลรอบล่าสุด");
    const data = await response.json();
    earnings = data.tickers || {};
    $("earnings-updated").textContent = data.updated_at
      ? `อัปเดตข้อมูลล่าสุด: ${new Date(data.updated_at).toLocaleString("th-TH", { timeZone: "Asia/Bangkok" })} · แหล่งข้อมูล Yahoo Finance`
      : "ยังไม่มีข้อมูลวันประกาศงบ";
  } catch (error) {
    earnings = {};
    $("earnings-updated").textContent = "ยังไม่มีข้อมูลวันประกาศงบ — รอ GitHub Actions ทำงานรอบแรก";
  }
  render();
}
async function loadWatchlist() {
  try {
    const data = await api(`/repos/${OWNER}/${REPO}/contents/${PATH}?ref=${BRANCH}`);
    const raw = atob(data.content.replace(/\n/g, ""));
    watchlist = JSON.parse(decodeURIComponent(escape(raw))).tickers || [];
    watchlist = [...new Set(watchlist.map(x => String(x).toUpperCase().trim()).filter(Boolean))].sort();
    dirty = false;
    setStatus("เชื่อมต่อ GitHub แล้ว", true);
    $("save-status").textContent = "โหลด Watchlist จาก GitHub แล้ว";
    render();
  } catch (error) {
    setStatus("เชื่อมต่อไม่สำเร็จ");
    $("save-status").textContent = error.message;
    render();
  }
}
$("add-form").onsubmit = event => {
  event.preventDefault();
  const ticker = $("ticker").value.trim().toUpperCase().replace(/^\$/, "");
  if (!/^[A-Z0-9.^=-]{1,15}$/.test(ticker)) { alert("Ticker ไม่ถูกต้อง"); return; }
  if (watchlist.includes(ticker)) { alert("มีหุ้นตัวนี้ในรายการแล้ว"); return; }
  watchlist.push(ticker);
  watchlist.sort();
  $("ticker").value = "";
  changed();
};
$("connect").onclick = async () => {
  const value = $("token").value.trim();
  if (!value) { alert("กรุณาใส่ GitHub Token"); return; }
  localStorage.setItem(tokenKey, value);
  try {
    const user = await api("/user");
    if (user.login !== OWNER) throw Error("Token นี้เป็นของบัญชี " + user.login + " ไม่ใช่ " + OWNER);
    await loadWatchlist();
  } catch (error) {
    setStatus("ตรวจสอบไม่ผ่าน");
    $("save-status").textContent = error.message;
  }
};
$("reload").onclick = async () => {
  if (dirty && !confirm("มีการแก้ไขที่ยังไม่บันทึก ต้องการโหลดทับและยกเลิกการแก้ไขหรือไม่?")) return;
  await loadWatchlist();
  await loadEarnings();
};
$("save").onclick = async () => {
  try {
    $("save").disabled = true;
    $("save-status").textContent = "กำลังบันทึก...";
    let old = null;
    try { old = await api(`/repos/${OWNER}/${REPO}/contents/${PATH}?ref=${BRANCH}`); } catch (error) { /* file may not exist */ }
    const content = btoa(unescape(encodeURIComponent(JSON.stringify({ tickers: watchlist, updated_at: new Date().toISOString() }, null, 2) + "\n")));
    const body = { message: "Update earnings watchlist", content, branch: BRANCH };
    if (old?.sha) body.sha = old.sha;
    await api(`/repos/${OWNER}/${REPO}/contents/${PATH}`, { method: "PUT", body: JSON.stringify(body) });
    dirty = false;
    $("save-status").textContent = "บันทึกสำเร็จ — GitHub Actions จะใช้รายการนี้ในการตรวจสอบรอบถัดไป";
    setStatus("บันทึกแล้ว", true);
    render();
  } catch (error) {
    $("save-status").textContent = "บันทึกไม่สำเร็จ: " + error.message;
    $("save").disabled = false;
  }
};
$("forget").onclick = () => {
  localStorage.removeItem(tokenKey);
  $("token").value = "";
  setStatus("ล้าง Token แล้ว");
  render();
};

const savedToken = localStorage.getItem(tokenKey);
if (savedToken) {
  $("token").value = savedToken;
  loadWatchlist();
} else {
  watchlist = [];
  render();
  $("stocks").innerHTML = '<p class="muted small">ใส่ GitHub Token เพื่อโหลด Watchlist ที่เก็บใน Repository</p>';
}
loadEarnings();
