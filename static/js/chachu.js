/* Budget Chachu: eye tracking, speaking, tips */
(() => {
  const body = document.body, KEY = 'chachuVoice', canSpeak = 'speechSynthesis' in window;
  const TIPS = ['Pay yourself first. Move savings out on salary day.',
    'Keep three to six months of expenses as an emergency fund.',
    'Credit card interest is 30 to 40 percent a year. Avoid it!',
    'Start a SIP early. Time in the market beats timing the market.',
    'Track every rupee for 30 days. You will be surprised!',
    'Never invest money you will need within three years.'];
  let token = 0;

  document.addEventListener('mousemove', e => {
    document.querySelectorAll('.chachu').forEach(svg => {
      const r = svg.getBoundingClientRect();
      if (!r.width) return;
      svg.style.setProperty('--px', ((e.clientX - r.left - r.width / 2) / innerWidth * 12).toFixed(1) + 'px');
      svg.style.setProperty('--py', ((e.clientY - r.top - r.height * .45) / innerHeight * 9).toFixed(1) + 'px');
    });
  });

  const voiceOn = () => canSpeak && localStorage.getItem(KEY) !== 'off';
  function status(state, text) {
    const s = document.getElementById('chStatus'); if (!s) return;
    s.dataset.state = state;
    document.getElementById('chStatusText').textContent = text;
  }
  function pickVoice() {
    const v = speechSynthesis.getVoices();
    return v.find(x => x.lang === 'en-IN') || v.find(x => x.lang.startsWith('en')) || null;
  }
  function speak(text) {
    return new Promise(res => {
      if (!voiceOn()) return res();
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text.replace(/\*\*/g, '').replace(/₹\s?([\d,.]+)/g, '$1 rupees'));
      const v = pickVoice(); if (v) { u.voice = v; u.lang = v.lang; } else u.lang = 'en-IN';
      u.rate = 1; u.pitch = .8; u.onend = u.onerror = () => res();
      speechSynthesis.speak(u);
    });
  }
  function think(on) {
    body.classList.toggle('thinking', on);
    if (on) { body.classList.remove('speaking'); status('thinking', 'Thinking...'); }
  }
  function stop() { token++; if (canSpeak) speechSynthesis.cancel(); body.classList.remove('speaking', 'thinking'); status('idle', 'Ready to help'); }

  /* Types the reply into `el` while Chachu's mouth moves and (optionally) his voice plays */
  async function talk(el, text, fmt, onTick) {
    const my = ++token;
    body.classList.remove('thinking'); body.classList.add('speaking'); status('speaking', 'Speaking...');
    el.classList.add('caret');
    const speech = speak(text), delay = voiceOn() ? 52 : 18;
    await new Promise(res => {
      let i = 0;
      (function tick() {
        if (my !== token) return res();
        i = Math.min(text.length, i + 1);
        let part = text.slice(0, i);
        if ((part.match(/\*\*/g) || []).length % 2) part += '**';
        el.innerHTML = fmt(part); onTick && onTick();
        i < text.length ? setTimeout(tick, delay) : res();
      })();
    });
    if (my !== token) return;
    el.innerHTML = fmt(text); onTick && onTick();
    await speech;
    if (my !== token) return;
    el.classList.remove('caret'); body.classList.remove('speaking'); status('idle', 'Ready to help');
  }

  function bubble(host, text, ms = 4500) {
    host.querySelectorAll('.chachu-bubble').forEach(b => b.remove());
    const b = document.createElement('div'); b.className = 'chachu-bubble'; b.textContent = text;
    host.appendChild(b); setTimeout(() => b.remove(), ms);
  }
  document.addEventListener('click', e => {
    const svg = e.target.closest('.chachu'), host = e.target.closest('[data-tips]');
    if (!svg || !host) return;
    svg.classList.add('hop'); setTimeout(() => svg.classList.remove('hop'), 650);
    bubble(host, TIPS[Math.floor(Math.random() * TIPS.length)]);
  });
  if (canSpeak) speechSynthesis.getVoices();
  window.addEventListener('beforeunload', () => canSpeak && speechSynthesis.cancel());

  window.Chachu = { think, talk, stop, voiceOn, bubble,
    toggleVoice() { localStorage.setItem(KEY, voiceOn() ? 'off' : 'on'); if (!voiceOn() && canSpeak) speechSynthesis.cancel(); return voiceOn(); } };
})();
