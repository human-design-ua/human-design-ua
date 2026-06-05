// Human Design Quiz — Step Navigation & Validation

const quizData = {};
let currentStep = 1;
const totalSteps = 7;

// ── Restore from localStorage ──────────────────────────────
(function restoreProgress() {
  const saved = localStorage.getItem('hd_quiz_data');
  if (saved) {
    try {
      Object.assign(quizData, JSON.parse(saved));
      // Restore text inputs
      if (quizData.name)       setValue('name', quizData.name);
      if (quizData.email)      setValue('email', quizData.email);
      if (quizData.birthDate)  setValue('birthDate', quizData.birthDate);
      if (quizData.birthTime)  setValue('birthTime', quizData.birthTime);
      if (quizData.birthPlace) setValue('birthPlace', quizData.birthPlace);
    } catch (e) { /* ignore */ }
  }
  // Set max date for birthDate to today
  const dateInput = document.getElementById('birthDate');
  if (dateInput) dateInput.max = new Date().toISOString().split('T')[0];

  // Pre-select plan from URL param
  const urlPlan = new URLSearchParams(window.location.search).get('plan');
  if (urlPlan === 'full' || urlPlan === 'basic') {
    quizData.plan = urlPlan;
  }
})();

function setValue(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function saveProgress() {
  localStorage.setItem('hd_quiz_data', JSON.stringify(quizData));
}

// ── Step Navigation ────────────────────────────────────────
function nextStep(stepNum) {
  if (!validateStep(stepNum)) return;
  collectStep(stepNum);
  saveProgress();
  trackStep(stepNum);

  const nextNum = stepNum + 1;
  if (nextNum > totalSteps) {
    goToPricing();
    return;
  }
  showStep('step' + nextNum, nextNum);
}

function prevStep(stepNum) {
  const prevNum = stepNum - 1;
  if (prevNum < 1) return;
  showStep('step' + prevNum, prevNum);
}

function showStep(stepId, stepNum) {
  document.querySelectorAll('.quiz-step').forEach(s => s.classList.remove('active'));
  const target = document.getElementById(stepId);
  if (target) target.classList.add('active');
  currentStep = stepNum || currentStep;
  updateProgress(currentStep);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function goToPricing() {
  showStep('stepPricing', totalSteps);
  // Auto-select full plan (single offer)
  if (!quizData.plan) {
    selectPlan('full');
  }
  if (typeof trackEvent === 'function') trackEvent('quiz_completed', quizData);
  // Push history state so browser back / iOS swipe triggers popstate
  history.pushState({ hd_pricing: true }, '', '#pricing');
}

// Intercept browser back button & iOS swipe-back
window.addEventListener('popstate', function(e) {
  var pricingStep = document.getElementById('stepPricing');
  var isOnPricing = pricingStep && pricingStep.classList.contains('active');
  if (isOnPricing) {
    // Show downsell instead of navigating away
    showDownsell();
    // Push state again to keep the page from navigating
    history.pushState({ hd_pricing: true }, '', '#pricing');
  }
});

function updateProgress(step) {
  const pct = Math.round((step / totalSteps) * 100);
  const fill = document.getElementById('progressFill');
  const text = document.getElementById('progressText');
  if (fill) fill.style.width = pct + '%';
  if (text) text.textContent = step <= totalSteps ? step + ' / ' + totalSteps : '✓';
  const bar = document.querySelector('.quiz-progress-bar');
  if (bar) bar.setAttribute('aria-valuenow', step);
}

// ── Collect data from each step ───────────────────────────
function collectStep(stepNum) {
  switch (stepNum) {
    case 1: quizData.name      = document.getElementById('name')?.value.trim(); break;
    case 2:
      quizData.email = document.getElementById('email')?.value.trim().toLowerCase();
      localStorage.setItem('hd_email', quizData.email);
      break;
    case 3: quizData.birthDate  = document.getElementById('birthDate')?.value; break;
    case 4: quizData.birthTime  = document.getElementById('birthTime')?.value; break;
    case 5: quizData.birthPlace = document.getElementById('birthPlace')?.value.trim(); break;
    // Steps 6-9 use selectOption()
  }
}

// ── Option selection ───────────────────────────────────────
function selectOption(field, value, el) {
  // Deselect siblings
  el.closest('.quiz-options').querySelectorAll('.quiz-option').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  quizData[field] = value;
  hideError(field + 'Error');
  saveProgress();
}

// ── Plan selection ────────────────────────────────────────
function selectPlan(plan) {
  quizData.plan = plan;
  localStorage.setItem('hd_plan', plan);
  const basic = document.getElementById('planBasic');
  const full  = document.getElementById('planFull');
  if (basic) basic.classList.toggle('selected', plan === 'basic');
  if (full)  full.classList.toggle('selected', plan === 'full');
  hideError('planError');
}

// ── Validation ─────────────────────────────────────────────
function validateStep(stepNum) {
  let valid = true;
  switch (stepNum) {
    case 1:
      if (!getVal('name')) { showError('nameError'); valid = false; }
      break;
    case 2:
      if (!isValidEmail(getVal('email'))) { showError('emailError'); valid = false; }
      break;
    case 3:
      if (!isValidBirthDate(getVal('birthDate'))) { showError('birthDateError'); valid = false; }
      break;
    case 4:
      if (!getVal('birthTime')) { showError('birthTimeError'); valid = false; }
      break;
    case 5:
      if (!getVal('birthPlace') || getVal('birthPlace').length < 2) { showError('birthPlaceError'); valid = false; }
      break;
    case 6:
      if (!quizData.lifeArea) { showError('lifeAreaError'); valid = false; }
      break;
    case 7:
      if (!quizData.challenge) { showError('challengeError'); valid = false; }
      break;
    // step 8 removed
  }
  return valid;
}

function validatePricing() {
  let valid = true;
  if (!quizData.plan) { showError('planError'); valid = false; }
  if (!document.getElementById('consent')?.checked) { showError('consentError'); valid = false; }
  return valid;
}

// ── Helper validators ─────────────────────────────────────
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email || '');
}

