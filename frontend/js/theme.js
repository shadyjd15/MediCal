(function() {
  try {
    var saved = localStorage.getItem("mt_theme");
    if (!saved) {
      saved = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    document.documentElement.setAttribute("data-theme", saved);
  } catch (e) { /* ignore */ }
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("mt_theme", next);
  const btn = document.getElementById("themeToggleLabel");
  if (btn) btn.textContent = next === "dark" ? "Light mode" : "Dark mode";
  if (typeof Api !== "undefined" && Auth && Auth.getToken && Auth.getToken()) {
    Api.updateMyTheme(next).catch(() => { /* non-fatal */ });
  }
}
