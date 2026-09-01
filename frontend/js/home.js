/** Homepage: populate hero slider, strengths, services grid, projects, testimonials. */

// ---------------------------------------------------------------------
// Hero slider. Renders every slide up front (all in the DOM at once, only
// the active one visible) and just toggles which one is .active - see the
// crossfade transition on .hero-slide in style.css.
// ---------------------------------------------------------------------
let __tgpHeroSlides = [];
let __tgpHeroIndex = 0;
let __tgpHeroTimer = null;

function tgpRenderHeroSlide(s, isActive) {
  return `
    <div class="hero-slide${isActive ? ' active' : ''}">
      <div class="hero-bg" style="background-image:url('${tgpEscapeHtml(s.image_url)}')"></div>
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        ${s.eyebrow ? `<div class="hero-eyebrow">${tgpEscapeHtml(s.eyebrow)}</div>` : ''}
        <h1 class="hero-title">${tgpEscapeHtml(s.title_line1 || '')}${s.title_line2 ? `<span>${tgpEscapeHtml(s.title_line2)}</span>` : ''}</h1>
        ${s.subtitle ? `<p class="hero-subtitle">${tgpEscapeHtml(s.subtitle)}</p>` : ''}
        <div class="hero-actions">
          ${s.button1_text ? `<a href="${tgpEscapeHtml(s.button1_link || '#')}" class="btn btn-primary">${tgpEscapeHtml(s.button1_text)}</a>` : ''}
          ${s.button2_text ? `<a href="${tgpEscapeHtml(s.button2_link || '#')}" class="btn btn-outline">${tgpEscapeHtml(s.button2_text)}</a>` : ''}
          ${isActive ? `
          <button type="button" class="btn btn-video" id="open-intro-video">
            <span class="btn-video-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M8 5v14l11-7z"/></svg></span>
            Xem video giới thiệu
          </button>` : ''}
        </div>
      </div>
    </div>`;
}

function tgpGoToHeroSlide(index) {
  if (!__tgpHeroSlides.length) return;
  __tgpHeroIndex = (index + __tgpHeroSlides.length) % __tgpHeroSlides.length;
  document.querySelectorAll('#hero-slides .hero-slide').forEach((el, i) => el.classList.toggle('active', i === __tgpHeroIndex));
  document.querySelectorAll('#hero-dots button').forEach((el, i) => el.classList.toggle('active', i === __tgpHeroIndex));
  tgpResetHeroAutoplay();
}

function tgpResetHeroAutoplay() {
  if (__tgpHeroTimer) clearInterval(__tgpHeroTimer);
  if (__tgpHeroSlides.length < 2) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  __tgpHeroTimer = setInterval(() => tgpGoToHeroSlide(__tgpHeroIndex + 1), 6500);
}

async function loadHeroSlides() {
  const container = document.getElementById('hero-slides');
  if (!container) return;
  try {
    const res = await TGP_API.get('/api/hero-slides', { auth: false });
    __tgpHeroSlides = res.data || [];
    if (!__tgpHeroSlides.length) return;

    container.innerHTML = __tgpHeroSlides.map((s, i) => tgpRenderHeroSlide(s, i === 0)).join('');
    initIntroVideoModal();
    initHeroParallax();

    if (__tgpHeroSlides.length > 1) {
      const prevBtn = document.getElementById('hero-prev');
      const nextBtn = document.getElementById('hero-next');
      const dots = document.getElementById('hero-dots');
      prevBtn.hidden = false;
      nextBtn.hidden = false;
      dots.hidden = false;
      dots.innerHTML = __tgpHeroSlides.map((_, i) => `<button type="button" aria-label="Ảnh ${i + 1}" class="${i === 0 ? 'active' : ''}"></button>`).join('');
      prevBtn.addEventListener('click', () => tgpGoToHeroSlide(__tgpHeroIndex - 1));
      nextBtn.addEventListener('click', () => tgpGoToHeroSlide(__tgpHeroIndex + 1));
      dots.querySelectorAll('button').forEach((btn, i) => btn.addEventListener('click', () => tgpGoToHeroSlide(i)));
      tgpResetHeroAutoplay();
    }
  } catch (e) {
    // Leave the hero empty (still shows the navy fallback background) rather
    // than blocking the rest of the homepage from rendering.
  }
}

