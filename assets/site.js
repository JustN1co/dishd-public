/* dishd. — shared UI script: language switching and mobile nav */
(function () {
  'use strict';

  var STORAGE_KEY = 'dishd_lang';
  var html = document.documentElement;
  var header = document.querySelector('.site-header');
  var nav = document.getElementById('site-nav');
  var navToggle = document.querySelector('.nav-toggle');
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

  /* ---------- Mobile navigation ---------- */

  function closeNav() {
    if (!nav || !header) return;
    nav.classList.remove('is-open');
    header.classList.remove('is-open');
    if (navToggle) navToggle.setAttribute('aria-expanded', 'false');
  }

  function openNav() {
    if (!nav || !header) return;
    nav.classList.add('is-open');
    header.classList.add('is-open');
    if (navToggle) navToggle.setAttribute('aria-expanded', 'true');
  }

  if (navToggle && nav && header) {
    navToggle.addEventListener('click', function () {
      if (nav.classList.contains('is-open')) {
        closeNav();
      } else {
        openNav();
      }
    });

    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) closeNav();
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeNav();
    });

    document.addEventListener('click', function (event) {
      if (!header.contains(event.target)) closeNav();
    });

    var desktop = window.matchMedia('(min-width: 921px)');
    var onChange = function (event) {
      if (event.matches) closeNav();
    };
    if (desktop.addEventListener) {
      desktop.addEventListener('change', onChange);
    } else if (desktop.addListener) {
      desktop.addListener(onChange);
    }
  }

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
