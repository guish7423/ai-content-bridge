/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — 3D Card Tilt + Light Glow Effect v2.0
   ═══════════════════════════════════════════════════════════════════════════ */

(function initTilt3D() {
  if ('ontouchstart' in window) return;

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.ks-bento__tile, .ks-card').forEach(function(card) {
      card.style.setProperty('--glow-x', '50%');
      card.style.setProperty('--glow-y', '50%');

      card.addEventListener('mousemove', function(e) {
        var rect = card.getBoundingClientRect();
        var x = (e.clientX - rect.left) / rect.width;
        var y = (e.clientY - rect.top) / rect.height;

        // 3D tilt
        card.style.transform = 'perspective(800px) rotateY(' + ((x - 0.5) * 8) + 'deg) rotateX(' + ((0.5 - y) * 8) + 'deg) translateZ(10px)';

        // Light glow follows cursor
        card.style.setProperty('--glow-x', (x * 100) + '%');
        card.style.setProperty('--glow-y', (y * 100) + '%');
      });

      card.addEventListener('mouseleave', function() {
        card.style.transform = 'perspective(800px) rotateY(0deg) rotateX(0deg) translateZ(0)';
        card.style.transition = 'transform 0.4s ease, box-shadow 0.4s ease';
        setTimeout(function() { card.style.transition = ''; }, 400);
      });
    });
  });
})();
