(() => {
  const app = document.getElementById('chatApp'), msgs = document.getElementById('msgs'), hist = [];
  const esc = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  const down = () => msgs.scrollTop = msgs.scrollHeight;
  function add(role, html) {
    const d = document.createElement('div'); d.className = 'm ' + role; d.innerHTML = html;
    msgs.appendChild(d); down(); return d;
  }
  async function ask(text) {
    text = text.trim(); if (!text) return;
    Chachu.stop();
    add('user', esc(text)); hist.push({role: 'user', content: text});
    const bot = add('bot', '<span class="dots"><span></span><span></span><span></span></span>');
    Chachu.think(true);
    let reply;
    try {
      const r = await fetch(app.dataset.api, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({messages: hist})});
      reply = (await r.json()).reply;
    } catch { reply = 'Arre! I could not reach the server. Please check that the app is running.'; }
    hist.push({role: 'model', content: reply});
    bot.innerHTML = '';
    await Chachu.talk(bot, reply, fmt, down);
  }
  document.getElementById('chatForm').onsubmit = e => {
    e.preventDefault(); const i = document.getElementById('chatInput'); const v = i.value; i.value = ''; ask(v);
  };
  document.querySelectorAll('#chips .pill').forEach(b => b.onclick = () => ask(b.textContent));

  const vb = document.getElementById('voiceBtn');
  const paintVoice = () => {
    const on = Chachu.voiceOn();
    vb.innerHTML = `<i class="bi bi-volume-${on ? 'up' : 'mute'}"></i> <span>Voice ${on ? 'on' : 'off'}</span>`;
  };
  vb.onclick = () => { Chachu.toggleVoice(); paintVoice(); };
  paintVoice();

  add('bot', 'Namaste beta! I am Budget Chachu, your money buddy. Ask me anything about saving, budgeting, SIP, gold or stocks.');
  if (app.dataset.prefill) setTimeout(() => ask(app.dataset.prefill), 500);
})();
