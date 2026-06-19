/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — Toast Notification System v1.0
   ═══════════════════════════════════════════════════════════════════════════ */

var toastQueue = [];
var isShowing = false;

function showToast(message, type, duration) {
  type = type || 'info';
  duration = duration || (type === 'error' ? 5000 : 2500);

  var container = document.getElementById('toast-container');
  if (!container) return;

  var toast = document.createElement('div');
  toast.className = 'ks-toast ks-toast--' + type;
  toast.innerHTML = '<span>' + message + '</span><button class="ks-toast-close" onclick="this.parentElement.remove()">×</button>';
  container.appendChild(toast);

  setTimeout(function() {
    if (toast.parentElement) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(function() { if (toast.parentElement) toast.remove(); }, 300);
    }
  }, duration);
}

/* ── Auto-toast from HTMX events ───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function() {
  document.body.addEventListener('htmx:responseError', function(evt) {
    var status = evt.detail.xhr.status;
    if (status === 429) {
      showToast('Monthly limit reached. Upgrade to continue.', 'error', 5000);
    } else if (status === 402) {
      showToast('Payment required. Please upgrade your plan.', 'error', 5000);
    } else if (status >= 500) {
      showToast('Server error. Please try again.', 'error');
    }
  });

  document.body.addEventListener('htmx:beforeRequest', function() {
    var btn = document.getElementById('submit-btn');
    if (btn) btn.classList.add('loading');
  });

  document.body.addEventListener('htmx:afterRequest', function() {
    var btn = document.getElementById('submit-btn');
    if (btn) btn.classList.remove('loading');
  });
});
