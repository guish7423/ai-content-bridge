/* ── Client-side i18n ──────────────────────────────────────────────────── */
(function() {
  const I18N = {
    en: {
      'nav.bridge': 'Bridge',
      'nav.pricing': 'Pricing',
      'nav.login': 'Login',
      'nav.logout': 'Logout',
      'nav.signup': 'Sign Up',
      'signup.title': 'Create Your Account',
      'signup.subtitle': 'Start bridging your content to the global audience',
      'signup.email': 'Email',
      'signup.password': 'Password',
      'signup.submit': 'Create Account',
      'signup.terms': 'Free plan: 10 conversions/month. No credit card required.',
      'signup.have_account': 'Already have an account?',
      'signup.login': 'Log in',
      'login.title': 'Welcome Back',
      'login.subtitle': 'Log in to your account',
      'login.email': 'Email',
      'login.password': 'Password',
      'login.submit': 'Log In',
      'login.no_account': "Don't have an account?",
      'login.signup': 'Sign up',
      'dashboard.title': 'Dashboard',
      'dashboard.plan': 'Plan',
      'dashboard.usage': 'Usage (month)',
      'dashboard.limit': 'Limit',
      'dashboard.api_key': 'API Key',
      'dashboard.copy': 'Copy',
      'dashboard.recent': 'Recent Conversions',
      'dashboard.loading': 'Loading…',
      'dashboard.upgrade_cta': 'Upgrade to Starter ($19/mo) for 100 conversions/month and social publishing.',
      'dashboard.upgrade_btn': 'See Plans',
      'dashboard.no_history': 'No conversions yet.',
      'dashboard.error': 'Failed to load.',
      'pricing.title': 'Simple, Transparent Pricing',
      'pricing.subtitle': 'Start free, upgrade when you need more',
      'pricing.month': '/mo',
      'pricing.popular': 'Most Popular',
      'pricing.free.name': 'Free',
      'pricing.free.feature1': '10 conversions/month',
      'pricing.free.feature2': 'All platforms (X/LinkedIn/Reddit)',
      'pricing.free.feature3': 'Basic localization',
      'pricing.free.feature4': 'Web interface',
      'pricing.free.cta': 'Get Started',
      'pricing.starter.name': 'Starter',
      'pricing.starter.feature1': '100 conversions/month',
      'pricing.starter.feature2': 'All platforms + X Threads',
      'pricing.starter.feature3': 'Advanced cultural adaptation',
      'pricing.starter.feature4': 'API access (1,000 req/hr)',
      'pricing.starter.feature5': 'Direct social publishing',
      'pricing.starter.cta': 'Subscribe',
      'pricing.pro.name': 'Pro',
      'pricing.pro.feature1': '10,000 conversions/month',
      'pricing.pro.feature2': 'All platforms + API priority',
      'pricing.pro.feature3': 'Custom brand voice training',
      'pricing.pro.feature4': 'API access (10,000 req/hr)',
      'pricing.pro.feature5': 'Priority support',
      'pricing.pro.cta': 'Subscribe',
      'pricing.coming_soon': 'Coming Soon',
    },
    zh: {
      'nav.bridge': '内容桥接',
      'nav.pricing': '定价',
      'nav.login': '登录',
      'nav.logout': '退出',
      'nav.signup': '注册',
      'signup.title': '创建您的账户',
      'signup.subtitle': '开始将您的内容桥梁到全球受众',
      'signup.email': '邮箱',
      'signup.password': '密码',
      'signup.submit': '创建账户',
      'signup.terms': '免费套餐：每月10次转换。无需信用卡。',
      'signup.have_account': '已有账户？',
      'signup.login': '登录',
      'login.title': '欢迎回来',
      'login.subtitle': '登录您的账户',
      'login.email': '邮箱',
      'login.password': '密码',
      'login.submit': '登录',
      'login.no_account': '没有账户？',
      'login.signup': '注册',
      'dashboard.title': '控制面板',
      'dashboard.plan': '套餐',
      'dashboard.usage': '本月使用量',
      'dashboard.limit': '上限',
      'dashboard.api_key': 'API 密钥',
      'dashboard.copy': '复制',
      'dashboard.recent': '最近的转换',
      'dashboard.loading': '加载中…',
      'dashboard.upgrade_cta': '升级到 Starter ($19/月) 获得每月100次转换和社交发布。',
      'dashboard.upgrade_btn': '查看套餐',
      'dashboard.no_history': '暂无转换记录。',
      'dashboard.error': '加载失败。',
      'pricing.title': '简单透明的定价',
      'pricing.subtitle': '免费开始，需要时升级',
      'pricing.month': '/月',
      'pricing.popular': '最受欢迎',
      'pricing.free.name': '免费',
      'pricing.free.feature1': '每月10次转换',
      'pricing.free.feature2': '所有平台 (X/LinkedIn/Reddit)',
      'pricing.free.feature3': '基础本地化',
      'pricing.free.feature4': 'Web 界面',
      'pricing.free.cta': '免费开始',
      'pricing.starter.name': '入门版',
      'pricing.starter.feature1': '每月100次转换',
      'pricing.starter.feature2': '所有平台 + X 线程',
      'pricing.starter.feature3': '高级文化适配',
      'pricing.starter.feature4': 'API 访问 (1,000 req/hr)',
      'pricing.starter.feature5': '直接社交发布',
      'pricing.starter.cta': '订阅',
      'pricing.pro.name': '专业版',
      'pricing.pro.feature1': '每月10,000次转换',
      'pricing.pro.feature2': '所有平台 + API 优先',
      'pricing.pro.feature3': '自定义品牌语调',
      'pricing.pro.feature4': 'API 访问 (10,000 req/hr)',
      'pricing.pro.feature5': '优先支持',
      'pricing.pro.cta': '订阅',
      'pricing.coming_soon': '即将推出',
    }
  };

  const LANG_KEY = 'acb_lang';
  let lang = localStorage.getItem(LANG_KEY) || 'en';

  function applyI18n() {
    const dict = I18N[lang] || I18N.en;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (dict[key]) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          el.setAttribute('placeholder', dict[key]);
        } else {
          el.textContent = dict[key];
        }
      }
    });
    document.documentElement.setAttribute('lang', lang);
  }

  window.setLang = function(l) {
    lang = l;
    localStorage.setItem(LANG_KEY, l);
    applyI18n();
  };

  window.getLang = function() { return lang; };

  document.addEventListener('DOMContentLoaded', applyI18n);
})();