// ---------------------------------------------------------------------
// "Vi sao chon chung toi" strength cards.
// ---------------------------------------------------------------------
async function loadHomeStrengths() {
  const grid = document.getElementById('home-strengths-grid');
  if (!grid) return;
  try {
    const res = await TGP_API.get('/api/strengths', { auth: false });
    const items = res.data || [];
    if (!items.length) { grid.innerHTML = ''; return; }
    grid.innerHTML = items.map(s => `
      <div class="strength-card reveal">
        <div class="strength-photo">${s.image_url ? `<img src="${tgpEscapeHtml(s.image_url)}" alt="${tgpEscapeHtml(s.title)}">` : '✓'}</div>
        <h3>${tgpEscapeHtml(s.title)}</h3>
        <p>${tgpEscapeHtml(s.description || '')}</p>
      </div>`).join('');
  } catch (e) {
    grid.innerHTML = '';
  }
}

async function loadHomeServices() {
  const grid = document.getElementById('home-services-grid');
  if (!grid) return;
  try {
    const res = await TGP_API.get('/api/services', { auth: false });
    const services = (res.data || []).slice(0, 8);
    grid.innerHTML = services.map(s => {
      const num = s.icon || '';
      const title = s.title.replace(/^\d+\.\s*/, '');
      return `
        <div class="service-card reveal">
          <div class="service-num">${tgpEscapeHtml(num)}</div>
          <div class="service-icon">${tgpIconForService(s.code)}</div>
          <h3>${tgpEscapeHtml(title)}</h3>
          <p>${tgpEscapeHtml(s.short_description || '')}</p>
          <a class="service-link" href="/pages/dich-vu.html#${tgpEscapeHtml(s.slug)}">Xem chi tiết →</a>
        </div>`;
    }).join('');
    initTiltCards('#home-services-grid .service-card');
  } catch (e) {
    grid.innerHTML = '<p style="color:var(--text-muted)">Không thể tải danh sách dịch vụ lúc này.</p>';
  }
}

async function loadHomeProjects() {
  const grid = document.getElementById('home-projects-grid');
  if (!grid) return;
  try {
    const res = await TGP_API.get('/api/projects?limit=3', { auth: false });
    const projects = res.data || [];
    if (!projects.length) {
      grid.innerHTML = '<div class="empty-state">Chưa có dự án nào được đăng tải. Vui lòng quay lại sau.</div>';
      return;
    }
    grid.innerHTML = projects.map(p => `
      <a href="/pages/du-an-chi-tiet.html?slug=${encodeURIComponent(p.slug)}" class="project-card reveal">
        <img src="${tgpEscapeHtml(p.cover_image || '')}" alt="${tgpEscapeHtml(p.title)}" loading="lazy">
        <div class="overlay">
          <span class="tag">${tgpEscapeHtml(TGP_CATEGORY_LABELS[p.category] || p.category)}</span>
          <h3>${tgpEscapeHtml(p.title)}</h3>
          <div class="meta">
            ${p.location ? `<span>${tgpEscapeHtml(p.location)}</span>` : ''}
            ${p.area_m2 ? `<span>${p.area_m2} m²</span>` : ''}
            ${p.year ? `<span>${p.year}</span>` : ''}
          </div>
        </div>
      </a>`).join('');
    initTiltCards('#home-projects-grid .project-card');
  } catch (e) {
    grid.innerHTML = '<div class="empty-state">Không thể tải dự án lúc này.</div>';
  }
}

async function loadHomeTestimonials() {
  const track = document.getElementById('home-testimonials');
  if (!track) return;
  try {
    const res = await TGP_API.get('/api/testimonials', { auth: false });
    const items = res.data || [];
    if (!items.length) {
      track.innerHTML = '<div class="empty-state">Chưa có đánh giá nào được đăng tải.</div>';
      return;
    }
    track.innerHTML = items.map(t => `
      <div class="testimonial-card reveal">
        <div class="stars">${'★'.repeat(t.rating)}${'☆'.repeat(5 - t.rating)}</div>
        <p class="quote">"${tgpEscapeHtml(t.content)}"</p>
        <div class="testimonial-person">
          <div class="testimonial-avatar">${t.avatar_url ? `<img src="${tgpEscapeHtml(t.avatar_url)}" alt="">` : tgpEscapeHtml((t.customer_name || '?')[0])}</div>
          <div>
            <strong>${tgpEscapeHtml(t.customer_name)}</strong>
            <span>${tgpEscapeHtml(t.project_name || '')}</span>
          </div>
        </div>
      </div>`).join('');
  } catch (e) {
    track.innerHTML = '<div class="empty-state">Không thể tải đánh giá khách hàng.</div>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadHeroSlides();
  loadHomeStrengths();
  loadHomeServices();
  loadHomeProjects();
  loadHomeTestimonials();
});
