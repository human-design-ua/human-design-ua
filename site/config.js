// Human Design — Environment Configuration
// Detects dev vs prod from hostname at runtime (no build step required)
// Replace placeholder values with real keys before deploy

(function () {
  var ENVS = {
    dev: {
      name: 'development',
      makeWebhookUrl: 'https://hook.eu1.make.com/REPLACE_DEV_WEBHOOK',
      supabaseUrl:    'https://REPLACE.supabase.co',
      supabaseAnonKey:'REPLACE_DEV_ANON_KEY',
      liqpayPublicKey:'REPLACE_DEV_LIQPAY_PUBLIC',
      liqpayMode:     'sandbox',
      ga4Id:          '',
      pixelId:        '',
      debug:          true,
    },
    prod: {
      name: 'production',
      makeWebhookUrl: 'https://hook.eu1.make.com/REPLACE_PROD_WEBHOOK',
      supabaseUrl:    'https://REPLACE.supabase.co',
      supabaseAnonKey:'REPLACE_PROD_ANON_KEY',
      liqpayPublicKey:'REPLACE_PROD_LIQPAY_PUBLIC',
      liqpayMode:     'production',
      ga4Id:          'G-XXXXXXXXXX',
      pixelId:        'XXXXXXXXXXXXXXX',
      debug:          false,
    }
  };

  // Hosts treated as dev environment
  var DEV_HOSTS    = ['localhost', '127.0.0.1'];
  var DEV_PATTERNS = ['deploy-preview--', 'branch-deploy--'];

  function detectEnv() {
    var host = window.location.hostname;
    // file:// protocol (opening HTML directly) → always dev
    if (!host || host === '') return 'dev';
    if (DEV_HOSTS.indexOf(host) !== -1) return 'dev';
    for (var i = 0; i < DEV_PATTERNS.length; i++) {
      if (host.indexOf(DEV_PATTERNS[i]) !== -1) return 'dev';
    }
    return 'prod';
  }

  window.HD_ENV    = detectEnv();
  window.HD_CONFIG = ENVS[window.HD_ENV];

  if (window.HD_CONFIG.debug) {
    console.log('[HD] env:', window.HD_ENV, window.HD_CONFIG);
  }
})();
