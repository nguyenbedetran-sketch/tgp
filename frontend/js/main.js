/**
 * Shared behaviour for every public page: sticky header, mobile nav,
 * scroll-reveal animations, counter animation, toast notifications,
 * dynamic company-info binding (from /api/settings) and pageview logging.
 */

// ---------------------------------------------------------------------
// Toasts
// ---------------------------------------------------------------------
function tgpToast(message, type = 'success', title) {
  let stack = document.querySelector('.toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'toast-stack';
    document.body.appendChild(stack);
  }
  const el = document.createElement('div');
  el.className = `toast ${type === 'error' ? 'error' : ''}`;
  el.innerHTML = `${title ? `<strong>${title}</strong>` : ''}${message}`;
  stack.appendChild(el);
  setTimeout(() => {
    el.style.transition = 'opacity .3s ease, transform .3s ease';
    el.style.opacity = '0';
    el.style.transform = 'translateX(30px)';
    setTimeout(() => el.remove(), 320);
  }, 4200);
}

// ---------------------------------------------------------------------
// Header scroll + mobile nav
// ---------------------------------------------------------------------
function initHeader() {
  const header = document.querySelector('.site-header');
  if (header) {
    const onScroll = () => {
      header.classList.toggle('scrolled', window.scrollY > 40);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  const hamburger = document.querySelector('.hamburger');
  const nav = document.querySelector('.main-nav');
  const overlay = document.querySelector('.nav-overlay');
  if (hamburger && nav) {
    const closeNav = () => { nav.classList.remove('open'); overlay?.classList.remove('open'); };
    hamburger.addEventListener('click', () => {
      nav.classList.toggle('open');
      overlay?.classList.toggle('open');
    });
    overlay?.addEventListener('click', closeNav);
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', closeNav));
  }

  // Highlight the current page in nav
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.main-nav a[data-nav]').forEach(a => {
    if (a.getAttribute('data-nav') === currentPath) a.classList.add('active');
  });
}

// ---------------------------------------------------------------------
// Header stack: wraps the existing fixed `.site-header` in a new fixed
// `.header-stack`, and prepends two optional rows above it -
//   1. a dismissible announcement/promo bar
//   2. a quick-contact info bar (phone / email / working hours)
// Both rows are populated from /api/settings and hidden entirely when
// there's nothing to show, so pages with no announcement configured render
// exactly like before. Wrapping via JS (instead of editing every page's
// header markup) keeps this in one place for all ~10 public pages.
// ---------------------------------------------------------------------
const ICON_MAIL_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 4h16v16H4zM4 6l8 7 8-7"/></svg>';
const ICON_CLOCK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>';

function initHeaderStack() {
  const header = document.querySelector('.site-header');
  if (!header || header.parentElement.classList.contains('header-stack')) return;

  const stack = document.createElement('div');
  stack.className = 'header-stack';
  header.parentNode.insertBefore(stack, header);

  const announcement = document.createElement('div');
  announcement.className = 'announcement-bar';
  announcement.hidden = true;
  announcement.innerHTML = `
    <div class="container">
      <span class="announcement-text"></span>
      <button type="button" class="announcement-close" aria-label="Đóng thông báo">&times;</button>
    </div>`;
  stack.appendChild(announcement);

  const infoBar = document.createElement('div');
  infoBar.className = 'header-info-bar';
  infoBar.hidden = true;
  infoBar.innerHTML = '<div class="container"></div>';
  stack.appendChild(infoBar);

  stack.appendChild(header);

  announcement.querySelector('.announcement-close').addEventListener('click', () => {
    announcement.hidden = true;
    try { localStorage.setItem('tgp_announcement_dismissed', announcement.dataset.id || ''); } catch (e) { /* ignore */ }
    syncHeaderHeight();
  });

  window.addEventListener('resize', syncHeaderHeight);
}

