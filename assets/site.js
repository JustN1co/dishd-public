/* dishd. — shared UI script: language switcher */
(function () {
  'use strict';

  var STORAGE_KEY = 'dishd_lang';
  var html = document.documentElement;
  var langButtons = Array.prototype.slice.call(document.querySelectorAll('.lang-btn'));
  var textNodes = Array.prototype.slice.call(document.querySelectorAll('[data-en][data-pl]'));
  var ariaNodes = Array.prototype.slice.call(document.querySelectorAll('[data-aria-en][data-aria-pl]'));
  var description = document.querySelector('meta[name="description"]');

  function readStoredLanguage() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function storeLanguage(lang) {
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (e) {
      /* storage may be unavailable (private mode) — language still applies */
    }
  }

  function setLanguage(lang) {
    if (lang !== 'en' && lang !== 'pl') return;
    var key = lang === 'pl' ? 'Pl' : 'En';

    html.lang = lang;

    textNodes.forEach(function (el) {
      var value = el.getAttribute('data-' + lang);
      if (typeof value === 'string') el.innerHTML = value;
    });

    ariaNodes.forEach(function (el) {
      var value = el.getAttribute('data-aria-' + lang);
      if (typeof value === 'string') el.setAttribute('aria-label', value);
    });

    if (document.body) {
      var title = document.body.getAttribute('data-title-' + lang);
      if (title) document.title = title;
      var desc = document.body.getAttribute('data-desc-' + lang);
      if (desc && description) description.setAttribute('content', desc);
    }

    langButtons.forEach(function (btn) {
      var active = btn.getAttribute('data-lang') === lang;
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });

    storeLanguage(lang);
  }

  langButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      setLanguage(btn.getAttribute('data-lang'));
    });
  });

  /* ---------- Initial language ---------- */

  (function init() {
    var params = new URLSearchParams(window.location.search);
    var urlLang = params.get('lang');
    if (urlLang === 'pl' || urlLang === 'en') {
      setLanguage(urlLang);
      return;
    }
    var stored = readStoredLanguage();
    if (stored === 'pl' || stored === 'en') {
      setLanguage(stored);
    }
  })();
})();
