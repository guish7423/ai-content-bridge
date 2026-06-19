/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — Bridge Tool Interactions v1.0
   ═══════════════════════════════════════════════════════════════════════════ */

/* ── Batch Translation ──────────────────────────────────────────────── */
function toggleBatch() {
  var el = document.getElementById('batch-mode');
  var btn = document.getElementById('batch-toggle');
  if (el.style.display === 'none') {
    el.style.display = 'block';
    btn.textContent = '收起批量翻译';
  } else {
    el.style.display = 'none';
    btn.textContent = '批量翻译';
  }
}

function doBatch() {
  var textarea = document.getElementById('batch-text');
  var btn = document.getElementById('batch-btn');
  var results = document.getElementById('batch-results');
  var texts = textarea.value.split('\n').filter(function(t){return t.trim()});
  if (!texts.length) { showToast('请输入内容', 'error'); return; }
  if (texts.length > 50) { showToast('最多 50 条', 'error'); return; }
  
  btn.disabled = true;
  btn.innerHTML = '<span class="ks-spinner"></span> 翻译中...';
  results.style.display = 'block';
  results.innerHTML = '<p style="font-size:var(--cw-text-sm);color:var(--cw-text-secondary)">处理中，请稍候...</p>';
  
  fetch('/batch', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({texts: texts, platform: 'x'})
  }).then(function(r){return r.json()}).then(function(d){
    results.innerHTML = '<div style="font-size:var(--cw-text-xs);color:var(--cw-text-tertiary);margin-bottom:var(--cw-space-sm)">共 ' + d.total + ' 条</div>' +
      d.results.map(function(item, i){
        return '<div style="padding:var(--cw-space-sm);border-bottom:1px solid var(--cw-border);font-size:var(--cw-text-sm)">' +
          '<div style="color:var(--cw-text-tertiary);margin-bottom:2px">#' + (i+1) + ' ' + item.original.slice(0,60) + '</div>' +
          '<div style="color:var(--cw-text-secondary)">' + (item.content || '<span style="color:var(--cw-red)">' + item.error + '</span>') + '</div></div>';
      }).join('');
    btn.disabled = false;
    btn.innerHTML = '<i class="ph ph-lightning"></i> 批量翻译';
  }).catch(function(){
    results.innerHTML = '<p style="color:var(--cw-red);font-size:var(--cw-text-sm)">请求失败</p>';
    btn.disabled = false;
    btn.innerHTML = '<i class="ph ph-lightning"></i> 批量翻译';
  });
}

/* ── Content Ideas Generator ────────────────────────────────────────── */
function toggleIdeas() {
  var el = document.getElementById('ideas-mode');
  var btn = document.getElementById('ideas-toggle');
  if (el.style.display === 'none') {
    el.style.display = 'block';
    btn.textContent = '收起创意生成';
  } else {
    el.style.display = 'none';
    btn.textContent = '内容创意生成';
  }
}

function doIdeas() {
  var desc = document.getElementById('ideas-desc');
  var platform = document.getElementById('ideas-platform');
  var btn = document.getElementById('ideas-btn');
  var results = document.getElementById('ideas-results');
  
  if (!desc.value.trim()) { showToast('请输入产品描述', 'error'); return; }
  
  btn.disabled = true;
  btn.innerHTML = '<span class="ks-spinner"></span> 生成中...';
  results.style.display = 'block';
  results.innerHTML = '<p style="font-size:var(--cw-text-sm);color:var(--cw-text-secondary)">生成创意中...</p>';
  
  fetch('/ideas', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({description: desc.value, platform: platform.value})
  }).then(function(r){return r.json()}).then(function(d){
    var ideas = typeof d.ideas === 'string' ? [{title: d.ideas}] : (d.ideas || []);
    results.innerHTML = ideas.map(function(item, i){
      return '<div style="padding:var(--cw-space-md);border-bottom:1px solid var(--cw-border)">' +
        '<div style="font-weight:600;font-size:var(--cw-text-sm);margin-bottom:4px">💡 创意 ' + (i+1) + '</div>' +
        '<div style="font-size:var(--cw-text-sm);color:var(--cw-text-secondary)">' + (item.title || item.hook || '') + '</div></div>';
    }).join('');
    btn.disabled = false;
    btn.innerHTML = '<i class="ph ph-magic-wand"></i> 生成 5 个帖子创意';
  }).catch(function(){
    results.innerHTML = '<p style="color:var(--cw-red)">生成失败</p>';
    btn.disabled = false;
    btn.innerHTML = '<i class="ph ph-magic-wand"></i> 生成 5 个帖子创意';
  });
}

/* ── Live Preview (实时预览) ──────────────────────────────────────────── */
var previewController = null;
var previewTimer = null;

function updateLivePreview(text) {
  var previewEl = document.getElementById('live-preview');
  var contentEl = document.getElementById('preview-content');
  var statusEl = document.getElementById('preview-status');
  if (!previewEl || !contentEl) return;

  text = text || document.getElementById('text').value;

  if (!text.trim()) {
    contentEl.innerHTML = '<span class="live-preview__placeholder">输入中文后，这里会实时显示英文结果</span>';
    previewEl.classList.remove('active');
    if (statusEl) statusEl.textContent = '⏎';
    return;
  }

  // Cancel previous request
  if (previewController) previewController.abort();
  previewController = new AbortController();

  if (statusEl) statusEl.textContent = '⏳ 生成中...';
  previewEl.classList.add('active');

  fetch('/quick', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: text, platform: 'x' }),
    signal: previewController.signal,
  })
  .then(function(r) {
    if (!r.ok) throw new Error('Preview failed');
    return r.json();
  })
  .then(function(data) {
    contentEl.textContent = data.content || '';
    if (statusEl) statusEl.textContent = '✅ 实时';
  })
  .catch(function(err) {
    if (err.name === 'AbortError') return;
    contentEl.innerHTML = '<span class="live-preview__placeholder">预览生成中...</span>';
    if (statusEl) statusEl.textContent = '⏎';
  });
}

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
    textarea.addEventListener('input', debounce(function() {
      updateBridgeUI();
      updateLivePreview(this.value);
    }, 400));
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
