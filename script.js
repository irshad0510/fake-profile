// FakeGuard — Frontend Logic
// Calls /api/predict (Vercel serverless function) and renders result

async function analyze() {
  const followers  = parseInt(document.getElementById('followers').value)  || 0;
  const following  = parseInt(document.getElementById('following').value)  || 0;
  const posts      = parseInt(document.getElementById('posts').value)      || 0;
  const bio        = parseInt(document.getElementById('bio').value)        || 0;
  const nums       = parseInt(document.getElementById('nums').value)       || 0;
  const namewords  = parseInt(document.getElementById('namewords').value)  || 1;
  const haspic     = document.getElementById('haspic').checked;
  const isprivate  = document.getElementById('isprivate').checked;
  const hasurl     = document.getElementById('hasurl').checked;

  // Basic validation
  const errEl = document.getElementById('form-error');
  if (!document.getElementById('followers').value ||
      !document.getElementById('following').value ||
      !document.getElementById('posts').value) {
    errEl.style.display = 'inline';
    return;
  }
  errEl.style.display = 'none';

  const btn = document.querySelector('.btn-analyze');
  btn.textContent = 'Analyzing…';
  btn.disabled = true;

  try {
    // Try the real API first; fall back to client-side scoring if not available
    let result;
    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ followers, following, posts, bio, nums_in_username: nums,
                               fullname_words: namewords, profile_pic: haspic ? 1 : 0,
                               is_private: isprivate ? 1 : 0, has_external_url: hasurl ? 1 : 0 })
      });
      if (!res.ok) throw new Error('API not available');
      result = await res.json();
    } catch (_) {
      // Client-side fallback scoring (used when running without a backend)
      result = clientSideScore({ followers, following, posts, bio, nums, namewords,
                                  haspic, isprivate, hasurl });
    }

    renderResult(result, { followers, following, posts });

  } catch (err) {
    alert('Something went wrong. Please try again.');
    console.error(err);
  } finally {
    btn.textContent = 'Analyze Profile ↗';
    btn.disabled = false;
  }
}

// ─── Client-side heuristic scorer (no backend needed) ───────────────────────
function clientSideScore({ followers, following, posts, bio, nums, namewords, haspic, isprivate, hasurl }) {
  let score = 0;
  const signals = [];

  const ratio = following > 0 ? followers / following : followers;

  if (!haspic)      { score += 22; signals.push({ text: 'No profile picture', warn: true }); }
  else              { signals.push({ text: 'Has profile picture', warn: false }); }

  if (nums >= 4)    { score += 18; signals.push({ text: 'Many numbers in username', warn: true }); }
  else if (nums >= 2){ score += 8; signals.push({ text: 'Some numbers in username', warn: true }); }
  else              { signals.push({ text: 'Clean username', warn: false }); }

  if (posts <= 2)   { score += 18; signals.push({ text: 'Very few posts', warn: true }); }
  else if (posts <= 10){ score += 8; signals.push({ text: 'Low post count', warn: true }); }
  else              { signals.push({ text: 'Adequate post count', warn: false }); }

  if (ratio < 0.05) { score += 22; signals.push({ text: 'Very low follower ratio', warn: true }); }
  else if (ratio < 0.2){ score += 10; signals.push({ text: 'Low follower ratio', warn: true }); }
  else              { signals.push({ text: 'Normal follower ratio', warn: false }); }

  if (bio === 0)    { score += 10; signals.push({ text: 'Empty bio', warn: true }); }
  else              { signals.push({ text: 'Bio present', warn: false }); }

  if (namewords <= 1){ score += 8; signals.push({ text: 'Single-word name', warn: true }); }
  else              { signals.push({ text: 'Full name present', warn: false }); }

  if (!isprivate)   { signals.push({ text: 'Public account', warn: false }); }
  else              { signals.push({ text: 'Private account', warn: false }); }

  if (hasurl)       { score += 2; signals.push({ text: 'External URL in bio', warn: true }); }

  score = Math.min(Math.round(score), 100);
  const fake = score >= 45;
  const confidence = fake
    ? Math.min(60 + score * 0.38, 98)
    : Math.min(60 + (100 - score) * 0.38, 97);

  return { fake, score, confidence: Math.round(confidence), signals, source: 'client' };
}

// ─── Render result ───────────────────────────────────────────────────────────
function renderResult({ fake, score, confidence, signals }, { followers, following, posts }) {
  const ratio = following > 0 ? (followers / following).toFixed(2) : followers;

  document.getElementById('verdict-text').textContent = fake
    ? 'Likely fake account'
    : 'Likely real account';

  const badge = document.getElementById('verdict-badge');
  badge.textContent = fake ? 'FAKE' : 'REAL';
  badge.className = 'verdict-badge ' + (fake ? 'badge-fake' : 'badge-real');

  document.getElementById('risk-pct-label').textContent = score + '%';

  const bar = document.getElementById('risk-bar');
  bar.style.width = score + '%';
  bar.style.background = score >= 65
    ? 'var(--danger)'
    : score >= 40
    ? 'var(--warn)'
    : 'var(--safe)';

  document.getElementById('m-ratio').textContent = ratio;
  document.getElementById('m-posts').textContent  = posts;
  document.getElementById('m-conf').textContent   = confidence + '%';

  const grid = document.getElementById('signals');
  grid.innerHTML = signals.map(s => `
    <div class="signal ${s.warn ? 'signal-warn' : 'signal-ok'}">
      <span class="signal-dot ${s.warn ? 'dot-warn' : 'dot-ok'}"></span>
      ${s.text}
    </div>
  `).join('');

  const resultEl = document.getElementById('result');
  resultEl.style.display = 'block';
  resultEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
