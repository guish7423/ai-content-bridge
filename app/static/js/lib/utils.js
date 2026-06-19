/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — Utilities v1.0
   ═══════════════════════════════════════════════════════════════════════════ */

function debounce(fn, delay) {
  var timer;
  return function() {
    var context = this;
    var args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function() { fn.apply(context, args); }, delay);
  };
}

function formatChars(text) {
  var chinese = text.match(/[\u4e00-\u9fff]/g) || [];
  var english = text.match(/[a-zA-Z0-9]/g) || [];
  return chinese.length + english.length;
}

function estimateCost(text) {
  var chars = formatChars(text);
  var tokens = Math.ceil(chars * 1.5);
  return (tokens * 0.07 / 1e6).toFixed(4);
}

function copyToClipboard(text, successMsg) {
  navigator.clipboard.writeText(text).then(function() {
    showToast(successMsg || 'Copied!', 'success');
  }).catch(function() {
    showToast('Failed to copy', 'error');
  });
}

function escapeHtml(text) {
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
