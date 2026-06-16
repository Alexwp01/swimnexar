/* Swimnexar — main.js */

document.addEventListener('DOMContentLoaded', function() {

  /* ── Ticker inside header ── */
  var header = document.getElementById('header');
  if (header) {
    var tickerHTML = '<div class="ticker-bar"><div class="ticker-track">'
      + '<span class="ticker-item">🎉 First practice FREE — no commitment</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">📍 Land O\' Lakes · Mon / Wed / Fri · 8–9:45 PM</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">📍 Temple Terrace · Tue / Thu · 7–8 PM</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">🏆 Coached by Asian Champion Alexandr Godovanyuk</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">💻 Online sessions — anywhere in the world</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">🤽 Ages 8–18 · All levels welcome</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">🏊 Swim Team · Wesley Chapel · Tue & Thu</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">📞 WhatsApp +1 (838) 333-0666</span>'
      + '<span class="ticker-dot"></span>'
      /* duplicate for seamless loop */
      + '<span class="ticker-item">🎉 First practice FREE — no commitment</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">📍 Land O\' Lakes · Mon / Wed / Fri · 8–9:45 PM</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">📍 Temple Terrace · Tue / Thu · 7–8 PM</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">🏆 Coached by Asian Champion Alexandr Godovanyuk</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">💻 Online sessions — anywhere in the world</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">🤽 Ages 8–18 · All levels welcome</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">🏊 Swim Team · Wesley Chapel · Tue & Thu</span>'
      + '<span class="ticker-dot"></span>'
      + '<span class="ticker-item">📞 WhatsApp +1 (838) 333-0666</span>'
      + '</div></div>';
    header.insertAdjacentHTML('afterbegin', tickerHTML);
  }

  /* ── Floating WhatsApp button ── */
  var wa = document.createElement('a');
  wa.href = 'https://wa.me/18383330666';
  wa.target = '_blank';
  wa.rel = 'noopener noreferrer';
  wa.className = 'wa-float';
  wa.setAttribute('aria-label', 'Chat on WhatsApp');
  wa.textContent = '💬';
  document.body.appendChild(wa);

});

/* ── Form submission → Google Apps Script ── */
const APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbzFaQscVvj-a6OWdvoZA9-QtxE_hXBWS8h8vDIT8Ihi9Jd-H5tj4bFFmtqstzrQaDHL/exec';

async function submitToGoogleForms(data) {
  await fetch(APPS_SCRIPT_URL, { method: 'POST', mode: 'no-cors', body: JSON.stringify(data) });
}

/* ── Entry popup ── */
const overlay    = document.getElementById('entryOverlay');
const pickWP     = document.getElementById('pickWaterpolo');

if (overlay) {
  // Show popup unless already dismissed this session
  if (!sessionStorage.getItem('programChosen')) {
    document.body.style.overflow = 'hidden';
  } else {
    overlay.classList.add('hidden');
  }

  // Water polo → close popup, stay on page
  if (pickWP) {
    pickWP.addEventListener('click', () => {
      sessionStorage.setItem('programChosen', 'waterpolo');
      overlay.classList.add('hidden');
      document.body.style.overflow = '';
    });
  }

  // Swim team card is an <a href="swimteam.html"> — navigates naturally
  // Store choice before nav
  const pickST = overlay.querySelector('.entry-card.swimteam');
  if (pickST) {
    pickST.addEventListener('click', () => {
      sessionStorage.setItem('programChosen', 'swimteam');
    });
  }
}

/* ── Header scroll ── */
const header = document.getElementById('header');
if (header) {
  const tick = () => header.classList.toggle('scrolled', window.scrollY > 50);
  window.addEventListener('scroll', tick, { passive: true });
  tick();
}

/* ── Mobile menu ── */
const menuBtn = document.getElementById('menuBtn');
const nav     = document.getElementById('nav');
if (menuBtn && nav) {
  menuBtn.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    menuBtn.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });
  nav.querySelectorAll('.nav-link').forEach(l => l.addEventListener('click', () => {
    nav.classList.remove('open');
    menuBtn.classList.remove('open');
    document.body.style.overflow = '';
  }));
}

/* ── Scroll reveal ── */
const revealEls = document.querySelectorAll('.reveal, .reveal-l, .reveal-r');
if (revealEls.length) {
  const ro = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); ro.unobserve(e.target); } });
  }, { threshold: 0.12, rootMargin: '0px 0px -48px 0px' });
  revealEls.forEach(el => ro.observe(el));
}

