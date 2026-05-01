/* Swimnexar — main.js */

/* ── Google Forms submission ── */
const _EXP = {
  'none':        "Beginner ( Can't swim independently )",
  'strokes':     'Can swim freestyle & breaststroke',
  'competitive': 'Competitive swimmer',
  'waterpolo':   'Has played water polo before',
};

const _GF = {
  waterpolo: {
    url: 'https://docs.google.com/forms/d/e/1FAIpQLSc2VkPrjFW_vxi1wY391Xwt1gBcoX6M6r9lEobDLSumkBNFLg/formResponse',
    map: d => ({
      'entry.2092238618': d.parentName  || '',
      'entry.1556369182': d.email       || '',
      'entry.479301265':  d.phone       || '',
      'entry.588393791':  d.childName   || '',
      'entry.1753222212': _EXP[d.experience] || d.experience || '',
      'entry.1795103341': d.waiver ? 'By signing, you agree to "Terms and Conditions"' : '',
    })
  },
  swimteam: {
    url: 'https://docs.google.com/forms/d/e/1FAIpQLSeQ1dlFbdOW5UnvCg9qh77FWpoRUl38vjPCuTacGK_iUq2pMA/formResponse',
    map: d => ({
      'entry.1556369182': d.email       || '',
      'entry.2092238618': d.parentName  || '',
      'entry.479301265':  d.email       || '',
      'entry.1753222212': d.phone       || '',
      'entry.588393791':  d.childName   || '',
      'entry.361570756':  _EXP[d.experience] || d.experience || '',
      'entry.2022420186': d.waiver ? 'By signing, you agree to "Terms and Conditions"' : '',
    })
  }
};

function submitToGoogleForms(data) {
  const key    = window.location.pathname.includes('swimteam') ? 'swimteam' : 'waterpolo';
  const gf     = _GF[key];
  const mapped = gf.map(data);

  // Hidden iframe so page doesn't redirect
  const iframe = document.createElement('iframe');
  iframe.name  = 'gf_' + Date.now();
  iframe.style.display = 'none';
  document.body.appendChild(iframe);

  // Hidden form targeting the iframe
  const hf    = document.createElement('form');
  hf.method   = 'POST';
  hf.action   = gf.url;
  hf.target   = iframe.name;
  hf.style.display = 'none';

  Object.entries(mapped).forEach(([name, value]) => {
    const inp = document.createElement('input');
    inp.type  = 'hidden';
    inp.name  = name;
    inp.value = value;
    hf.appendChild(inp);
  });

  document.body.appendChild(hf);
  hf.submit();

  // Clean up after Google Forms processes it
  setTimeout(() => {
    document.body.removeChild(iframe);
    document.body.removeChild(hf);
  }, 5000);
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
    // include waiver checked state (checkbox not in FormData when unchecked)
    rawData.waiver = form.querySelector('[name="waiver"]')?.checked || false;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending…';
    hideMsg();

    try {
      submitToGoogleForms(rawData);
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
