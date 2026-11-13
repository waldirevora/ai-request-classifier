import { useEffect, useState } from "react";
export const THEME_KEY = "arc-theme";
export function useTheme() {
  const [mode, setMode] = useState(
    () => document.documentElement.dataset.themeChoice || "dark",
  );
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      const resolved =
        mode === "auto" ? (media.matches ? "dark" : "light") : mode;
      document.documentElement.dataset.theme = resolved;
      document.documentElement.dataset.themeChoice = mode;
      document.documentElement.style.colorScheme = resolved;
      document
        .querySelector('meta[name="theme-color"]')
        ?.setAttribute("content", resolved === "dark" ? "#0b1422" : "#f3f6fa");
    };
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [mode]);
  const choose = (next) => {
    if (!["auto", "light", "dark"].includes(next)) return;
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* Preferência funciona nesta sessão mesmo sem armazenamento. */
    }
    setMode(next);
  };
  return [mode, choose];
}
