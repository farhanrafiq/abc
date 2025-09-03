// Advanced 3D Effects JavaScript

// Initialize 3D effects when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initParticles();
    init3DCards();
    initMatrixRain();
    initMouseFollower();
    initParallax();
    initGlitchEffect();
    init3DProductViewer();
});

// Particle System
function initParticles() {
    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles';
    document.body.appendChild(particlesContainer);
    
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (20 + Math.random() * 10) + 's';
        particlesContainer.appendChild(particle);
    }
}

// 3D Card Tilt Effect
function init3DCards() {
    const cards = document.querySelectorAll('.tilt-card, .product-card-3d');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.05)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
        });
    });
}

// Matrix Rain Effect
function initMatrixRain() {
    const matrixContainer = document.createElement('div');
    matrixContainer.className = 'matrix-rain';
    document.body.appendChild(matrixContainer);
    
    const columns = Math.floor(window.innerWidth / 20);
    
    for (let i = 0; i < columns; i++) {
        const column = document.createElement('div');
        column.className = 'matrix-column';
        column.style.left = i * 20 + 'px';
        column.style.animationDuration = (5 + Math.random() * 10) + 's';
        column.style.animationDelay = Math.random() * 5 + 's';
        column.style.opacity = Math.random() * 0.5;
        
        // Generate random characters
        let text = '';
        for (let j = 0; j < 20; j++) {
            text += String.fromCharCode(0x30A0 + Math.random() * 96);
        }
        column.textContent = text;
        
        matrixContainer.appendChild(column);
    }
}

// Custom Cursor with Trail
function initMouseFollower() {
    const cursor = document.createElement('div');
    cursor.style.cssText = `
        position: fixed;
        width: 20px;
        height: 20px;
        border: 2px solid cyan;
        border-radius: 50%;
        pointer-events: none;
        transition: all 0.1s ease;
        z-index: 10000;
        mix-blend-mode: difference;
    `;
    document.body.appendChild(cursor);
    
    const trail = [];
    for (let i = 0; i < 10; i++) {
        const dot = document.createElement('div');
        dot.style.cssText = `
            position: fixed;
            width: ${10 - i}px;
            height: ${10 - i}px;
            background: rgba(0, 255, 255, ${0.5 - i * 0.05});
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
        `;
        document.body.appendChild(dot);
        trail.push(dot);
    }
    
    let mouseX = 0;
    let mouseY = 0;
    
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        
        cursor.style.left = mouseX - 10 + 'px';
        cursor.style.top = mouseY - 10 + 'px';
    });
    
    // Animate trail
    setInterval(() => {
        trail.forEach((dot, index) => {
            const prevIndex = index === 0 ? { x: mouseX, y: mouseY } : trail[index - 1];
            dot.style.left = prevIndex.x - dot.offsetWidth / 2 + 'px';
            dot.style.top = prevIndex.y - dot.offsetHeight / 2 + 'px';
            dot.x = prevIndex.x;
            dot.y = prevIndex.y;
        });
    }, 50);
}

// Parallax Scrolling
function initParallax() {
    const parallaxElements = document.querySelectorAll('[data-parallax]');
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        
        parallaxElements.forEach(element => {
            const speed = element.dataset.parallax || 0.5;
            const yPos = -(scrolled * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
    });
}

// Glitch Effect on Hover
function initGlitchEffect() {
    const glitchElements = document.querySelectorAll('.glitch-hover');
    
    glitchElements.forEach(element => {
        element.addEventListener('mouseenter', () => {
            element.classList.add('glitch');
            setTimeout(() => {
                element.classList.remove('glitch');
            }, 1000);
        });
    });
}

// 3D Product Viewer
function init3DProductViewer() {
    const viewers = document.querySelectorAll('.product-3d-viewer');
    
    viewers.forEach(viewer => {
        let isRotating = false;
        let startX = 0;
        let currentRotation = 0;
        
        viewer.addEventListener('mousedown', (e) => {
            isRotating = true;
            startX = e.clientX;
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isRotating) return;
            
            const deltaX = e.clientX - startX;
            currentRotation += deltaX * 0.5;
            viewer.style.transform = `rotateY(${currentRotation}deg)`;
            startX = e.clientX;
        });
        
        document.addEventListener('mouseup', () => {
            isRotating = false;
        });
        
        // Auto-rotate when not interacting
        let autoRotate = setInterval(() => {
            if (!isRotating) {
                currentRotation += 1;
                viewer.style.transform = `rotateY(${currentRotation}deg)`;
            }
        }, 50);
    });
}

// Smooth Scroll with 3D Effect
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
            
            // Add 3D entrance animation
            target.style.animation = 'float3D 0.6s ease-out';
            setTimeout(() => {
                target.style.animation = '';
            }, 600);
        }
    });
});

// Dynamic Background Color Change
let colorIndex = 0;
const colors = [
    'linear-gradient(135deg, #0a0a0a 0%, #1a0033 50%, #000428 100%)',
    'linear-gradient(135deg, #000428 0%, #004e92 50%, #009ffd 100%)',
    'linear-gradient(135deg, #1a0033 0%, #330867 50%, #30cfd0 100%)',
    'linear-gradient(135deg, #0a0a0a 0%, #434343 50%, #000000 100%)'
];

setInterval(() => {
    colorIndex = (colorIndex + 1) % colors.length;
    document.body.style.background = colors[colorIndex];
    document.body.style.transition = 'background 3s ease-in-out';
}, 10000);

// Audio Reactive Visualizer (if audio elements present)
function initAudioVisualizer() {
    const audioElements = document.querySelectorAll('audio');
    if (audioElements.length === 0) return;
    
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    
    audioElements.forEach(audio => {
        const source = audioContext.createMediaElementSource(audio);
        source.connect(analyser);
        analyser.connect(audioContext.destination);
    });
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    function draw() {
        requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);
        
        // Update visual elements based on audio data
        const average = dataArray.reduce((a, b) => a + b) / bufferLength;
        document.body.style.filter = `hue-rotate(${average * 2}deg)`;
    }
    
    draw();
}

// Initialize Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
            entry.target.style.animation = 'float3D 1s ease-out forwards';
        }
    });
}, observerOptions);

// Observe all sections
document.querySelectorAll('section').forEach(section => {
    observer.observe(section);
});

// WebGL Background (Optional - requires Three.js)
function initWebGLBackground() {
    // This would require Three.js library
    // Placeholder for advanced WebGL effects
    console.log('WebGL effects ready for implementation');
}

// Performance optimization - reduce effects on low-end devices
function optimizePerformance() {
    const fps = 60;
    let lastTime = performance.now();
    let frames = 0;
    
    function checkPerformance() {
        const currentTime = performance.now();
        frames++;
        
        if (currentTime >= lastTime + 1000) {
            const currentFPS = Math.round(frames * 1000 / (currentTime - lastTime));
            
            if (currentFPS < 30) {
                // Disable heavy effects
                document.body.classList.add('low-performance');
                console.log('Performance mode activated');
            }
            
            frames = 0;
            lastTime = currentTime;
        }
        
        requestAnimationFrame(checkPerformance);
    }
    
    checkPerformance();
}

// Initialize performance monitoring
optimizePerformance();