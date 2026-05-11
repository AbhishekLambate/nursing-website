/* ══════════════════════════════════════════════════════════
   NursingCNE — Main Frontend JavaScript
══════════════════════════════════════════════════════════ */
'use strict';

// ── Toast Notifications ──────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || '💬'}</span><span>${message}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, duration);
}

// ── Navbar Scroll Behavior ───────────────────────────────
const navbar = document.getElementById('navbar');
const stickyCTA = document.getElementById('stickyCTA');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y > 80) {
        navbar.classList.add('scrolled');
        stickyCTA.classList.add('visible');
    } else {
        navbar.classList.remove('scrolled');
        stickyCTA.classList.remove('visible');
    }
    lastScroll = y;
}, { passive: true });

// ── Hamburger Menu ───────────────────────────────────────
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');
hamburger.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    hamburger.classList.toggle('active');
});
navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
        navLinks.classList.remove('open');
        hamburger.classList.remove('active');
    });
});

// ── Counter Animation ────────────────────────────────────
function animateCounter(el) {
    const target = parseInt(el.dataset.target);
    const duration = 2000;
    const step = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = Math.floor(current).toLocaleString('en-IN');
        if (current >= target) clearInterval(timer);
    }, 16);
}

const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.querySelectorAll('[data-target]').forEach(animateCounter);
            counterObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const heroStats = document.querySelector('.hero-stats');
if (heroStats) counterObserver.observe(heroStats);

// ── Scroll Reveal ────────────────────────────────────────
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.service-card, .offer-card, .gallery-placeholder, .testimonial-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    revealObserver.observe(el);
});

// ── Testimonials Slider ──────────────────────────────────
let currentSlide = 0;
const track = document.querySelector('.testimonials-track');
const dots = document.querySelectorAll('.dot');

