// ==UserScript==
// @name         Torn Honor Frames
// @namespace    torn-honor-frames
// @version      1.0.2
// @description  Turns the honor bar on Torn profiles into an ornate frame around the profile picture, with the name on its nameplate.
// @author       Manuel [3747263]
// @license      MIT
// @homepageURL  https://github.com/manuelcecchetto/torn-honor-frames
// @supportURL   https://github.com/manuelcecchetto/torn-honor-frames/issues
// @updateURL    https://raw.githubusercontent.com/manuelcecchetto/torn-honor-frames/main/userscript/honor-frames.user.js
// @downloadURL  https://raw.githubusercontent.com/manuelcecchetto/torn-honor-frames/main/userscript/honor-frames.user.js
// @match        https://www.torn.com/profiles.php*
// @run-at       document-idle
// @grant        GM_xmlhttpRequest
// @connect      raw.githubusercontent.com
// ==/UserScript==

// Each frame was generated from one honor bar (tools/ in this project) and comes with its photo
// window and nameplate in frames.json, in CSS pixels of the 232x348 frame box. Frames are served
// straight from the GitHub repository (raw.githubusercontent.com, cached 5 minutes); the script sends nothing about the page or
// the player anywhere, it only downloads frames.json and the frame of the honor being shown. Torn's own markup is
// only hidden, never changed, so the profile page's React keeps working; profiles whose honor has
// no frame stay as they are.
(() => {
  'use strict';

  const BASE = 'https://raw.githubusercontent.com/manuelcecchetto/torn-honor-frames/main';
  /** How far the photo reaches under the frame on each side, so the frame's inner lip overlaps it. */
  const UNDER = 4;

  const CSS = `
/* The profile column stays 206px wide so Torn's floats keep their places; the frame is
   centred on it and reaches a little past it. */
.profile-wrapper .profile-image.thf-framed { position: relative; height: 348px; }
.profile-wrapper .profile-image.thf-framed > :not(.thf-frame) { display: none; }
.thf-frame { position: absolute; left: -10px; top: -6px; width: 232px; height: 348px; display: block; }
.thf-photo { position: absolute; object-fit: cover; }
.thf-art { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
.thf-frame .honor-text-wrap.thf-name {
  position: absolute; display: block; height: 20px; line-height: 20px;
  pointer-events: none; transform: scale(1.5);
}
/* Torn overlaps each letter's outline with the next (-2px); scaled up that reads cramped. */
.thf-frame .honor-text-wrap.thf-name .honor-text-svg span { margin-right: -1px; }
.thf-frame .honor-text-wrap.thf-name .honor-text-svg span:last-of-type { margin-right: 0; }`;

  let manifest = null;
  function loadManifest() {
    manifest ??= new Promise((resolve) => {
      GM_xmlhttpRequest({
        method: 'GET',
        url: `${BASE}/frames/frames.json`,
        timeout: 20000,
        onload: (r) => {
          try {
            resolve(r.status === 200 ? JSON.parse(r.responseText) : {});
          } catch {
            resolve({});
          }
        },
        onerror: () => resolve({}),
        ontimeout: () => resolve({}),
      });
    });
    return manifest;
  }

  function honorId(profileImage) {
    const src = profileImage.querySelector('.honor-text-wrap img')?.getAttribute('src') ?? '';
    return /\/images\/honors\/(\d+)\//.exec(src)?.[1] ?? null;
  }

  function buildFrame(profileImage, id, info) {
    const honor = profileImage.querySelector('.honor-text-wrap');
    const photo = profileImage.querySelector('.img-wrap img');
    const link = profileImage.querySelector('a.profile-image-wrapper');
    if (!honor) return null;

    const box = document.createElement(link ? 'a' : 'div');
    box.className = 'thf-frame';
    box.dataset.honor = id;
    if (link) box.href = link.href;

    const [wx0, wy0, wx1, wy1] = info.win;
    if (photo?.src) {
      const img = document.createElement('img');
      img.className = 'thf-photo';
      img.alt = 'Profile';
      img.src = photo.src;
      img.style.cssText = `left:${wx0 - UNDER}px;top:${wy0 - UNDER}px;width:${wx1 - wx0 + 2 * UNDER}px;height:${wy1 - wy0 + 2 * UNDER}px`;
      box.append(img);
    }

    const art = document.createElement('img');
    art.className = 'thf-art';
    art.alt = '';
    art.src = `${BASE}/frames/${id}.webp?v=${info.v}`;
    box.append(art);

    // Torn's lettering: the honor-text-svg spans keep their sprite (and admin/officer colours) by class.
    const name = honor.cloneNode(true);
    name.querySelector('img')?.remove();
    name.querySelector('.honor-text:not(.honor-text-svg)')?.remove();
    name.classList.add('thf-name');
    const [px0, py0, px1, py1] = info.plate;
    name.style.cssText = `left:${px0}px;width:${px1 - px0}px;top:${Math.round((py0 + py1) / 2 - 10)}px`;
    box.append(name);
    return box;
  }

  async function apply(profileImage) {
    const id = honorId(profileImage);
    const current = profileImage.querySelector(':scope > .thf-frame');
    if (current && current.dataset.honor === id) return;
    current?.remove();
    profileImage.classList.remove('thf-framed');
    if (!id) return;
    const info = (await loadManifest())[id];
    if (!info || profileImage.querySelector(':scope > .thf-frame')) return;
    const box = buildFrame(profileImage, id, info);
    if (!box) return;
    profileImage.append(box);
    profileImage.classList.add('thf-framed');
  }

  const style = document.createElement('style');
  style.textContent = CSS;
  document.head.append(style);

  let queued = false;
  const scan = () => {
    queued = false;
    document.querySelectorAll('.profile-wrapper .profile-image').forEach((el) => void apply(el));
  };
  scan();
  // The profile is rendered by React after load and Torn's chat changes the page all the time:
  // look again on changes, at most once a frame.
  new MutationObserver(() => {
    if (!queued) {
      queued = true;
      requestAnimationFrame(scan);
    }
  }).observe(document.body, { childList: true, subtree: true });
})();
