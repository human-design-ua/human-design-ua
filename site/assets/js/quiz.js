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
  // Personalize headings with name
  var name = quizData.name || '';
  if (name && stepNum > 1) {
    var heading = target && target.querySelector('.step-question');
    if (heading && !heading.dataset.originalText) {
      heading.dataset.originalText = heading.textContent;
    }
    if (heading && heading.dataset.originalText) {
      heading.textContent = name + ', ' + heading.dataset.originalText.replace(/^[^,]+,\s*/, '').toLowerCase();
    }
  }
  currentStep = stepNum || currentStep;
  updateProgress(currentStep);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function goToPricing() {
  if (typeof trackEvent === 'function') trackEvent('quiz_completed', quizData);

  // Step 1: Processing screen
  showProcessingScreen(function() {
    // Step 2: Bridge result screen
    showBridgeScreen(function() {
      // Step 3: Pricing
      document.querySelectorAll('.quiz-step').forEach(function(s) { s.classList.remove('active'); });
      var pricing = document.getElementById('stepPricing');
      if (pricing) pricing.classList.add('active');
      if (!quizData.plan) selectPlan('full');
      updateProgress(totalSteps);
      // Dynamic pricing subtitle
      var subs = {
        career_decisions: 'У твоїй карті: чому рішення в кар\'єрі даються так важко — і як твій тип це вирішує',
        career_fatigue:   'Чому ти виснажуєшся на роботі — і де твій справжній джерело енергії',
        career_purpose:   'Де твоє призначення насправді — і чому нинішній шлях може бути не твоїм',
        career_people:    'Як твій тип взаємодіє в команді — і де твоя природна роль',
        relationships_decisions: 'Як твій тип приймає рішення у стосунках — і чому інші не розуміють тебе',
        relationships_fatigue:   'Чому стосунки виснажують — і які люди дають тобі енергію',
        relationships_purpose:   'Яку роль ти граєш у стосунках — і де ти зраджуєш себе',
        relationships_people:    'Чому тебе тягне до одних людей і відштовхує від інших — відповідь у карті',
        energy_decisions:  'Як твій тип керує енергією — і чому стандартні поради не працюють',
        energy_fatigue:    'Чому ти завжди втомлена — і що бодиграф каже про твій природний ритм',
        energy_purpose:    'Де ти витрачаєш енергію на чуже — і як знайти своє',
        energy_people:     'Які люди забирають твою енергію — і як захиститись без почуття провини',
        self_decisions:    'Як твій тип приймає вірні рішення — і чому голос голови часто обманює',
        self_fatigue:      'Чому ти не впізнаєш себе — і що твій дизайн каже про твою справжню природу',
        self_purpose:      'Де ти справді на своєму місці — відповідь закодована в карті народження',
        self_people:       'Як ти взаємодієш зі світом — і де втрачаєш себе заради інших',
      };
      var key = (quizData.lifeArea || 'career') + '_' + (quizData.challenge || 'decisions');
      var pricingDesc = document.getElementById('pricingDynamicDesc');
      if (pricingDesc) pricingDesc.textContent = subs[key] || subs['self_purpose'];
      window.scrollTo({ top: 0, behavior: 'smooth' });
      history.pushState({ hd_pricing: true }, '', '#pricing');
    });
  });
}

function showProcessingScreen(callback) {
  var screen = document.getElementById('processingScreen');
  if (!screen) { callback(); return; }

  document.querySelectorAll('.quiz-step').forEach(function(s) { s.classList.remove('active'); });
  screen.classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });

  var steps = [
    'Аналізуємо дату народження...',
    'Розраховуємо планетарні позиції...',
    'Визначаємо активовані ворота...',
    'Будуємо твій бодиграф...',
    'Результат готовий!'
  ];
  var fill = document.getElementById('processingFill');
  var text = document.getElementById('processingText');
  var idx = 0;

  var interval = setInterval(function() {
    if (idx < steps.length) {
      if (text) text.textContent = steps[idx];
      if (fill) fill.style.width = ((idx + 1) / steps.length * 100) + '%';
      idx++;
    } else {
      clearInterval(interval);
      setTimeout(function() {
        screen.classList.remove('active');
        callback();
      }, 400);
    }
  }, 500);
}

