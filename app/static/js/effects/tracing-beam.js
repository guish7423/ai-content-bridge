/* ═══════════════════════════════════════════════════════════════════════════
   AI Content Bridge — Tracing Beam Effect v1.0
   ═══════════════════════════════════════════════════════════════════════════ */

(function initTracingBeam() {
  var beam = document.querySelector('.tracing-beam');
  var steps = document.querySelectorAll('.step-item');
  if (!beam || !steps.length) return;

  var dot = document.createElement('div');
  dot.className = 'tracing-beam__dot';
  beam.appendChild(dot);

  function updateBeam() {
    var visibleStep = null;
    var visibleIndex = -1;

    steps.forEach(function(step, i) {
      var rect = step.getBoundingClientRect();
      var isVisible = rect.top < window.innerHeight * 0.6 && rect.bottom > 0;

      if (isVisible && visibleIndex < i) {
        visibleStep = step;
        visibleIndex = i;
      }

      if (isVisible) {
        step.classList.add('visible');
      }
    });

    if (visibleStep) {
      var stepRect = visibleStep.getBoundingClientRect();
      var beamRect = beam.getBoundingClientRect();
      var relativeTop = stepRect.top + stepRect.height / 2 - beamRect.top;
      dot.style.top = relativeTop + 'px';
      dot.classList.add('tracing-beam__dot--active');

      var progress = (visibleIndex + 1) / steps.length;
      beam.querySelector('.tracing-beam__line').style.opacity = 0.3 + (progress * 0.4);
    }
  }

  // Use IntersectionObserver for efficiency
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.3 });

  steps.forEach(function(step) { observer.observe(step); });

  // Throttled scroll for beam dot position
  var ticking = false;
  window.addEventListener('scroll', function() {
    if (!ticking) {
      window.requestAnimationFrame(function() {
        updateBeam();
        ticking = false;
      });
      ticking = true;
    }
  });

  updateBeam();
  window.addEventListener('resize', updateBeam);
})();
