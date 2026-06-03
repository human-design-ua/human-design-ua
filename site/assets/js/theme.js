// Human Design — Theme Engine
// Current themes: dark (default), light
// To add a future theme:
//   1. Add entry to THEMES object below
//   2. Add [data-theme="name"] { ... } CSS block in main.css
//   3. Optionally add it to the cycle in toggleTheme()

var THEME_KEY     = 'hd_theme';
var DEFAULT_THEME = 'dark';

// ── Theme registry ──────────────────────────────────────────
// label: icon shown on toggle button (indicates CURRENT theme)
var THEMES = {
  dark:  { label: '☾', labelNext: '☀', name: 'dark' },
  light: { label: '☀', labelNext: '☾', name: 'light' },
  // === FUTURE THEMES — add here ===
  // cosmic: { label: '✦', labelNext: '☾', name: 'cosmic' },
  // aurora: { label: '◈', labelNext: '☾', name: 'aurora' },
};

var currentTheme = DEFAULT_THEME;

// ── Init — runs immediately to prevent flash of wrong theme ─
function themeInit() {
  var saved       = localStorage.getItem(THEME_KEY);
  var prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;

  if (saved && THEMES[saved]) {
    currentTheme = saved;
  } else if (prefersLight) {
    currentTheme = 'light';
  } else {
    currentTheme = DEFAULT_THEME;
  }

  applyTheme(currentTheme);
}

// ── Apply theme ─────────────────────────────────────────────
function applyTheme(theme) {
  if (!THEMES[theme]) theme = DEFAULT_THEME;
  currentTheme = theme;

  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);

  updateToggleButton(theme);
}

// ── Update toggle button UI ─────────────────────────────────
function updateToggleButton(theme) {
  var btn = document.getElementById('themeToggle');
  if (!btn) return;
  var icon = btn.querySelector('.theme-icon');
  if (icon) icon.textContent = THEMES[theme] ? THEMES[theme].labelNext : '☀';
  var ariaLabel = theme === 'dark' ? 'Увімкнути світлу тему' : 'Увімкнути темну тему';
  btn.setAttribute('aria-label', ariaLabel);
}

// ── Toggle between dark and light ──────────────────────────
function toggleTheme() {
  var next = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  if (typeof trackEvent === 'function') trackEvent('theme_changed', { theme: next });
}

// ── Public API ──────────────────────────────────────────────
window.theme = {
  init:    themeInit,
  apply:   applyTheme,
  toggle:  toggleTheme,
  current: function () { return currentTheme; },
  THEMES:  THEMES,
};

// Run immediately (before DOMContentLoaded) to avoid flash
themeInit();
