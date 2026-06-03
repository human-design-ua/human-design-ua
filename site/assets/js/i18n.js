// Human Design — i18n Engine
// Supported languages: uk (Ukrainian), ru (Russian), en (English)
// HTML usage:
//   data-i18n="key"             → replaces textContent
//   data-i18n-html="key"        → replaces innerHTML (safe: translations are hardcoded)
//   data-i18n-placeholder="key" → replaces placeholder attribute
//   data-i18n-aria="key"        → replaces aria-label attribute
//   data-i18n-template="key" data-i18n-var-n="1" data-i18n-var-total="9"
//                               → interpolates {{n}} and {{total}} in text

var I18N_KEY        = 'hd_lang';
var SUPPORTED_LANGS = ['uk', 'ru', 'en'];
var DEFAULT_LANG    = 'uk';
var currentLang     = DEFAULT_LANG;

// ── Init ───────────────────────────────────────────────────
function i18nInit() {
  var saved      = localStorage.getItem(I18N_KEY);
  var browserLang = (navigator.language || navigator.userLanguage || '').slice(0, 2);

  if (saved && SUPPORTED_LANGS.indexOf(saved) !== -1) {
    currentLang = saved;
  } else if (browserLang === 'ru') {
    currentLang = 'ru';
  } else if (browserLang === 'en') {
    currentLang = 'en';
  } else {
    currentLang = DEFAULT_LANG;
  }

  applyLang(currentLang);
}

// ── Apply translations ──────────────────────────────────────
function applyLang(lang) {
  if (SUPPORTED_LANGS.indexOf(lang) === -1) lang = DEFAULT_LANG;
  currentLang = lang;

  var t = (typeof HD_TRANSLATIONS !== 'undefined' && HD_TRANSLATIONS[lang]) ? HD_TRANSLATIONS[lang] : {};

  document.documentElement.lang = lang;
  localStorage.setItem(I18N_KEY, lang);

  // Text content
  document.querySelectorAll('[data-i18n]').forEach(function (el) {
    var key = el.dataset.i18n;
    if (t[key] !== undefined) el.textContent = t[key];
  });

  // innerHTML — safe because translations are our own hardcoded JS
  document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
    var key = el.dataset.i18nHtml;
    if (t[key] !== undefined) el.innerHTML = t[key];
  });

  // Placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
    var key = el.dataset.i18nPlaceholder;
    if (t[key] !== undefined) el.placeholder = t[key];
  });

  // aria-label
  document.querySelectorAll('[data-i18n-aria]').forEach(function (el) {
    var key = el.dataset.i18nAria;
    if (t[key] !== undefined) el.setAttribute('aria-label', t[key]);
  });

  // Templates with {{var}} interpolation
  document.querySelectorAll('[data-i18n-template]').forEach(function (el) {
    var key  = el.dataset.i18nTemplate;
    var text = t[key];
    if (text === undefined) return;
    Object.keys(el.dataset).forEach(function (k) {
      if (k.indexOf('i18nVar') === 0) {
        var varName = k.replace('i18nVar', '').toLowerCase();
        text = text.split('{{' + varName + '}}').join(el.dataset[k]);
      }
    });
    el.textContent = text;
  });

  syncLangButtons(lang);
}

// ── Translate helper (use in JS code) ──────────────────────
function t(key, vars) {
  var translations = (typeof HD_TRANSLATIONS !== 'undefined' && HD_TRANSLATIONS[currentLang])
    ? HD_TRANSLATIONS[currentLang] : {};
  var text = translations[key] !== undefined ? translations[key] : key;
  if (vars) {
    Object.keys(vars).forEach(function (k) {
      text = text.split('{{' + k + '}}').join(vars[k]);
    });
  }
  return text;
}

// ── Sync active button state ────────────────────────────────
function syncLangButtons(lang) {
  document.querySelectorAll('.lang-btn').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
}

// ── Public API ─────────────────────────────────────────────
function switchLang(lang) {
  applyLang(lang);
  if (typeof trackEvent === 'function') trackEvent('language_changed', { lang: lang });
}

window.i18n = {
  init:    i18nInit,
  t:       t,
  switch:  switchLang,
  current: function () { return currentLang; },
  apply:   applyLang,
};
window.t = t;

// Auto-init on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', i18nInit);
} else {
  i18nInit();
}
