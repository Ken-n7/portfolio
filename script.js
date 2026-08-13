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

  /* ---- 2. Header border, and the progress bar under it ----------------- */

  var header = document.querySelector('.site-header');
  var docEl = document.documentElement;
  var ticking = false;
  var travel = 0;          // how far the page can actually scroll

  /* Measured on load and resize rather than on every frame: reading
     scrollHeight during a scroll forces a layout, and the overlay's scroll
     lock collapses it — which moved the bar while the page had not. */
  function measure() {
    if (document.body.style.overflow === 'hidden') return;   // overlay open
    travel = docEl.scrollHeight - docEl.clientHeight;
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      header.setAttribute('data-scrolled', window.scrollY > 8 ? 'true' : 'false');
      /* A page shorter than the viewport has nothing to report, so the bar
         stays at zero rather than sitting permanently full. */
      header.style.setProperty('--scroll',
        travel > 0 ? Math.min(1, window.scrollY / travel).toFixed(4) : '0');
      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () { measure(); onScroll(); });
  window.addEventListener('load', function () { measure(); onScroll(); });
  measure();
  onScroll();

  /* ---- 3. Theme toggle ------------------------------------------------ */

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

  /* ---- 4. Project detail overlay --------------------------------------
     The card is the trigger; its .project-detail block is *moved* into the
     dialog on open and moved home on close. Moving rather than cloning keeps
     one copy of every node, so there is never a clone that can drift out of
     step with the card it came from.                                    */

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
      var kicker = card.querySelector('.project-kicker');   // only EVMC still has one
      pdKicker.textContent = kicker ? kicker.textContent : '';
      pdKicker.hidden = !kicker;

      /* Four projects carry their own wordmark; the rest just use the title.
         Lent in like everything else, so there is one copy of it. */
      var brand = card.querySelector('.brand');
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

  /* ---- 5. Hero underline draws itself in on load ---------------------- */

  var accent = document.querySelector('.hero h1 .accent');
  if (accent && !reduced) {
    requestAnimationFrame(function () { accent.style.setProperty('--u', '100%'); });
  } else if (accent) {
    accent.style.setProperty('--u', '100%');
  }

  /* ---- 6. The contact plate catches the light -------------------------
     Sheen and tilt both follow the pointer. Fine pointers only: a finger
     would leave the highlight stranded wherever it happened to lift, and
     the tilt would fight the scroll. */

  var plate = document.querySelector('.contact-card');

  if (plate && !reduced && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    var tiltFrame = 0;
    var arrival = 0;

    /* Read from the stylesheet so the two live in one place. */
    var ARRIVE = parseFloat(getComputedStyle(plate).getPropertyValue('--dur-arrive')) || 520;

    /* The highlight rests on the far side of the plate, so on entry it crosses
       to meet the pointer instead of appearing under it. Once it has had time
       to arrive, the lag drops to the tracking speed. */
    plate.addEventListener('pointerenter', function () {
      plate.classList.remove('is-tracking');
      plate.classList.add('is-arriving');
      clearTimeout(arrival);
      arrival = setTimeout(function () {
        plate.classList.remove('is-arriving');
        plate.classList.add('is-tracking');
      }, ARRIVE);
    });

    plate.addEventListener('pointermove', function (e) {
      if (tiltFrame) return;                 // one update per frame, no more
      var px = e.clientX, py = e.clientY;
      tiltFrame = requestAnimationFrame(function () {
        tiltFrame = 0;
        /* Measured inside the frame so a move never forces a sync layout. */
        var r = plate.getBoundingClientRect();
        var x = (px - r.left) / r.width;
        var y = (py - r.top) / r.height;
        plate.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
        plate.style.setProperty('--my', (y * 100).toFixed(1) + '%');
        /* Small angles on purpose. Past about 4deg the type starts to skew
           and the plate reads as a gimmick instead of a surface. */
        plate.style.setProperty('--ry', ((x - 0.5) * 6).toFixed(2) + 'deg');
        plate.style.setProperty('--rx', ((0.5 - y) * 4).toFixed(2) + 'deg');
      });
    });

    plate.addEventListener('pointerleave', function () {
      if (tiltFrame) { cancelAnimationFrame(tiltFrame); tiltFrame = 0; }
      clearTimeout(arrival);
      /* Both classes off, so the transition falls back to the slow settle. */
      plate.classList.remove('is-arriving');
      plate.classList.remove('is-tracking');
      plate.style.removeProperty('--rx');
      plate.style.removeProperty('--ry');
      plate.style.removeProperty('--mx');
      plate.style.removeProperty('--my');
    });
  }
})();