function showBridgeScreen(callback) {
  var screen = document.getElementById('bridgeScreen');
  if (!screen) { callback(); return; }

  // Determine type based on birth month (simplified calculation)
  var types = [
    { type: 'Генератор', pct: '37', desc: 'Твоя сила — відгук і наполегливість.' },
    { type: 'Маніфестуючий Генератор', pct: '33', desc: 'Швидкість і багатозадачність — твоя природа.' },
    { type: 'Проектор', pct: '21', desc: 'Твій дар — бачити систему і людей наскрізь.' },
    { type: 'Маніфестор', pct: '9', desc: 'Ти народжена ініціювати і змінювати світ.' },
  ];
  var bdate = quizData.birthDate || '';
  var month = bdate ? parseInt(bdate.split('-')[1]) || 1 : 1;
  var tidx = [0,0,0,1,1,1,2,2,2,3,0,1][month - 1] || 0;
  var t = types[tidx];

  var name = quizData.name || '';
  var nameEl = document.getElementById('bridgeName');
  var typeEl = document.getElementById('bridgeType');
  var pctEl  = document.getElementById('bridgePct');
  var descEl = document.getElementById('bridgeDesc');

  if (nameEl) nameEl.textContent = name ? name + ', твій тип визначено' : 'Твій тип визначено';
  if (typeEl) typeEl.textContent = t.type;
  if (pctEl)  pctEl.textContent = 'Лише ' + t.pct + '% людей мають цей дизайн';
  if (descEl) descEl.textContent = t.desc;

  document.querySelectorAll('.quiz-step').forEach(function(s) { s.classList.remove('active'); });
  screen.classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Auto-proceed after 3.5 sec OR on button click
  var btn = document.getElementById('bridgeBtn');
  if (btn) btn.onclick = function() { screen.classList.remove('active'); callback(); };
  setTimeout(function() { screen.classList.remove('active'); callback(); }, 3500);
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
  // Auto-advance on choice steps
  var choiceSteps = {lifeArea: 6, challenge: 7};
  if (choiceSteps[field] !== undefined) {
    setTimeout(function() { nextStep(choiceSteps[field]); }, 400);
  }
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
      if (!getVal('birthTime')) {
        // Allow skip — use 12:00 as default
        var timeInput = document.getElementById('birthTime');
        if (timeInput) timeInput.value = '12:00';
        // Show note
        var skipNote = document.getElementById('birthTimeSkipNote');
        if (skipNote) skipNote.style.display = 'block';
      }
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



// ── Order Bump ─────────────────────────────────────────────
function toggleOrderBump(checked) {
  const display = document.getElementById('quizPriceDisplay');
  const payBtn  = document.getElementById('payBtn');
  const bump    = document.getElementById('orderBump');

  if (checked) {
    // Upgrade to full
    selectPlan('full');
    if (display) display.textContent = '799';
    if (bump) bump.classList.add('order-bump--active');
    if (payBtn) payBtn.style.background = 'linear-gradient(135deg,#D4A830,#E8C55A)';
  } else {
    // Stay basic
    selectPlan('basic');
    if (display) display.textContent = '399';
    if (bump) bump.classList.remove('order-bump--active');
    if (payBtn) payBtn.style.background = '';
  }
}

// Auto-select basic when pricing step shown
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

// Downsell bump toggle
function toggleDownsellBump() {
  const check = document.getElementById('downsellBumpCheck');
  const bump  = document.getElementById('downsellBump');
  const cta   = document.getElementById('downsellCTA');
  if (!check || !cta) return;
  check.checked = !check.checked;
  if (check.checked) {
    bump.style.borderColor  = 'rgba(212,168,48,0.9)';
    bump.style.background   = 'rgba(212,168,48,0.08)';
    cta.textContent = 'Отримати повну розшифровку за 799 грн →';
    cta.style.background = 'linear-gradient(135deg,#D4A830,#E8C55A)';
  } else {
    bump.style.borderColor  = 'rgba(212,168,48,0.5)';
    bump.style.background   = 'transparent';
    cta.textContent = 'Отримати базову за 399 грн →';
    cta.style.background = 'var(--gold,#D4A830)';
  }
}

function submitDownsell() {
  const check = document.getElementById('downsellBumpCheck');
  const isFull = check && check.checked;
  closeDownsell();
  selectPlan(isFull ? 'full' : 'basic');
  const consent = document.getElementById('consent');
  if (consent && !consent.checked) consent.checked = true;
  setTimeout(() => submitPayment(), 200);
}

function selectDownsellBasic() {
  submitDownsell(); // backward compat
}

// Close modal on backdrop click
document.addEventListener('click', function(e) {
  const modal = document.getElementById('downsellModal');
  if (modal && e.target === modal) closeDownsell();
});