function applyHeaderStackSettings(settings) {
  const announcement = document.querySelector('.announcement-bar');
  if (announcement) {
    const enabled = settings.announcement_enabled === 'true' || settings.announcement_enabled === '1';
    const text = (settings.announcement_text || '').trim();
    let dismissed = '';
    try { dismissed = localStorage.getItem('tgp_announcement_dismissed') || ''; } catch (e) { /* ignore */ }
    if (enabled && text && dismissed !== text) {
      announcement.dataset.id = text;
      const link = (settings.announcement_link || '').trim();
      const isRealLink = /^https?:\/\//i.test(link) || link.startsWith('/');
      announcement.querySelector('.announcement-text').innerHTML = isRealLink
        ? `${tgpEscapeHtml(text)} <a href="${tgpEscapeHtml(link)}">Xem ngay →</a>`
        : tgpEscapeHtml(text);
      announcement.hidden = false;
    } else {
      announcement.hidden = true;
    }
  }

  const infoBar = document.querySelector('.header-info-bar');
  if (infoBar) {
    const hotline = (settings.hotline || settings.phone || '').trim();
    const email = (settings.email || '').trim();
    const hours = (settings.working_hours || '').trim();
    const parts = [];
    if (hotline) parts.push(`<a href="tel:${hotline.replace(/\s+/g, '')}">${QC_PHONE_SVG}<span>${tgpEscapeHtml(hotline)}</span></a>`);
    if (email) parts.push(`<a href="mailto:${email}">${ICON_MAIL_SVG}<span>${tgpEscapeHtml(email)}</span></a>`);
    if (hours) parts.push(`<span class="info-hours">${ICON_CLOCK_SVG}<span>${tgpEscapeHtml(hours)}</span></span>`);
    infoBar.querySelector('.container').innerHTML = parts.join('');
    infoBar.hidden = parts.length === 0;
  }

  syncHeaderHeight();
}

function syncHeaderHeight() {
  const stack = document.querySelector('.header-stack');
  if (!stack) return;
  requestAnimationFrame(() => {
    document.documentElement.style.setProperty('--header-h', `${stack.offsetHeight}px`);
  });
}

// ---------------------------------------------------------------------
// Scroll progress bar. The markup (`<div class="scroll-progress"><span>`)
// only exists on index.html / gioi-thieu.html, so this is a no-op on every
// other page.
// ---------------------------------------------------------------------
function initScrollProgress() {
  const bar = document.querySelector('.scroll-progress span');
  if (!bar) return;
  const update = () => {
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    const pct = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
    bar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
  };
  update();
  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
}

// ---------------------------------------------------------------------
// Hero cursor parallax (desktop only, only on the homepage's .hero
// section). Shifts background-position rather than transform so it never
// fights the heroZoom keyframe animation already running on .hero-bg.
// ---------------------------------------------------------------------
function initHeroParallax() {
  const hero = document.querySelector('.hero');
  const heroBg = document.querySelector('.hero .hero-bg');
  if (!hero || !heroBg) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!window.matchMedia('(pointer: fine)').matches) return;

  hero.addEventListener('mousemove', (e) => {
    const r = hero.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    heroBg.style.backgroundPosition = `${50 - px * 12}% ${50 - py * 12}%`;
  });
  hero.addEventListener('mouseleave', () => {
    heroBg.style.backgroundPosition = '50% 50%';
  });
}

// ---------------------------------------------------------------------
// 3D tilt-on-hover for cards (desktop only). Call this AFTER injecting
// cards into the DOM (e.g. right after an API-populated grid's innerHTML
// is set), with a selector scoped to that grid's container id, so the
// effect only applies to the specific grid the caller intends.
// ---------------------------------------------------------------------
function initTiltCards(selector) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!window.matchMedia('(pointer: fine)').matches) return;
  document.querySelectorAll(selector).forEach(card => {
    if (card.__tgpTiltBound) return;
    card.__tgpTiltBound = true;
    card.addEventListener('mousemove', (e) => {
      const r = card.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      card.style.transform = `translateY(-8px) perspective(900px) rotateX(${(-py * 6).toFixed(2)}deg) rotateY(${(px * 8).toFixed(2)}deg)`;
    });
    card.addEventListener('mouseleave', () => { card.style.transform = ''; });
  });
}

