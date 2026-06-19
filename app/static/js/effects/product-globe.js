// 3D product globe
// Three.js spinning sphere in hero section

(function initProductGlobe() {
  if ('ontouchstart' in window) return;
  
  var container = document.getElementById('product-globe');
  if (!container) return;
  
  var scene, camera, renderer, sphere;
  var WIDTH = container.clientWidth;
  var HEIGHT = container.clientHeight;
  
  function init() {
    scene = new THREE.Scene();
    
    camera = new THREE.PerspectiveCamera(45, WIDTH / HEIGHT, 0.1, 1000);
    camera.position.z = 3.5;
    
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(WIDTH, HEIGHT);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);
    
    // Sphere geometry
    var geometry = new THREE.SphereGeometry(1.2, 64, 64);
    
    // Gradient material
    var material = new THREE.MeshPhongMaterial({
      color: 0x6366f1,
      emissive: 0x312e81,
      emissiveIntensity: 0.2,
      shininess: 30,
      transparent: true,
      opacity: 0.9,
      wireframe: false,
    });
    
    sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);
    
    // Wireframe overlay
    var wireframeGeo = new THREE.SphereGeometry(1.22, 24, 24);
    var wireframeMat = new THREE.MeshBasicMaterial({
      color: 0x818cf8,
      wireframe: true,
      transparent: true,
      opacity: 0.15,
    });
    var wireframe = new THREE.Mesh(wireframeGeo, wireframeMat);
    scene.add(wireframe);
    
    // Floating particles
    var particlesGeo = new THREE.BufferGeometry();
    var particleCount = 200;
    var positions = new Float32Array(particleCount * 3);
    for (var i = 0; i < particleCount * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 8;
    }
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    var particlesMat = new THREE.PointsMaterial({
      color: 0x818cf8,
      size: 0.02,
      transparent: true,
      opacity: 0.4,
    });
    var particles = new THREE.Points(particlesGeo, particlesMat);
    scene.add(particles);
    
    // Lights
    var ambientLight = new THREE.AmbientLight(0x404060);
    scene.add(ambientLight);
    
    var directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);
    
    var backLight = new THREE.DirectionalLight(0x6366f1, 0.5);
    backLight.position.set(-1, -1, -0.5);
    scene.add(backLight);
    
    animate();
  }
  
  function animate() {
    requestAnimationFrame(animate);
    if (sphere) {
      sphere.rotation.x += 0.003;
      sphere.rotation.y += 0.005;
    }
    if (renderer && scene && camera) {
      renderer.render(scene, camera);
    }
  }
  
  init();
  
  window.addEventListener('resize', function() {
    WIDTH = container.clientWidth;
    HEIGHT = container.clientHeight;
    if (camera && renderer) {
      camera.aspect = WIDTH / HEIGHT;
      camera.updateProjectionMatrix();
      renderer.setSize(WIDTH, HEIGHT);
    }
  });
})();
