/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — Scroll Reveal v1.0 (AOS-style, IntersectionObserver)
   ═══════════════════════════════════════════════════════════════════════════ */

(function initScrollReveal() {
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .stagger').forEach(function(el) {
      observer.observe(el);
    });
  });
})();