// ---------------------------------------------------------------------
// Scroll-reveal animations (IntersectionObserver, graceful no-op fallback)
//
// Pages load most of their content asynchronously (services/projects/blog/
// testimonials/team fetched from the API and injected via innerHTML), so a
// single one-shot querySelectorAll('.reveal') at DOMContentLoaded is not
// enough - it would miss every element added after that point and leave it
// permanently invisible (opacity: 0 forever). To avoid depending on every
// call site remembering to re-run initReveal(), a MutationObserver watches
// the whole document for newly-added .reveal elements and observes them
// automatically. A short safety-net timeout also force-reveals anything
// still hidden, so a slow network or an edge case never leaves content
// permanently blank for a real visitor.
// ---------------------------------------------------------------------
let __tgpRevealIO = null;

function __tgpObserveReveal(el) {
  if (!__tgpRevealIO) {
    el.classList.add('is-visible');
    return;
  }
  __tgpRevealIO.observe(el);
}

function initReveal() {
  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('.reveal').forEach(el => el.classList.add('is-visible'));
    return;
  }
  if (!__tgpRevealIO) {
    __tgpRevealIO = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          __tgpRevealIO.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    // Auto-pick-up any .reveal element added to the DOM later (e.g. after
    // an API fetch resolves and a page injects a grid of cards).
    const mo = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType !== 1) return;
          if (node.matches && node.matches('.reveal')) __tgpObserveReveal(node);
          node.querySelectorAll && node.querySelectorAll('.reveal').forEach(__tgpObserveReveal);
        });
      }
    });
    mo.observe(document.body, { childList: true, subtree: true });

    // Safety net: never let a real visitor be stuck looking at blank
    // sections because of a timing edge case.
    setInterval(() => {
      document.querySelectorAll('.reveal:not(.is-visible)').forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight + 200) el.classList.add('is-visible');
      });
    }, 1500);
  }

  document.querySelectorAll('.reveal').forEach(__tgpObserveReveal);
}

// ---------------------------------------------------------------------
// Counter animation (elements: <span class="stat-number" data-target="100">)
// ---------------------------------------------------------------------
function animateCounter(el, target, duration = 1600) {
  const start = performance.now();
  const isFloat = target % 1 !== 0;
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = target * eased;
    el.textContent = (isFloat ? value.toFixed(1) : Math.round(value)).toString();
    if (progress < 1) requestAnimationFrame(tick);
    else {
      el.textContent = target.toString();
      el.classList.add('stat-pop');
      setTimeout(() => el.classList.remove('stat-pop'), 500);
    }
  }
  requestAnimationFrame(tick);
}

function initCounters() {
  const counters = document.querySelectorAll('.stat-number[data-target]');
  if (!counters.length) return;
  const run = (el) => {
    const target = parseFloat(el.getAttribute('data-target'));
    if (!isNaN(target)) animateCounter(el, target);
  };
  if (!('IntersectionObserver' in window)) {
    counters.forEach(run);
    return;
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        run(entry.target);
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.4 });
  counters.forEach(el => io.observe(el));
}

