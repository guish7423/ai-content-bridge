/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — Theme Toggle v1.0
   ═══════════════════════════════════════════════════════════════════════════ */

(function initTheme() {
  var saved = localStorage.getItem('cw-theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  }

  // 始终默认中文（目标用户是中国创业者）
  currentLang = localStorage.getItem('cw-lang') || 'zh';
  applyLang(currentLang);
})();

function toggleTheme() {
  var html = document.documentElement;
  var current = html.getAttribute('data-theme') || 'dark';
  var next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('cw-theme', next);
  document.querySelectorAll('.theme-toggle').forEach(function(btn) {
    btn.textContent = next === 'light' ? '☀️' : '🌙';
  });
}

/* ── Language toggle ────────────────────────────────────────────────────── */

function applyLang(lang) {
  currentLang = lang;
  localStorage.setItem('cw-lang', lang);
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.getAttribute('data-i18n');
    if (window.I18N && window.I18N[lang] && window.I18N[lang][key]) {
      el.textContent = window.I18N[lang][key];
    }
  });
  document.documentElement.lang = lang;
}

function toggleLang() {
  applyLang(currentLang === 'en' ? 'zh' : 'en');
}

document.addEventListener('DOMContentLoaded', function() {
  applyLang(currentLang);
});