function isValidBirthDate(dateStr) {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const now = new Date();
  return d instanceof Date && !isNaN(d) && d < now && d.getFullYear() > 1900;
}

function getVal(id) {
  return document.getElementById(id)?.value?.trim() || '';
}

function showError(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('visible');
}

function hideError(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('visible');
}

// ── Submit payment ─────────────────────────────────────────
function submitPayment() {
  // DEV: auto-select basic plan and consent if not done
  if (window.HD_ENV === 'dev') {
    if (!quizData.plan) {
      selectPlan('basic');
      console.log('[DEV] Auto-selected basic plan');
    }
    const consent = document.getElementById('consent');
    if (consent && !consent.checked) {
      consent.checked = true;
      console.log('[DEV] Auto-checked consent');
    }
  }

  if (!validatePricing()) {
    console.warn('[DEV] validatePricing failed:', {
      plan: quizData.plan,
      consent: document.getElementById('consent')?.checked
    });
    return;
  }
  if (typeof initiatePayment === 'function') {
    initiatePayment(quizData);
  } else {
    console.error('payment.js not loaded');
  }
}

// ── Analytics helper ─────────────────────────────────────
function trackStep(stepNum) {
  if (stepNum === 1 && typeof trackEvent === 'function') {
    trackEvent('quiz_started');
  }
}

// ── Keyboard support ─────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && document.activeElement?.tagName !== 'BUTTON') {
    const activeStep = document.querySelector('.quiz-step.active');
    if (activeStep && activeStep.id.startsWith('step') && activeStep.id !== 'stepPricing') {
      const stepNum = parseInt(activeStep.id.replace('step', ''));
      if (!isNaN(stepNum)) nextStep(stepNum);
    }
  }
});

// ── Init ─────────────────────────────────────────────────
if (typeof trackEvent === 'function') trackEvent('page_view', { page: 'quiz' });


// ── Wire pricing back button after DOM ready ─────────────
(function initPricingBack() {
  function wire() {
    var btn = document.getElementById('pricingBackBtn');
    if (btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var m = document.getElementById('downsellModal');
        if (m) {
          m.style.cssText = m.style.cssText.replace('display:none','display:flex');
          m.style.display = 'flex';
          document.body.style.overflow = 'hidden';
        }
      });
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
// ── Downsell modal ─────────────────────────────────────────
function showDownsell() {
  const m = document.getElementById('downsellModal');
  if (!m) return;
  m.style.cssText = 'display:flex!important;position:fixed;inset:0;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.85);z-index:99999;align-items:center;justify-content:center;';
  document.body.style.overflow = 'hidden';
}

function closeDownsell() {
  const m = document.getElementById('downsellModal');
  if (!m) return;
  m.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:99999;align-items:center;justify-content:center;';
  document.body.style.overflow = '';
  // Push state again so next back will trigger downsell again
  history.pushState({ hd_pricing: true }, '', '#pricing');
}

function selectDownsellBasic() {
  closeDownsell();
  selectPlan('basic');
  const consent = document.getElementById('consent');
  if (consent && !consent.checked) consent.checked = true;
  // Small delay then submit
  setTimeout(() => submitPayment(), 200);
}

// Close modal on backdrop click
document.addEventListener('click', function(e) {
  const modal = document.getElementById('downsellModal');
  if (modal && e.target === modal) closeDownsell();
});
