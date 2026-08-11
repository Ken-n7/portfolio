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

  /* ---- 6. Project detail overlay --------------------------------------
     The card is the trigger; its .project-detail block is *moved* into the
     dialog on open and moved home on close. Moving rather than cloning keeps
     one copy of every node, so the video trigger keeps the listener that
     section 5 already gave it and nothing can drift out of step.        */

  var pd = document.getElementById('project-dialog');

  if (pd && typeof pd.showModal === 'function') {
    var pdImg    = pd.querySelector('.pd-img');
    var pdVideo  = pd.querySelector('.pd-video');
    var pdShot   = pd.querySelector('.pd-shot');
    var pdSide   = pd.querySelector('.pd-side');
    var pdText   = pd.querySelector('.pd-text');
    var pdBrand  = pd.querySelector('.pd-brand');
    var pdTitle  = pd.querySelector('.pd-title');
    var pdKicker = pd.querySelector('.pd-kicker');
    var pdClose  = pd.querySelector('.pd-close');
    var borrowed = [];      // [node, itsHome] so close can always undo the move
    var opener   = null;
    var source   = null;    // the card it came from, so it can fly back
    var closing  = false;
    var currentFly = null;  // only ever one in the air

    function lend(node, into) {
      if (!node) return;
      borrowed.push([node, node.parentNode]);
      into.appendChild(node);
    }

    function returnAll() {
      borrowed.forEach(function (pair) { pair[1].appendChild(pair[0]); });
      borrowed.length = 0;
    }

    /* Not the site's Expo.out here — at a third of the way through it has
       already covered 96% of the distance, which reads as a snap rather than
       a move. This curve eases in a little before it settles, so the shot
       looks like it travels. */
    var FLY_EASE = 'cubic-bezier(0.42, 0.02, 0.18, 1)';
    var EASE = 'cubic-bezier(0.16, 1, 0.3, 1)';
    var FLY_MS = 540;

    /* The clone that travels. It starts exactly on top of the card, so the
       first frame is indistinguishable from the grid, and lands exactly on
       .pd-shot, so the last frame is indistinguishable from the overlay. */
    function fly(fromEl, toEl, sourceCard, reverse) {
      if (reduced) return null;
      var from = fromEl.getBoundingClientRect();
      var to = toEl.getBoundingClientRect();
      if (!from.width || !to.width) return null;

      // Esc pressed mid-open would otherwise leave two clones racing, and
      // whichever finished first would clear the flags out from under the other.
      if (currentFly) { currentFly.cancel(); currentFly = null; }
      pd.querySelectorAll('.pd-fly').forEach(function (el) { el.remove(); });

      var model = reverse ? toEl : fromEl;
      var img = model.querySelector('img');
      var clone = document.createElement('img');
      clone.className = 'pd-fly';
      clone.src = img.currentSrc || img.src;
      clone.alt = '';
      var cs = getComputedStyle(img);
      clone.style.objectFit = cs.objectFit;
      clone.style.objectPosition = cs.objectPosition;
      clone.style.padding = cs.padding;
      pd.appendChild(clone);
      pd.classList.add('is-flying');
      if (sourceCard) sourceCard.classList.add('is-source');

      var frame = function (r, radius) {
        return { top: r.top + 'px', left: r.left + 'px',
                 width: r.width + 'px', height: r.height + 'px', borderRadius: radius };
      };
      var anim = clone.animate([frame(from, '20px'), frame(to, '14px')],
        { duration: reverse ? FLY_MS - 90 : FLY_MS, easing: FLY_EASE, fill: 'both' });

      currentFly = anim;
      var land = function () {
        clone.remove();
        if (currentFly === anim) { currentFly = null; pd.classList.remove('is-flying'); }
      };

      /* The clone carries the card's screenshot. Where the overlay holds a
         demo instead, the thing underneath is different footage entirely, so
         the swap has to be a fade — a straight cut reads as a glitch. */
      if (!reverse && pdShot.classList.contains('is-video')) {
        anim.finished.then(function () {
          if (currentFly !== anim) return land();
          pd.classList.remove('is-flying');
          pdShot.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 220, easing: EASE });
          var out = clone.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 200, easing: EASE, fill: 'both' });
          out.finished.then(land).catch(land);
        }).catch(land);
      } else {
        anim.finished.then(land).catch(land);
      }   // .cancel() rejects; same cleanup

      return anim;
    }

    /* Everything that isn't the shot arrives just behind it, staggered, so the
       panel assembles around the picture rather than appearing all at once. */
    function revealContent() {
      if (reduced) return;
      [pdBrand, pdTitle, pdKicker, pdText, pdSide].forEach(function (el, i) {
        if (!el) return;
        el.classList.add('pd-enter');
        var a = el.animate(
          [{ opacity: 0, transform: 'translateY(14px)' }, { opacity: 1, transform: 'none' }],
          { duration: 420, delay: 180 + i * 70, easing: EASE, fill: 'both' });
        a.finished.then(function () { el.classList.remove('pd-enter'); })
                  .catch(function () { el.classList.remove('pd-enter'); });
      });
    }

    /* Closing runs the entrance backwards: the text goes first and only then
       does the shot start travelling, so the panel empties before the picture
       leaves rather than everything sliding away together. */
    function hideContent() {
      if (reduced) return Promise.resolve();
      var anims = [pdSide, pdText, pdKicker, pdTitle, pdBrand].filter(Boolean).map(function (el, i) {
        el.classList.add('pd-enter');
        return el.animate(
          [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(10px)' }],
          { duration: 165, delay: i * 38, easing: 'cubic-bezier(0.4, 0, 1, 1)', fill: 'both' });
      });
      return Promise.all(anims.map(function (a) { return a.finished.catch(function () {}); }));
    }

    /* The scrim ramps rather than snapping. On the way out it waits until the
       shot is already back in the grid, so the blur lifts off a page that is
       whole again. */
    /* showModal alone doesn't stop the page behind from scrolling, but
       overflow:hidden reclaims the scrollbar's strip and shifts the whole
       layout. Measure what locking actually cost and give it straight back as
       padding. Reads 0 wherever scrollbar-gutter or overlay scrollbars already
       hold the space, so it costs nothing there. */
    function lockScroll() {
      var before = document.documentElement.clientWidth;
      document.body.style.overflow = 'hidden';
      var gained = document.documentElement.clientWidth - before;
      if (gained > 0) document.body.style.paddingRight = gained + 'px';
    }

    function unlockScroll() {
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    }

    var CLEAR = 'rgba(0, 0, 0, 0)';
    var BLURRED = 'blur(26px) saturate(112%)';
    var scrimAnim = null;

    function scrim(on) {
      if (reduced) return Promise.resolve();
      if (scrimAnim) scrimAnim.cancel();
      var lit = getComputedStyle(pd).backgroundColor;   // resolves the live theme
      var a = { backgroundColor: lit, backdropFilter: BLURRED, webkitBackdropFilter: BLURRED };
      var b = { backgroundColor: CLEAR, backdropFilter: 'blur(0px)', webkitBackdropFilter: 'blur(0px)' };
      scrimAnim = pd.animate(on ? [b, a] : [a, b],
        { duration: on ? 360 : 290, easing: on ? EASE : 'cubic-bezier(0.33, 0, 0.5, 1)', fill: 'both' });
      return scrimAnim.finished.catch(function () {});
    }

    function openProject(card, trigger) {
      var shot   = card.querySelector('.project-shot');
      var img    = shot.querySelector('img');
      var detail = card.querySelector('.project-detail');

      opener = trigger;
      source = card;
      pd.classList.remove('is-emptied');
      pd.style.setProperty('--theme-color', card.style.getPropertyValue('--theme-color'));

      /* A project with a demo opens straight into it — the screenshot has
         already done its job on the card. */
      var demo = card.dataset.demo;
      pdVideo.hidden = !demo;
      pdImg.hidden = !!demo;
      if (demo) {
        if (card.dataset.demoPoster) pdVideo.poster = card.dataset.demoPoster;
        if (pdVideo.getAttribute('src') !== demo) pdVideo.setAttribute('src', demo);
      } else {
        pdVideo.removeAttribute('src');
      }

      pdImg.src = img.currentSrc || img.src;
      pdImg.alt = img.alt;
      pdImg.width = img.width; pdImg.height = img.height;
      // A portrait shot or an app icon has to keep its shape here too.
      pdShot.className = 'pd-shot' +
        (demo ? ' is-video' : '') +
        (!demo && shot.classList.contains('is-portrait') ? ' is-portrait' : '') +
        (!demo && shot.classList.contains('is-icon') ? ' is-icon' : '');

      pdTitle.textContent  = card.querySelector('.project-name').textContent;
      pdKicker.textContent = card.querySelector('.project-kicker').textContent;

      /* Four projects carry their own wordmark; the rest just use the title.
         Lent in like everything else, so there is one copy of it. */
      var brand = detail.querySelector('.brand');
      pd.classList.toggle('has-brand', !!brand);
      lend(brand, pdBrand);

      lend(detail.querySelector('.tags'), pdSide);
      lend(detail.querySelector('.project-links'), pdSide);
      lend(detail.querySelector('.project-desc'), pdText);

      pdText.scrollTop = 0;
      document.body.classList.add('pd-open');
      lockScroll();
      pd.showModal();
      // Measured only now — .pd-shot has no box until the dialog is laid out.
      scrim(true);
      fly(shot, pdShot, card, false);
      revealContent();
      pdClose.focus();
    }

    /* Abandon the close choreography and land immediately. */
    function snapShut() {
      closing = false;
      pd.classList.remove('is-emptied');
      if (scrimAnim) { scrimAnim.cancel(); scrimAnim = null; }
      if (currentFly) { currentFly.cancel(); currentFly = null; }
      if (pd.open) pd.close();
    }

    /* Fly it home before closing. The clone lives inside the dialog, so the
       moment the dialog leaves the top layer the clone stops being painted —
       the animation has to finish first. */
    function closeProject() {
      if (!pd.open || closing) return;
      closing = true;

      var done = function () { closing = false; if (pd.open) pd.close(); };

      hideContent().then(function () {
        if (!pd.open) return done();
        var shot = source && source.querySelector('.project-shot');
        var anim = shot ? fly(pdShot, shot, source, true) : null;
        if (!anim) return scrim(false).then(done);

        return anim.finished.catch(function () {}).then(function () {
          // The card is back in its slot before the blur starts lifting, so
          // the grid is never seen with a hole in it. Blanking the panel in
          // the same batch keeps the overlay's copy of the shot from painting
          // again at the position it opened in.
          pd.classList.add('is-emptied');
          if (source) source.classList.remove('is-source');
          return scrim(false);
        }).then(done);
      }).catch(done);
    }

    document.querySelectorAll('.project-open').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var card = btn.closest('.project');
        /* The close choreography runs about a second. Swallowing taps for that
           long feels broken, so a click mid-close cuts it short instead. */
        if (closing || pd.open) {
          snapShut();
          /* close() queues its event rather than firing it inline. Opening on
             this tick would let that event land afterwards and hand the new
             card's description and links straight back to the grid, leaving
             the overlay empty. Wait a task. */
          setTimeout(function () { openProject(card, btn); }, 0);
          return;
        }
        openProject(card, btn);
      });
    });

    pdClose.addEventListener('click', closeProject);

    /* There is no panel to click outside of any more — the dialog fills the
       screen — so treat a hit on the empty ground as a dismiss. Only the
       containers themselves count; anything inside them is content. */
    var pdGrid = pd.querySelector('.pd-grid');
    pd.addEventListener('click', function (e) {
      if (e.target === pd || e.target === pdGrid) closeProject();
    });

    /* Esc closes a dialog natively and instantly, which would skip the flight
       home. Take it over so both routes out look the same. */
    pd.addEventListener('cancel', function (e) {
      e.preventDefault();
      closeProject();
    });

    pd.addEventListener('close', function () {
      returnAll();
      document.body.classList.remove('pd-open');
      unlockScroll();
      pdImg.removeAttribute('src');
      pdVideo.pause();
      pdVideo.currentTime = 0;
      pdVideo.removeAttribute('src');
      if (currentFly) { currentFly.cancel(); currentFly = null; }
      pd.querySelectorAll('.pd-fly').forEach(function (el) { el.remove(); });
      pd.classList.remove('is-flying');
      pd.classList.remove('is-emptied');
      if (scrimAnim) { scrimAnim.cancel(); scrimAnim = null; }
      [pdBrand, pdTitle, pdKicker, pdText, pdSide].forEach(function (el) {
        if (!el) return;
        el.getAnimations().forEach(function (a) { a.cancel(); });
        el.classList.remove('pd-enter');
      });
      closing = false;
      if (source) source.classList.remove('is-source');
      source = null;
      /* preventScroll because scroll-behavior is smooth: without it, focus
         can glide the page to the card and that glide reads as a lurch right
         as the overlay disappears. The card is always still on screen anyway —
         the page was locked the whole time it was open. */
      if (opener && opener.focus) opener.focus({ preventScroll: true });
      opener = null;
    });
  }

  /* ---- 7. Logo rails: drift, swipe, drag ------------------------------
     Each rail is a scroller holding several identical copies of its set. The
     drift is a scroll offset nudged once a frame rather than a CSS transform,
     which is what lets a finger or a mouse grab it mid-flight: touch gets the
     browser's own panning and momentum for free, and only the mouse needs
     hand-rolled dragging. Whenever the offset leaves the middle band it jumps
     back by exactly one set — identical pixels, so the seam is invisible, and
     there is always a whole spare copy either side to drag into. */

  var railsBlock = document.querySelector('.stack-rails');

  if (railsBlock && !reduced) {
    var SPEED = 34;        // px per second — one pace for every rail
    var FRICTION = 0.94;   // per frame decay on a mouse throw
    var RESUME = 900;      // ms of stillness before the drift picks up again

    var rails = Array.prototype.map.call(
      railsBlock.querySelectorAll('.rail'),
      function (rail) {
        var view = rail.querySelector('.rail-viewport');
        var track = rail.querySelector('.rail-track');
        var r = {
          view: view,
          dir: /reverse/.test(track.style.getPropertyValue('--rail-dir')) ? -1 : 1,
          setW: 0,
          hover: false,
          idleAt: 0,       // timestamp the visitor last let go
          fling: 0,        // leftover mouse velocity, px/s
          drag: null
        };

        r.measure = function () {
          var set = rail.querySelector('.rail-set');
          var w = set ? set.getBoundingClientRect().width : 0;
          if (!w) return;
          r.setW = w;
          if (view.scrollLeft < w) view.scrollLeft = w;   // start in the middle band
        };
        r.measure();

        /* Keep the offset inside [setW, 2·setW). Landing on the same pixels one
           set over means nothing visibly moves. */
        r.wrap = function () {
          if (!r.setW) return;
          var x = view.scrollLeft;
          if (x >= r.setW * 2) view.scrollLeft = x - r.setW;
          else if (x < r.setW) view.scrollLeft = x + r.setW;
        };

        view.addEventListener('mouseenter', function () { r.hover = true; });
        view.addEventListener('mouseleave', function () { r.hover = false; });

        /* Any contact stops the drift; it only resumes after a pause, so the
           rail doesn't crawl out from under a finger that's still resting. */
        function touched() { r.idleAt = performance.now(); r.fling = 0; }
        view.addEventListener('scroll', function () { if (r.drag) return; r.wrap(); }, { passive: true });
        view.addEventListener('touchstart', touched, { passive: true });
        view.addEventListener('touchmove', touched, { passive: true });
        view.addEventListener('touchend', touched, { passive: true });
        view.addEventListener('wheel', touched, { passive: true });

        /* Touch and pen already pan natively — hijacking them would cost the
           browser's momentum and its vertical-scroll handoff. Mouse doesn't. */
        view.addEventListener('pointerdown', function (e) {
          if (e.pointerType !== 'mouse' || e.button !== 0) return;
          r.drag = { x: e.clientX, from: view.scrollLeft, at: performance.now(), moved: false };
          r.fling = 0;
          view.setPointerCapture(e.pointerId);
        });

        view.addEventListener('pointermove', function (e) {
          if (!r.drag) return;
          var dx = e.clientX - r.drag.x;
          if (!r.drag.moved && Math.abs(dx) > 3) {
            r.drag.moved = true;
            view.classList.add('is-dragging');
          }
          if (!r.drag.moved) return;
          var now = performance.now();
          var prev = view.scrollLeft;

          /* Fold the target into the band *before* handing it over. Assigning
             first and correcting after would let the browser clamp a fast flick
             at the end of the scroller, and the rail would snag. Shifting the
             drag origin by the same amount keeps the next delta honest. */
          var target = r.drag.from - dx;
          while (target >= r.setW * 2) { target -= r.setW; r.drag.from -= r.setW; }
          while (target < r.setW)      { target += r.setW; r.drag.from += r.setW; }
          view.scrollLeft = target;

          var dt = now - r.drag.at;
          var step = view.scrollLeft - prev;
          // A wrap makes the raw step a whole set wide; that isn't real speed.
          if (dt > 0 && Math.abs(step) < r.setW / 2) r.fling = step / dt * 1000;
          r.drag.at = now;
        });

        function endDrag(e) {
          if (!r.drag) return;
          if (view.hasPointerCapture && e.pointerId != null &&
              view.hasPointerCapture(e.pointerId)) view.releasePointerCapture(e.pointerId);
          r.drag = null;
          r.idleAt = performance.now();
          view.classList.remove('is-dragging');
        }
        view.addEventListener('pointerup', endDrag);
        view.addEventListener('pointercancel', endDrag);

        return r;
      }
    );

    /* Off screen or in a background tab the whole loop shuts down — four rails
       nudging scroll offsets forever is work nobody can see, and battery on a
       phone. */
    var inView = !('IntersectionObserver' in window);
    var railFrame = null;   // named apart from section 5's iframe: same function scope

    function tick(now) {
      railFrame = null;
      var dt = Math.min((now - (tick.last || now)) / 1000, 0.05);  // cap after a tab switch
      tick.last = now;

      rails.forEach(function (r) {
        if (!r.setW || r.drag) return;
        if (r.fling) {
          r.view.scrollLeft += r.fling * dt;
          r.fling *= Math.pow(FRICTION, dt * 60);
          if (Math.abs(r.fling) < 8) r.fling = 0;
        } else if (!r.hover && now - r.idleAt > RESUME) {
          r.view.scrollLeft += SPEED * dt * r.dir;
        }
        r.wrap();
      });

      if (running()) railFrame = requestAnimationFrame(tick);
    }

    function running() { return inView && !document.hidden; }

    function sync() {
      if (running() && !railFrame) { tick.last = performance.now(); railFrame = requestAnimationFrame(tick); }
      if (!running() && railFrame) { cancelAnimationFrame(railFrame); railFrame = null; }
    }

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        inView = entries[0].isIntersecting;
        sync();
      }, { rootMargin: '120px 0px' }).observe(railsBlock);
    } else {
      sync();
    }

    document.addEventListener('visibilitychange', sync);

    var remeasure;
    window.addEventListener('resize', function () {
      clearTimeout(remeasure);
      remeasure = setTimeout(function () { rails.forEach(function (r) { r.measure(); }); }, 150);
    }, { passive: true });

    // Only now, so a JS failure above leaves the CSS marquee running.
    railsBlock.classList.add('is-live');
    rails.forEach(function (r) { r.measure(); });
  }

  /* ---- 8. Hero underline draws itself in on load ---------------------- */

  var accent = document.querySelector('.hero h1 .accent');
  if (accent && !reduced) {
    requestAnimationFrame(function () { accent.style.setProperty('--u', '100%'); });
  } else if (accent) {
    accent.style.setProperty('--u', '100%');
  }
})();
