/* ── AI Content Bridge — Animation Engine ───────────────────────────────── */
/* Scroll Reveal, Counter Animation, Nav Effect, Mobile Menu, Toast System   */

(function() {
  'use strict';

  // ══════════════════════════════════════════════════════════════════════════
  // 1. NAVBAR — Glassmorphism Scroll Effect
  // ══════════════════════════════════════════════════════════════════════════
  const navbar = document.getElementById('navbar');
  if (navbar) {
    const onScroll = () => {
      navbar.classList.toggle('scrolled', window.scrollY > 40);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // initial state
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 2. MOBILE MENU — Hamburger Toggle
  // ══════════════════════════════════════════════════════════════════════════
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobile-nav');
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('active');
      mobileNav.classList.toggle('open');
      document.body.style.overflow = mobileNav.classList.contains('open') ? 'hidden' : '';
    });

    // Close on link click
    mobileNav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        hamburger.classList.remove('active');
        mobileNav.classList.remove('open');
        document.body.style.overflow = '';
      });
    });
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 3. SCROLL REVEAL — IntersectionObserver
  // ══════════════════════════════════════════════════════════════════════════
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        // Optional: unobserve after reveal for performance
        revealObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.08,
    rootMargin: '0px 0px -40px 0px'
  });

  document.querySelectorAll('[data-aos="fade-up"]').forEach(el => revealObserver.observe(el));

  // Also observe sections without data-aos
  document.querySelectorAll('.section:not([data-aos])').forEach(el => {
    el.setAttribute('data-aos', 'fade-up');
    revealObserver.observe(el);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 4. COUNTER ANIMATION — Trust Bar Numbers
  // ══════════════════════════════════════════════════════════════════════════
  function animateCounters() {
    const counters = document.querySelectorAll('.count-up');
    if (!counters.length) return;

    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseInt(el.dataset.target, 10) || 0;
          const duration = 1800;
          const startTime = performance.now();

          function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(eased * target);
            el.textContent = current.toLocaleString();
            if (progress < 1) {
              requestAnimationFrame(update);
            } else {
              el.textContent = target.toLocaleString();
            }
          }

          requestAnimationFrame(update);
          counterObserver.unobserve(el);
        }
      });
    }, { threshold: 0.5 });

    counters.forEach(c => counterObserver.observe(c));
  }
  animateCounters();

  // ══════════════════════════════════════════════════════════════════════════
  // 5. TOAST SYSTEM
  // ══════════════════════════════════════════════════════════════════════════
  window.showToast = function(message, duration = 2500) {
    let toast = document.querySelector('.toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(() => toast.classList.remove('show'), duration);
  };

  // ══════════════════════════════════════════════════════════════════════════
  // 6. CHARACTER COUNTER — Textarea
  // ══════════════════════════════════════════════════════════════════════════
  document.querySelectorAll('textarea[data-char-count]').forEach(textarea => {
    const counterId = textarea.dataset.charCount;
    const counter = document.getElementById(counterId);
    if (!counter) return;

    const update = () => {
      counter.textContent = `${textarea.value.length} chars`;
    };
    textarea.addEventListener('input', update);
    update();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 7. PRICING TOGGLE (when present)
  // ══════════════════════════════════════════════════════════════════════════
  const pricingToggle = document.getElementById('pricing-toggle');
  if (pricingToggle) {
    pricingToggle.addEventListener('click', () => {
      pricingToggle.classList.toggle('active');
      const isYearly = pricingToggle.classList.contains('active');

      // Update toggle labels
      document.querySelectorAll('.toggle-label').forEach(label => {
        label.classList.toggle('active', label.dataset.period === (isYearly ? 'yearly' : 'monthly'));
      });

      // Animate prices
      document.querySelectorAll('.price-value').forEach(el => {
        const monthly = parseInt(el.dataset.monthly, 10);
        const yearly = parseInt(el.dataset.yearly, 10);
        el.textContent = isYearly ? `$${yearly}` : `$${monthly}`;
      });

      document.querySelectorAll('.period-value').forEach(el => {
        el.textContent = isYearly ? '/yr' : '/mo';
      });
    });
  }

  // ══════════════════════════════════════════════════════════════════════════
  // 8. FAQ ACCORDION — Smooth toggle
  // ══════════════════════════════════════════════════════════════════════════
  document.querySelectorAll('.faq-q').forEach(q => {
    q.addEventListener('click', () => {
      const isOpen = q.classList.contains('open');
      // Close all
      document.querySelectorAll('.faq-q.open').forEach(el => {
        el.classList.remove('open');
        el.nextElementSibling.classList.remove('open');
      });
      // Toggle clicked
      if (!isOpen) {
        q.classList.add('open');
        q.nextElementSibling.classList.add('open');
      }
    });
  });

})();