/* ── FAQ accordion ── */
document.querySelectorAll('.faq-item').forEach(item => {
  const q = item.querySelector('.faq-q');
  const a = item.querySelector('.faq-a');
  if (!q || !a) return;
  q.addEventListener('click', () => {
    const open = item.classList.contains('open');
    document.querySelectorAll('.faq-item.open').forEach(x => {
      x.classList.remove('open');
      x.querySelector('.faq-a').style.maxHeight = '0';
    });
    if (!open) {
      item.classList.add('open');
      a.style.maxHeight = a.scrollHeight + 'px';
    }
  });
});

/* ── Smooth scroll ── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    const top = target.getBoundingClientRect().top + window.scrollY - (header ? header.offsetHeight + 16 : 80);
    window.scrollTo({ top, behavior: 'smooth' });
  });
});

/* ── Lightbox ── */
(function () {
  const lb = document.createElement('div');
  lb.className = 'lightbox';
  lb.innerHTML = '<button class="lightbox-close" aria-label="Close">✕</button><img src="" alt="">';
  document.body.appendChild(lb);

  const lbImg = lb.querySelector('img');

  document.querySelectorAll('.gal-item img').forEach(img => {
    img.addEventListener('click', () => {
      lbImg.src = img.src;
      lbImg.alt = img.alt;
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  });

  function closeLb() {
    lb.classList.remove('open');
    document.body.style.overflow = '';
  }

  lb.addEventListener('click', e => { if (e.target !== lbImg) closeLb(); });
  lb.querySelector('.lightbox-close').addEventListener('click', closeLb);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLb(); });
})();

/* ── Program select → swap waiver link ── */
const programSelect = document.getElementById('programSelect');
const waiverLink    = document.getElementById('waiverLink');

if (programSelect && waiverLink) {
  const waiverData = {
    waterpolo: { href: 'waterpolo-terms.html', text: 'Water Polo Tryout Terms & Conditions' },
    swimteam:  { href: 'swimteam-terms.html',  text: 'Swim Team Free Trial Terms & Conditions' }
  };
  programSelect.addEventListener('change', () => {
    const d = waiverData[programSelect.value];
    if (!d) return;
    waiverLink.href = d.href;
    waiverLink.textContent = d.text;
    const waiverCheck = document.getElementById('waiverCheck');
    if (waiverCheck) waiverCheck.checked = false;
  });
}

/* ── Pricing age toggle ── */
(function () {
  const ageBtns = document.querySelectorAll('[data-age]');
  if (!ageBtns.length) return;

  ageBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      ageBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const group = btn.dataset.age; // 'young' or 'teen'
      document.querySelectorAll('.price-amount, .price-note').forEach(el => {
        if (el.dataset[group]) el.textContent = el.dataset[group];
      });
    });
  });
})();

