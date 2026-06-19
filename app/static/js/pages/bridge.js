/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — Bridge Tool Interactions v1.0
   ═══════════════════════════════════════════════════════════════════════════ */

/* ── Sample presets ────────────────────────────────────────────────────── */
var SAMPLES = [
  "",
  "我们是一家AI驱动的跨境电商营销公司，帮助中国卖家在Shopify和Amazon上提升转化率。我们的AI系统能自动分析产品卖点，生成多语言的产品描述和广告文案。使用我们服务的卖家平均转化率提升30%，客单价提升15%。目前已经有超过2000家商户在使用我们的平台。",
  "做独立开发三年，最大的感悟是：不要等产品完美了再发布。我的第一个产品做了6个月，上线后无人问津。第二个产品只花了2周做MVP，发布当天就有3个付费用户。",
  "我们公司专注于为企业提供AI驱动的数字化转型解决方案。成立于2020年，总部位于深圳，团队规模50人，服务客户涵盖金融、医疗、制造等行业。",
];

function setSample(n) {
  var textarea = document.getElementById('text');
  if (!textarea) return;
  textarea.value = SAMPLES[n];
  updateBridgeUI();
  var results = document.getElementById('results');
  if (results) results.innerHTML = '';
}

/* ── Platform toggle ───────────────────────────────────────────────────── */
function togglePlatform(btn) {
  btn.classList.toggle('active');
  btn.classList.toggle('ks-button--ghost');
  btn.classList.toggle('ks-button--secondary');
  var selected = [];
  document.querySelectorAll('.platform-btn.active').forEach(function(b) {
    selected.push(b.dataset.value);
  });
  var input = document.getElementById('platforms-input');
  if (input) input.value = JSON.stringify(selected.length ? selected : ['x']);
}

/* ── Character count + cost estimate ──────────────────────────────────── */
function updateBridgeUI() {
  var textarea = document.getElementById('text');
  var countEl = document.getElementById('char-count');
  var costEl = document.getElementById('cost-estimate');
  if (!textarea || !countEl || !costEl) return;

  var text = textarea.value;
  var chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  var englishChars = (text.match(/[a-zA-Z0-9]/g) || []).length;
  var total = chineseChars + englishChars;
  var estimatedTokens = Math.ceil(total * 1.5);
  var cost = (estimatedTokens * 0.07 / 1e6).toFixed(4);

  countEl.textContent = total + ' chars';
  costEl.textContent = '~$' + cost;
}

/* ── FAQ toggle ────────────────────────────────────────────────────────── */
function toggleFaq(btn) {
  var answer = btn.nextElementSibling;
  if (!answer) return;
  var isOpen = answer.style.display === 'block';
  answer.style.display = isOpen ? 'none' : 'block';
}

/* ── Mobile nav ────────────────────────────────────────────────────────── */
function toggleMobile() {
  var nav = document.getElementById('mobile-nav');
  var ham = document.querySelector('.hamburger');
  if (!nav) return;
  nav.classList.toggle('open');
  if (ham) ham.classList.toggle('active');
  document.body.style.overflow = nav.classList.contains('open') ? 'hidden' : '';
}

function closeMobile() {
  var nav = document.getElementById('mobile-nav');
  var ham = document.querySelector('.hamburger');
  if (nav) nav.classList.remove('open');
  if (ham) ham.classList.remove('active');
  document.body.style.overflow = '';
}

/* ── HTMX handlers ────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function() {
  var textarea = document.getElementById('text');
  if (textarea) {
    textarea.addEventListener('input', debounce(updateBridgeUI, 100));
  }

  var form = document.getElementById('bridge-form');
  if (form) {
    form.addEventListener('htmx:configRequest', function(evt) {
      try {
        var raw = document.getElementById('platforms-input').value;
        evt.detail.parameters['platforms'] = JSON.parse(raw);
      } catch(e) {
        evt.detail.parameters['platforms'] = ['x'];
      }
    });

    form.addEventListener('htmx:afterSwap', function(evt) {
      if (evt.detail.target && evt.detail.target.id === 'results') {
        var btn = document.getElementById('submit-btn');
        if (btn) {
          var span = btn.querySelector('span');
          if (span) span.textContent = '✦ Bridge Again';
        }
        evt.detail.target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });

    form.addEventListener('htmx:responseError', function(evt) {
      var resultsDiv = document.getElementById('results');
      if (resultsDiv) {
        resultsDiv.innerHTML = '<div class="ks-empty"><span class="ks-empty__icon">❌</span><h3 class="ks-empty__title">Error</h3><p class="ks-empty__text">' +
          (evt.detail.xhr.responseText || 'Request failed. Please try again.') +
          '</p></div>';
      }
    });
  }
});
