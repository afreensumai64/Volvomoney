(() => {
  const API = document.getElementById('dash').dataset.news;
  const esc = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const getNews = async cat => { try { const r = await fetch(API + '?cat=' + cat); return r.ok ? await r.json() : []; } catch { return []; } };

  /* Market pulse panel */
  const list = document.getElementById('pulseList');
  async function loadPulse(cat) {
    list.innerHTML = '<div class="skel mb-2"></div>'.repeat(3);
    const items = (await getNews(cat)).slice(0, 5);
    list.innerHTML = items.length ? items.map(n => `<a href="${esc(n.link)}" target="_blank" rel="noopener">${esc(n.title)}<br><small>${esc(n.source)}</small></a>`).join('')
      : '<p class="text-secondary mb-0">News is unavailable right now. Check your internet connection.</p>';
  }
  document.querySelectorAll('#pulseTabs .pill').forEach(b => b.onclick = () => {
    document.querySelectorAll('#pulseTabs .pill').forEach(x => x.classList.toggle('on', x === b)); loadPulse(b.dataset.c);
  });
  loadPulse('stocks');

  /* Pop-up news toasts */
  const toast = document.getElementById('newsToast'); let queue = [], idx = 0, timer;
  const closeToast = () => toast.classList.remove('show');
  document.getElementById('toastClose').onclick = () => { closeToast(); clearTimeout(timer); sessionStorage.setItem('fsToastOff', '1'); };
  function showNext() {
    if (!queue.length || sessionStorage.getItem('fsToastOff')) return;
    const n = queue[idx++ % queue.length];
    const a = document.getElementById('toastLink'); a.textContent = n.title; a.href = n.link;
    document.getElementById('toastSrc').textContent = n.source;
    toast.classList.add('show');
    timer = setTimeout(() => { closeToast(); timer = setTimeout(showNext, 6000); }, 10000);
  }
  async function startToasts() {
    const [a, b] = await Promise.all([getNews('stocks'), getNews('gold')]);
    for (let i = 0; i < 4; i++) { if (a[i]) queue.push(a[i]); if (b[i]) queue.push(b[i]); }
    setTimeout(showNext, 1500);
  }

  /* Welcome / invest suggestions pop-up (once per browser session) */
  const el = document.getElementById('welcomeModal');
  if (!sessionStorage.getItem('fsWelcome')) {
    sessionStorage.setItem('fsWelcome', '1');
    el.addEventListener('hidden.bs.modal', startToasts, {once: true});
    setTimeout(() => new bootstrap.Modal(el).show(), 500);
  } else startToasts();
})();
