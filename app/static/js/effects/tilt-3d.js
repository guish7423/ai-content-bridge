/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — 3D Card Tilt Effect v1.0 (for pricing page)
   ═══════════════════════════════════════════════════════════════════════════ */

(function initTilt3D() {
  var isTouch = 'ontouchstart' in window;
  if (isTouch) return;

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.ks-bento__tile').forEach(function(card) {
      card.addEventListener('mousemove', function(e) {
        var rect = card.getBoundingClientRect();
        var x = (e.clientX - rect.left) / rect.width - 0.5;
        var y = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.transform = 'perspective(800px) rotateY(' + (x * 6) + 'deg) rotateX(' + (-y * 6) + 'deg) translateZ(8px)';
      });
      card.addEventListener('mouseleave', function() {
        card.style.transform = 'perspective(800px) rotateY(0deg) rotateX(0deg) translateZ(0)';
        card.style.transition = 'transform 0.3s ease';
        setTimeout(function() { card.style.transition = ''; }, 300);
      });
    });
  });
})();
