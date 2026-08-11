/* Portfolio interactions — vanilla, no dependencies.
   Everything here is progressive enhancement: with JS off, the CSS
   `.no-js` rule shows all content and the page still works. */

(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- 1. Scroll reveal (staggered) ----------------------------------- */

  var revealables = document.querySelectorAll('.reveal');

  if (reduced || !('IntersectionObserver' in window)) {
    revealables.forEach(function (el) { el.classList.add('is-visible'); });
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);   // reveal once, then stop watching
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    revealables.forEach(function (el) { observer.observe(el); });

    /* Grid children get a wave stagger unless they set their own delay. */
    document.querySelectorAll('.work-grid').forEach(function (grid) {
      Array.prototype.forEach.call(grid.children, function (child, i) {
        if (!child.style.getPropertyValue('--reveal-delay')) {
          child.style.setProperty('--reveal-delay', (i % 2) * 60 + Math.floor(i / 2) * 40 + 'ms');
        }
      });
    });
  }

  /* ---- 2. Header border appears once you leave the top ---------------- */

  var header = document.querySelector('.site-header');
  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      header.setAttribute('data-scrolled', window.scrollY > 8 ? 'true' : 'false');
      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- 3. Nav highlights the section you're reading -------------------- */

  var links = {};
  document.querySelectorAll('.site-nav a[href^="#"]').forEach(function (a) {
    links[a.getAttribute('href').slice(1)] = a;
  });

  var sections = Object.keys(links)
    .map(function (id) { return document.getElementById(id); })
    .filter(Boolean);

  if (sections.length && 'IntersectionObserver' in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var link = links[entry.target.id];
        if (!link || link.classList.contains('nav-cta')) return;
        if (entry.isIntersecting) {
          link.setAttribute('aria-current', 'true');
        } else {
          link.removeAttribute('aria-current');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });

    sections.forEach(function (s) { spy.observe(s); });
  }

  /* ---- 3b. Mobile menu ------------------------------------------------ */

  var navBtn = document.getElementById('nav-toggle');
  var siteHeader = document.querySelector('.site-header');

  if (navBtn && siteHeader) {
    var setMenu = function (open) {
      siteHeader.classList.toggle('nav-open', open);
      navBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      navBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    };

    navBtn.addEventListener('click', function () {
      setMenu(!siteHeader.classList.contains('nav-open'));
    });

    // Following a link should close it, or the menu covers where you landed.
    document.querySelectorAll('.site-nav a').forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });

    document.addEventListener('click', function (e) {
      if (!siteHeader.contains(e.target)) setMenu(false);
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && siteHeader.classList.contains('nav-open')) {
        setMenu(false);
        navBtn.focus();
      }
    });

    // Resizing past the breakpoint leaves the menu class stranded otherwise.
    window.matchMedia('(max-width: 40rem)').addEventListener('change', function (e) {
      if (!e.matches) setMenu(false);
    });
  }

  /* ---- 4. Theme toggle ------------------------------------------------ */

  var toggle = document.getElementById('theme-toggle');
  var systemDark = window.matchMedia('(prefers-color-scheme: dark)');

  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') ||
           (systemDark.matches ? 'dark' : 'light');
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (toggle) {
      toggle.setAttribute('aria-label',
        theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    }
    // Keep the browser UI (mobile address bar) in step with the page.
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#0F172A' : '#F6F8FB');
  }

  if (toggle) {
    applyTheme(currentTheme());

    toggle.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem('theme', next); } catch (e) { /* private mode */ }
    });
  }

  // Follow the OS only while the visitor hasn't made a choice of their own.
  systemDark.addEventListener('change', function (e) {
    var saved = null;
    try { saved = localStorage.getItem('theme'); } catch (err) { /* private mode */ }
    if (!saved) applyTheme(e.matches ? 'dark' : 'light');
  });

  /* ---- 5. Video player ------------------------------------------------
     Two source kinds: a file in this repo plays in <video>; anything remote
     (Google Drive, YouTube) has to go through an <iframe>, because those
     hosts don't serve a raw file that <video> can stream.               */

  var lightbox = document.getElementById('video-lightbox');

  if (lightbox && typeof lightbox.showModal === 'function') {
    var vid = lightbox.querySelector('.lightbox-video');
    var frame = lightbox.querySelector('.lightbox-frame');
    var vidError = lightbox.querySelector('.lightbox-error');
    var closeBtn = lightbox.querySelector('.lightbox-close');
    var lastFocus = null;

    var triggers = Array.prototype.slice.call(document.querySelectorAll('[data-video]'));

    function isRemote(src) { return /^https?:/i.test(src); }

    /* Accepts any shape of share link and returns the embeddable one. */
    function embedUrl(src) {
      if (/drive\.google\.com/i.test(src)) {
        var id = (src.match(/\/file\/d\/([^/?#]+)/) || src.match(/[?&]id=([^&#]+)/) || [])[1];
        return id ? 'https://drive.google.com/file/d/' + id + '/preview' : src;
      }
      var yt = src.match(/(?:youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{6,})/i);
      if (yt) return 'https://www.youtube.com/embed/' + yt[1] + '?rel=0';
      return src;
    }

    function openVideo(src, title) {
      lastFocus = document.activeElement;
      vidError.hidden = true;
      lightbox.setAttribute('aria-label', title || 'Video player');

      if (isRemote(src)) {
        vid.hidden = true;
        frame.hidden = false;
        frame.setAttribute('title', title || 'Video');
        frame.src = embedUrl(src);
      } else {
        frame.hidden = true;
        frame.removeAttribute('src');
        vid.hidden = false;
        if (vid.getAttribute('src') !== src) vid.setAttribute('src', src);
      }

      lightbox.showModal();

      if (!isRemote(src)) {
        var playing = vid.play();
        if (playing && playing.catch) playing.catch(function () { /* autoplay blocked — controls are there */ });
      }
    }

    function stopPlayback() {
      vid.pause();
      vid.currentTime = 0;
      // An iframe has no pause API, so the src has to go or Drive keeps playing
      // with the dialog shut.
      if (frame.getAttribute('src')) frame.removeAttribute('src');
    }

    function closeVideo() {
      stopPlayback();
      if (lightbox.open) lightbox.close();
    }

    triggers.forEach(function (t) {
      t.addEventListener('click', function () {
        openVideo(t.dataset.video, t.dataset.videoTitle);
      });
    });

    closeBtn.addEventListener('click', closeVideo);

    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox) closeVideo();
    });

    lightbox.addEventListener('close', function () {
      stopPlayback();
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    });

    /* Clicking into a cross-origin player hands focus to Google's document,
       and Esc goes there instead of closing this dialog. Take focus back as
       soon as the pointer returns to our own chrome, so Esc works again. */
    lightbox.addEventListener('mousemove', function (e) {
      if (e.target !== frame && document.activeElement === frame) closeBtn.focus();
    });

    vid.addEventListener('error', function () {
      vid.hidden = true;
      vidError.hidden = false;
    });

    /* Local files are probed so a missing one shows no button at all. Remote
       hosts can't be probed (CORS), so those triggers just show. */
    triggers.forEach(function (t) {
      var src = t.dataset.video;
      if (!src) return;
      if (isRemote(src) || location.protocol === 'file:' || !window.fetch) {
        t.hidden = false;
        return;
      }
      fetch(src, { method: 'HEAD' })
        .then(function (r) { if (r.ok) t.hidden = false; })
        .catch(function () { /* absent — leave the trigger hidden */ });
    });
  }

  /* ---- 6. Clamp long descriptions on small screens -------------------- */

  var CLAMP_AT = window.matchMedia('(max-width: 46rem)');

  function buildToggle(card) {
    var desc = card.querySelector('.project-desc');
    if (!desc || card.querySelector('.desc-toggle')) return;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'desc-toggle';
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = '<span>Read more</span>' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="m6 9 6 6 6-6"/></svg>';

    var name = (card.querySelector('h3') || {}).textContent || 'this project';
    btn.setAttribute('aria-label', 'Read more about ' + name.trim());

    btn.addEventListener('click', function () {
      var open = card.classList.toggle('is-expanded');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.firstChild.textContent = open ? 'Show less' : 'Read more';
      btn.setAttribute('aria-label',
        (open ? 'Show less about ' : 'Read more about ') + name.trim());
    });

    desc.insertAdjacentElement('afterend', btn);
  }

  /* Only clamp cards whose text actually overflows three lines — a short
     description shouldn't grow a button that does nothing. */
  function applyClamps() {
    document.querySelectorAll('#work .project').forEach(function (card) {
      if (!CLAMP_AT.matches) { card.classList.remove('has-clamp', 'is-expanded'); return; }
      buildToggle(card);
      var desc = card.querySelector('.project-desc');
      if (!desc) return;
      card.classList.add('has-clamp');
      var overflows = desc.scrollHeight > desc.clientHeight + 2;
      var manyTags = card.querySelectorAll('.tags li').length > 3;
      if (!overflows && !manyTags) card.classList.remove('has-clamp');
    });
  }

  applyClamps();
  CLAMP_AT.addEventListener('change', applyClamps);

  /* ---- 7. Hero underline draws itself in on load ---------------------- */

  var accent = document.querySelector('.hero h1 .accent');
  if (accent && !reduced) {
    requestAnimationFrame(function () { accent.style.setProperty('--u', '100%'); });
  } else if (accent) {
    accent.style.setProperty('--u', '100%');
  }
})();