// ---------------------------------------------------------------------
// Company info binding: any element with data-setting="phone" gets its
// textContent (or href, for <a>) filled from /api/settings.
// ---------------------------------------------------------------------
async function initSettings() {
  try {
    const res = await TGP_API.get('/api/settings', { auth: false });
    const settings = res.data || {};
    document.querySelectorAll('[data-setting]').forEach(el => {
      const key = el.getAttribute('data-setting');
      const value = settings[key];
      if (value === undefined) return;
      if (el.hasAttribute('data-setting-href')) {
        const trimmed = (value || '').trim();
        if (!trimmed) {
          // Not configured yet (empty, or still the unfilled `[LINK ...]` /
          // `[SO DIEN THOAI]` placeholder that fails the checks below) -
          // hide the element instead of shipping a dead/broken link.
          el.style.display = 'none';
        } else if (key.startsWith('phone') || key === 'hotline') {
          el.setAttribute('href', `tel:${trimmed.replace(/\s+/g, '')}`);
        } else if (key === 'email') {
          el.setAttribute('href', `mailto:${trimmed}`);
        } else if (/^https?:\/\//i.test(trimmed)) {
          el.setAttribute('href', trimmed);
        } else {
          el.style.display = 'none';
        }
      }
      // `data-setting-href-only` opts an element out of having its own label
      // text replaced by the raw setting value - use it on CTA buttons like
      // "Goi ngay" / "Chat qua Zalo" that should keep their own wording and
      // only borrow the href from settings.
      if (!el.hasAttribute('data-setting-href-only')) {
        el.textContent = value;
      }
    });
    document.querySelectorAll('[data-setting-year]').forEach(el => {
      el.textContent = settings.copyright_year || new Date().getFullYear();
    });
    // Feed real counters into the animated stat elements if present.
    document.querySelectorAll('.stat-number[data-setting-counter]').forEach(el => {
      const key = el.getAttribute('data-setting-counter');
      if (settings[key]) el.setAttribute('data-target', settings[key]);
    });
    initCounters();
    renderMapEmbed(settings.map_embed_url);
    initQuickContact(settings);
    applyHeaderStackSettings(settings);
    window.__tgpSettings = settings;
  } catch (e) {
    // Non-fatal: page still renders with static placeholder text.
    initCounters();
    console.warn('Không thể tải site settings', e);
  }
}

// ---------------------------------------------------------------------
// Floating quick-contact widget (call + Zalo), added to every public page
// once settings load. Deliberately self-contained (own inline SVG) rather
// than depending on TGP_ICONS, since not every page loads js/icons.js.
// Placed bottom-LEFT so it never overlaps the toast stack (bottom-right).
// ---------------------------------------------------------------------
const QC_PHONE_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 3a2 2 0 0 1-.5 2.1L8 10.1a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c1 .3 2 .5 3 .7a2 2 0 0 1 1.6 2z"/></svg>';

function initQuickContact(settings) {
  if (document.querySelector('.quick-contact')) return;
  const hotline = (settings.hotline || settings.phone || '').trim();
  const zaloUrl = (settings.zalo_url || '').trim();
  const zaloHref = /^https?:\/\//i.test(zaloUrl) ? zaloUrl : '';
  if (!hotline && !zaloHref) return;

  const wrap = document.createElement('div');
  wrap.className = 'quick-contact';

  if (hotline) {
    const call = document.createElement('a');
    call.href = `tel:${hotline.replace(/\s+/g, '')}`;
    call.className = 'qc-btn qc-call';
    call.title = `Gọi ngay ${hotline}`;
    call.setAttribute('aria-label', `Gọi ngay ${hotline}`);
    call.innerHTML = QC_PHONE_SVG;
    wrap.appendChild(call);
  }
  if (zaloHref) {
    const zalo = document.createElement('a');
    zalo.href = zaloHref;
    zalo.target = '_blank';
    zalo.rel = 'noopener noreferrer';
    zalo.className = 'qc-btn qc-zalo';
    zalo.title = 'Chat qua Zalo';
    zalo.setAttribute('aria-label', 'Chat qua Zalo');
    zalo.textContent = 'Zalo';
    wrap.appendChild(zalo);
  }
  document.body.appendChild(wrap);
}

