/* Swimnexar — main.js */

/* ── Floating WhatsApp button ── */
(function(){
  const btn = document.createElement('a');
  btn.href = 'https://wa.me/18383330666';
  btn.target = '_blank';
  btn.rel = 'noopener noreferrer';
  btn.className = 'wa-float';
  btn.setAttribute('aria-label', 'Chat on WhatsApp');
  btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="#fff"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>';
  document.body.appendChild(btn);
})();

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

/* ── Waiver checkbox — locked until terms link is opened ── */
(function () {
  const check = document.getElementById('waiverCheck');
  const link  = document.getElementById('waiverLink');
  if (!check || !link) return;
  check.disabled = true;
  check.title    = 'Please open the Terms & Conditions link first';
  link.addEventListener('click', () => {
    check.disabled = false;
    check.title    = '';
  });
  // Re-lock when program changes (link href swaps)
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
  if (!expSelect || !gate || !programSelect) return;

  function checkGate() {
    const show = programSelect.value === 'waterpolo' && expSelect.value === 'none';
    gate.style.display = show ? 'block' : 'none';
  }

  expSelect.addEventListener('change', checkGate);
  programSelect.addEventListener('change', checkGate);

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
      showMsg('ok', '✅ Thank you! We\'ll contact you within 24 hours to schedule your free first practice.');
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
