

document.addEventListener('DOMContentLoaded', function() {
  // відлік до Нового року
  function getNewYearDate() {
    const now = new Date();
    const year = now.getMonth() === 11 && now.getDate() > 31
      ? now.getFullYear() + 1
      : now.getFullYear() + 1;

    return new Date(year, 0, 1, 0, 0, 0);
  }

  const target = getNewYearDate();

  function updateCountdown() {
    const now = new Date();
    let diff = Math.max(0, Math.floor((target - now) / 1000));

    const days = Math.floor(diff / 86400);
    diff %= 86400;

    const hours = Math.floor(diff / 3600);
    diff %= 3600;

    const minutes = Math.floor(diff / 60);
    const seconds = diff % 60;

    const el = document.getElementById('countdown');
    if (!el) return;

    el.textContent =
      `${String(days).padStart(2, '0')}д ` +
      `${String(hours).padStart(2, '0')}г ` +
      `${String(minutes).padStart(2, '0')}х ` +
      `${String(seconds).padStart(2, '0')}с`;

    if (target <= now) clearInterval(timer);
  }

  const timer = setInterval(updateCountdown, 1000);
  updateCountdown();
  // відлік до Нового року


  // Перемикання теми
  (function(){
    const KEY = 'site_theme';
    const body = document.body;
    const btn = document.getElementById('theme-toggle');

    function applyTheme(theme) {
      body.classList.remove('theme-dark','theme-light');
      if (theme === 'dark') body.classList.add('theme-dark');
      else body.classList.add('theme-light');
    }

    // прочитати з localStorage 
    const saved = localStorage.getItem(KEY);
    if (saved) {
      applyTheme(saved);
    } else {
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      applyTheme(prefersDark ? 'dark' : 'light');
    }

    if (btn) {
      btn.addEventListener('click', () => {
        const current = body.classList.contains('theme-dark') ? 'dark' : 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        localStorage.setItem(KEY, next);
      });
    }
  })();
  // Перемикання теми



  document.addEventListener("DOMContentLoaded", () => {
  const banner = document.getElementById("cookie-banner");
  const acceptBtn = document.getElementById("cookie-accept");

  if (!banner || !acceptBtn) return;

  if (!document.cookie.includes("cookie_consent=true")) {
    banner.style.display = "block";
  }

  acceptBtn.addEventListener("click", () => {
    // document.cookie = "cookie_consent=true; max-age=" + 60 * 60 * 24 * 365 + "; path=/";
    document.cookie = "cookie_consent=true; max-age=" + 60 + "; path=/";
    banner.style.display = "none";
  });
});

});
