// Executado antes do React e dos estilos para evitar flash do tema incorreto.
(function () {
  var mode = "dark";
  try {
    var saved = localStorage.getItem("arc-theme");
    if (["auto", "light", "dark"].indexOf(saved) !== -1) mode = saved;
  } catch (_) {
    /* Armazenamento indisponível: usar o padrão escuro. */
  }
  var dark =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  var theme = mode === "auto" ? (dark ? "dark" : "light") : mode;
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.themeChoice = mode;
  document.documentElement.style.colorScheme = theme;
  document
    .querySelector('meta[name="theme-color"]')
    .setAttribute("content", theme === "dark" ? "#0b1422" : "#f3f6fa");
})();
