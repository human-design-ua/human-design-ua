// Human Design — Analytics Module (GA4 + Meta Pixel)
// Replace IDs below with your actual tracking IDs

const GA4_ID    = 'G-XXXXXXXXXX';   // Replace with your GA4 Measurement ID
const PIXEL_ID  = 'XXXXXXXXXXXXXXX'; // Replace with your Meta Pixel ID

// ── Google Analytics 4 ────────────────────────────────────
(function loadGA4() {
  if (!GA4_ID || GA4_ID === 'G-XXXXXXXXXX') return;
  const s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  window.gtag = function() { dataLayer.push(arguments); };
  gtag('js', new Date());
  gtag('config', GA4_ID, { send_page_view: true });
})();

// ── Meta Pixel ─────────────────────────────────────────────
(function loadPixel() {
  if (!PIXEL_ID || PIXEL_ID === 'XXXXXXXXXXXXXXX') return;
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window,document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', PIXEL_ID);
  fbq('track', 'PageView');
})();

// ── Unified event tracker ──────────────────────────────────
function trackEvent(eventName, params) {
  params = params || {};

  // GA4
  if (typeof gtag === 'function') {
    gtag('event', eventName, params);
  }

  // Meta Pixel — map to standard events
  if (typeof fbq === 'function') {
    switch (eventName) {
      case 'quiz_started':
        fbq('track', 'Lead');
        break;
      case 'quiz_completed':
        fbq('track', 'CompleteRegistration');
        break;
      case 'purchase':
        fbq('track', 'Purchase', {
          currency: 'UAH',
          value: params.value || 399,
        });
        break;
      case 'upsell_clicked':
        fbq('track', 'InitiateCheckout', {
          currency: 'UAH',
          value: 400,
        });
        break;
      default:
        fbq('trackCustom', eventName, params);
    }
  }
}

// ── Auto-track quiz option clicks ─────────────────────────
document.addEventListener('click', (e) => {
  const option = e.target.closest('.quiz-option');
  if (option) {
    trackEvent('quiz_option_selected', {
      option_text: option.textContent.trim().slice(0, 50),
    });
  }
  const planCard = e.target.closest('.plan-card');
  if (planCard) {
    const plan = planCard.id === 'planFull' ? 'full' : 'basic';
    trackEvent('plan_selected', { plan });
  }
});
