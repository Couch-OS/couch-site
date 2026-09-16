/* One quick pass through the integrations, ending on the original headline. */
(() => {
  const headline = document.querySelector('#headline em');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  if (!headline || motion.matches || !headline.animate) return;
  const names = [
    'Kodi', 'CoreELEC', 'Sonos', 'Philips Hue', 'Home Assistant',
    'LG webOS', 'Denon AVR', 'Android / Google TV', 'Apple TV',
    'Samsung Tizen', 'Bluetooth', 'UniFi Protect', 'Matter', 'Infrared',
  ];
  const finalText = headline.textContent;
  const reel = document.createElement('span');
  reel.className = 'headline-reel';
  reel.setAttribute('aria-hidden', 'true');
  const track = document.createElement('span');
  track.className = 'headline-track';
  [finalText, ...names, finalText].forEach(text => {
    const line = document.createElement('span');
    line.className = 'headline-word';
    line.textContent = text;
    track.append(line);
  });
  reel.append(track);
  let animation;
  const finish = () => {
    animation?.cancel();
    headline.classList.remove('headline-rolling');
    reel.remove();
    motion.removeEventListener('change', finish);
    window.removeEventListener('resize', finish);
  };
  const start = () => {
    if (motion.matches || !headline.isConnected) return;
    headline.append(reel);
    const height = headline.getBoundingClientRect().height;
    track.querySelectorAll('.headline-word').forEach(line => {
      line.style.height = `${height}px`;
      // Keep long integration names inside the original headline's width.
      const text = document.createRange();
      text.selectNodeContents(line);
      const width = text.getBoundingClientRect().width;
      if (width > headline.clientWidth) line.style.fontSize = `${parseFloat(getComputedStyle(headline).fontSize) * headline.clientWidth / width}px`;
    });
    headline.classList.add('headline-rolling');
    const steps = names.length + 1;
    // One continuous movement avoids stopping and restarting at every name.
    animation = track.animate([
      {transform:'translate3d(0, 0, 0)'},
      {transform:`translate3d(0, -${steps * height}px, 0)`},
    ], {duration:4200, delay:350, easing:'cubic-bezier(.35, 0, .25, 1)', fill:'both'});
    animation.finished.then(finish, () => {});
    motion.addEventListener('change', finish);
    window.addEventListener('resize', finish, {once:true});
  };
  document.fonts.ready.then(start);
})();