// ---------------------------------------------------------------------
// Google Maps embed on the contact page. `map_embed_url` (set via
// Admin -> Thong tin cong ty) must be a real EMBED url from Google Maps'
// "Chia se" -> "Nhung ban do" (Share -> Embed a map) dialog - it looks like
// https://www.google.com/maps/embed?pb=... . A normal "share/directions"
// link (maps.google.com/maps/dir/... or /maps/place/...) is NOT
// embeddable - Google blocks it from loading inside an <iframe>, so it
// would just show a blank box. We detect that case and show a plain
// "open in Google Maps" link instead of a broken iframe.
// ---------------------------------------------------------------------
function renderMapEmbed(rawValue) {
  const frame = document.getElementById('map-frame');
  if (!frame || !rawValue) return;

  // The setting may contain either a bare URL or the full <iframe ...>
  // snippet copy-pasted from Google's embed dialog - handle both.
  let url = rawValue.trim();
  const iframeMatch = url.match(/src=["']([^"']+)["']/i);
  if (iframeMatch) url = iframeMatch[1];

  if (!/^https:\/\/www\.google\.com\/maps\/embed/i.test(url)) {
    frame.innerHTML = '';
    const p = document.createElement('p');
    p.style.margin = '0';
    p.textContent = 'Đường liên kết bản đồ hiện chưa phải link "Nhúng bản đồ" của Google nên không hiển thị được trực tiếp tại đây.';
    const a = document.createElement('a');
    a.href = rawValue;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.textContent = 'Mở địa chỉ trên Google Maps';
    a.style.display = 'inline-block';
    a.style.marginTop = '8px';
    frame.appendChild(p);
    frame.appendChild(a);
    return;
  }

  frame.innerHTML = '';
  const iframe = document.createElement('iframe');
  iframe.src = url;
  iframe.width = '100%';
  iframe.height = '320';
  iframe.style.border = '0';
  iframe.loading = 'lazy';
  iframe.referrerPolicy = 'no-referrer-when-downgrade';
  iframe.title = 'Bản đồ vị trí Trần Gia Phát';
  frame.appendChild(iframe);
}

// ---------------------------------------------------------------------
// Real pageview logging (powers the admin dashboard "Luot truy cap")
// ---------------------------------------------------------------------
function logPageview() {
  TGP_API.post('/api/visit', { path: window.location.pathname }, { auth: false }).catch(() => {});
}

// ---------------------------------------------------------------------
// Intro video popup (homepage). The <video> has no `src` in the HTML on
// purpose (preload="none") - the file is only fetched once the visitor
// actually opens the popup, so the ~16MB video never slows down the
// initial page load.
//
// Called once at DOMContentLoaded (no-op then, since the button lives
// inside a hero slide that hasn't loaded yet) and again by home.js's
// loadHeroSlides() once the button actually exists. The two `__tgpBound`
// guards keep that safe: the button's click handler rebinds correctly for
// each freshly-rendered slide's button, while the modal's own close/escape
// handlers (on the one persistent modal element) only ever bind once.
// ---------------------------------------------------------------------
function initIntroVideoModal() {
  const openBtn = document.getElementById('open-intro-video');
  const modal = document.getElementById('intro-video-modal');
  if (!openBtn || !modal) return;

  const player = document.getElementById('intro-video-player');
  const VIDEO_SRC = '/assets/videos/gioi-thieu-tgp.mp4';

  function openModal() {
    if (!player.getAttribute('src')) {
      const source = document.createElement('source');
      source.src = VIDEO_SRC;
      source.type = 'video/mp4';
      player.appendChild(source);
      player.load();
    }
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    player.play().catch(() => {});
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = '';
    player.pause();
  }

  if (!openBtn.__tgpBound) {
    openBtn.__tgpBound = true;
    openBtn.addEventListener('click', openModal);
  }
  if (!modal.__tgpBound) {
    modal.__tgpBound = true;
    modal.querySelectorAll('[data-close-video]').forEach(el => el.addEventListener('click', closeModal));
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.hidden) closeModal();
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initHeaderStack();
  initHeader();
  initReveal();
  initSettings();
  initIntroVideoModal();
  initScrollProgress();
  initHeroParallax();
  logPageview();
});