/* ── Waiver — modal popup ── */
(function () {
  const check = document.getElementById('waiverCheck');
  const link  = document.getElementById('waiverLink');
  if (!check || !link) return;

  check.disabled = true;
  check.title    = 'Please open the Terms & Conditions link first';

  const modal = document.createElement('div');
  modal.style.cssText = 'display:none;position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.72);overflow-y:auto;-webkit-overflow-scrolling:touch;padding:20px 16px;';
  modal.innerHTML =
    '<div style="max-width:700px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;">'
    + '<div style="position:sticky;top:0;background:#fff;border-bottom:1px solid #e5e7eb;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;">'
    + '<span id="termsModalTitle" style="font-weight:800;font-size:16px;color:#0d0d0d;"></span>'
    + '<button id="termsModalClose" style="background:none;border:none;font-size:26px;line-height:1;cursor:pointer;color:#6b7280;padding:0 6px;">&times;</button>'
    + '</div>'
    + '<div id="termsModalBody" style="padding:24px 28px 32px;font-size:15px;line-height:1.8;color:#4b5563;"></div>'
    + '<div style="padding:16px 28px 24px;border-top:1px solid #e5e7eb;background:#f9fafb;text-align:right;">'
    + '<button id="termsModalAccept" style="background:#0d0d0d;color:#fff;border:none;padding:12px 28px;border-radius:50px;font-size:14px;font-weight:700;cursor:pointer;">✓ I\'ve Read — Close</button>'
    + '</div>'
    + '</div>';
  document.body.appendChild(modal);

  function closeModal() {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
  document.getElementById('termsModalClose').addEventListener('click', closeModal);
  document.getElementById('termsModalAccept').addEventListener('click', closeModal);
  modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && modal.style.display !== 'none') closeModal(); });

  link.addEventListener('click', e => {
    e.preventDefault();
    const href = link.getAttribute('href');
    const bodyEl = document.getElementById('termsModalBody');
    bodyEl.innerHTML = '<p style="text-align:center;padding:48px 0;color:#9ca3af;">Loading…</p>';
    document.getElementById('termsModalTitle').textContent = '';
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    fetch(href)
      .then(r => r.text())
      .then(html => {
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const content = doc.querySelector('.terms-body');
        if (content) {
          content.querySelectorAll('.terms-back, a.btn').forEach(el => el.remove());
          bodyEl.innerHTML = content.innerHTML;
          document.getElementById('termsModalTitle').textContent =
            doc.querySelector('h1')?.textContent || 'Terms & Conditions';
        } else {
          bodyEl.innerHTML = '<p>Could not load. <a href="' + href + '" target="_blank" style="color:#d42b2b">Open in new tab →</a></p>';
        }
      })
      .catch(() => {
        bodyEl.innerHTML = '<p>Could not load. <a href="' + href + '" target="_blank" style="color:#d42b2b">Open in new tab →</a></p>';
      });

    check.disabled = false;
    check.title    = '';
  });

  const sel = document.getElementById('programSelect');
  if (sel) sel.addEventListener('change', () => {
    check.disabled = true;
    check.checked  = false;
    check.title    = 'Please open the Terms & Conditions link first';
  });
})();

/* ── Water polo swim gate ── */
(function () {
  const expSelect = document.getElementById('experienceSelect');
  const gate      = document.getElementById('wpGate');
  if (!expSelect || !gate) return;

  function checkGate() {
    const prog = programSelect ? programSelect.value : 'waterpolo';
    const show = prog === 'waterpolo' && expSelect.value === 'none';
    gate.style.display = show ? 'block' : 'none';
  }

  expSelect.addEventListener('change', checkGate);
  if (programSelect) programSelect.addEventListener('change', checkGate);

  // Dismiss — coach will assess anyway
  const gateDismiss = document.getElementById('gateDismiss');
  if (gateDismiss) {
    gateDismiss.addEventListener('click', () => {
      gate.style.display = 'none';
    });
  }
})();

/* ── Contact form → Google Sheets ── */
const form      = document.getElementById('contactForm');
const submitBtn = document.getElementById('submitBtn');
const formMsg   = document.getElementById('formMsg');

if (form) {
  form.addEventListener('submit', async e => {
    e.preventDefault();

    // Honeypot check — bots fill hidden field, humans don't see it
    if (form.querySelector('[name="_hp"]')?.value) return;

    // Validate required fields
    let valid = true;
    form.querySelectorAll('[required]').forEach(f => {
      f.style.borderColor = '';
      if (f.type === 'checkbox') {
        if (!f.checked) { f.style.outline = '2px solid #ef4444'; valid = false; }
        else { f.style.outline = ''; }
      } else {
        if (!f.value.trim()) { f.style.borderColor = '#ef4444'; valid = false; }
      }
    });
    if (!valid) { showMsg('err', 'Please fill in all required fields and accept the Terms & Conditions.'); return; }

    const rawData = Object.fromEntries(new FormData(form).entries());
    delete rawData['_hp'];
    rawData.waiver   = form.querySelector('[name="waiver"]')?.checked || false;
    rawData.program  = rawData.program || (window.location.pathname.includes('swimteam') ? 'swimteam' : 'waterpolo');

    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending…';
    hideMsg();

    try {
      await submitToGoogleForms(rawData);
      showMsg('ok', '✅ Thank you! We received your request. We\'ll reach out within 24 hours — reply to let us know which day works best for your first practice!');
      form.reset();
    } catch (err) {
      console.error('Google Forms error:', err);
      showMsg('err', '❌ Something went wrong. Please email swimnexar@gmail.com or WhatsApp +1 838-333-0666.');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit — First Practice is FREE →';
    }
  });
}

function showMsg(type, text) {
  if (!formMsg) return;
  formMsg.className = 'form-msg ' + type;
  formMsg.textContent = text;
  formMsg.style.display = 'block';
  formMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function hideMsg() {
  if (formMsg) formMsg.style.display = 'none';
}