function goToSlide(n) {
    currentSlide = Math.max(0, Math.min(n, dots.length - 1));
    track.style.transform = `translateX(-${currentSlide * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === currentSlide));
}
window.goToSlide = goToSlide;

// Auto-advance slider
setInterval(() => goToSlide((currentSlide + 1) % dots.length), 5000);

// ── Load Offers ──────────────────────────────────────────
async function loadOffers() {
    const grid = document.getElementById('offersGrid');
    try {
        const res = await fetch('/api/offers');
        const { offers } = await res.json();

        if (!offers || offers.length === 0) {
            grid.innerHTML = `
        <div class="offers-loading">
          <p>🎓 No active programs right now. Check back soon!</p>
        </div>`;
            return;
        }

        grid.innerHTML = offers.map(o => {
            const discount = o.original_amount ? Math.round((1 - o.amount / o.original_amount) * 100) : 0;
            const seatsLeft = o.seats_total > 0 ? o.seats_total - o.seats_filled : null;

            return `
        <div class="offer-card">
          <div class="offer-card-header">
            ${o.badge ? `<div class="offer-badge">${o.badge}</div>` : ''}
            <h3>${escHtml(o.title)}</h3>
            <div class="offer-price">
              <span class="price-current">₹${formatPrice(o.amount)}</span>
              ${o.original_amount ? `<span class="price-original">₹${formatPrice(o.original_amount)}</span>` : ''}
              ${discount > 0 ? `<span class="price-discount">${discount}% OFF</span>` : ''}
            </div>
          </div>
          <div class="offer-card-body">
            <p class="offer-desc">${escHtml(o.description || '')}</p>
            <div class="offer-meta">
              ${o.valid_till ? `<span class="offer-meta-item">📅 Valid till ${formatDate(o.valid_till)}</span>` : ''}
              ${seatsLeft !== null ? `<span class="offer-meta-item">💺 ${seatsLeft} seats left</span>` : ''}
            </div>
            <button class="btn btn-primary btn-full" onclick="openRegModal(${o.id}, '${escHtml(o.title)}', ${o.amount})">
              Register Now →
            </button>
          </div>
        </div>`;
        }).join('');

        // Re-apply reveal observer to new cards
        grid.querySelectorAll('.offer-card').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(24px)';
            el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            revealObserver.observe(el);
        });
    } catch (err) {
        console.error('Failed to load offers:', err);
        grid.innerHTML = `<div class="offers-loading"><p>⚠️ Failed to load programs. Please refresh.</p></div>`;
    }
}

// ── Registration Modal ───────────────────────────────────
const regModal = document.getElementById('regModal');
const modalBackdrop = document.getElementById('modalBackdrop');
const modalClose = document.getElementById('modalClose');
const regForm = document.getElementById('regForm');

function openRegModal(offerId, offerName, amount) {
    document.getElementById('selectedOfferId').value = offerId;
    document.getElementById('selectedAmount').value = amount;
    document.getElementById('modalOfferName').textContent = offerName;
    document.getElementById('formAmount').textContent = `₹${formatPrice(amount)}`;
    regModal.classList.add('open');
    modalBackdrop.classList.add('open');
    document.body.style.overflow = 'hidden';
}
window.openRegModal = openRegModal;

function closeRegModal() {
    regModal.classList.remove('open');
    modalBackdrop.classList.remove('open');
    document.body.style.overflow = '';
    regForm.reset();
    clearFormErrors();
}

modalClose.addEventListener('click', closeRegModal);
modalBackdrop.addEventListener('click', closeRegModal);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeRegModal(); });

// ── Form Validation ──────────────────────────────────────
function clearFormErrors() {
    document.querySelectorAll('.field-error').forEach(e => e.textContent = '');
    document.querySelectorAll('.error').forEach(e => e.classList.remove('error'));
}

function setError(fieldId, errId, msg) {
    const el = document.getElementById(fieldId);
    el.classList.add('error');
    document.getElementById(errId).textContent = msg;
    return false;
}

function validateRegForm() {
    clearFormErrors();
    let valid = true;
    const name = document.getElementById('reg-name').value.trim();
    const mobile = document.getElementById('reg-mobile').value.trim().replace(/\D/g, '');
    const email = document.getElementById('reg-email').value.trim();
    const institute = document.getElementById('reg-institute').value.trim();

    if (!name || name.length < 2) { setError('reg-name', 'err-name', 'Enter a valid full name'); valid = false; }
    if (!/^[0-9]{10}$/.test(mobile)) { setError('reg-mobile', 'err-mobile', '10-digit mobile number required'); valid = false; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError('reg-email', 'err-email', 'Enter a valid email address'); valid = false; }
    if (!institute) { setError('reg-institute', 'err-institute', 'Institute name is required'); valid = false; }
    return valid;
}

// ── Registration Form Submit ─────────────────────────────
regForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateRegForm()) return;

    const btn = document.getElementById('regSubmitBtn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;margin:0 auto;border-width:2px"></div> Processing...';

    const data = {
        offer_id: document.getElementById('selectedOfferId').value || null,
        name: document.getElementById('reg-name').value.trim(),
        mobile: document.getElementById('reg-mobile').value.trim(),
        email: document.getElementById('reg-email').value.trim(),
        institute: document.getElementById('reg-institute').value.trim(),
        reg_number: document.getElementById('reg-regnum').value.trim()
    };

    try {
        const res = await fetch('/api/registrations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();

        if (!res.ok) throw new Error(result.error || 'Registration failed');

        // If there's an amount, initiate payment
        if (result.amount > 0) {
            const payRes = await fetch('/api/payment/initiate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    registration_id: result.registration_id,
                    amount: result.amount,
                    name: data.name,
                    mobile: data.mobile,
                    email: data.email
                })
            });
            const payData = await payRes.json();

            if (payData.success && payData.paymentUrl) {
                closeRegModal();
                showToast('Redirecting to payment gateway...', 'info');
                setTimeout(() => { window.location.href = payData.paymentUrl; }, 1000);
                return;
            }
        }

        // Free or payment failed to initiate
        closeRegModal();
        showToast('Registration successful! Check your email for confirmation.', 'success', 6000);
    } catch (err) {
        showToast(err.message || 'Registration failed. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Proceed to Payment 💳';
    }
});

// ── Contact Form ─────────────────────────────────────────
document.getElementById('contactForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Sending...';
    // Simulate send (implement backend route if needed)
    await new Promise(r => setTimeout(r, 1500));
    showToast('Message sent! We\'ll get back to you soon.', 'success');
    e.target.reset();
    btn.disabled = false;
    btn.textContent = 'Send Message 📨';
});

// ── Utilities ────────────────────────────────────────────
function escHtml(str) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(str).replace(/[&<>"']/g, c => map[c]);
}
function formatPrice(n) {
    return Number(n).toLocaleString('en-IN');
}
function formatDate(d) {
    return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ── Init ─────────────────────────────────────────────────
loadOffers();
