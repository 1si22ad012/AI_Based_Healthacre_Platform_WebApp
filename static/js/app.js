function showToast(message, type) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.style.background = type === "error" ? "#991b1b" : "#111827";
  toast.style.display = "block";
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => { toast.style.display = "none"; }, 3500);
}

(function initWebSocket() {
  const statusEl = document.getElementById("ws-status");
  if (!statusEl) return;
  let socket = null;
  let reconnectTimer = null;
  function connect() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${protocol}://${window.location.host}/ws/security/`);
    socket.onopen = function () {
      statusEl.textContent = "connected";
      statusEl.style.color = "#16a34a";
    };
    socket.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "notification") {
          showToast(data.payload.title || "New notification", "info");
        }
        if (data.type === "security_event" || data.type === "anomaly_alert") {
          showToast("Security alert received", "warning");
        }
      } catch (e) {}
    };
    socket.onclose = function () {
      statusEl.textContent = "disconnected";
      statusEl.style.color = "#dc2626";
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => { reconnectTimer = null; connect(); }, 3000);
      }
    };
    socket.onerror = function () { socket.close(); };
  }
  connect();
})();
