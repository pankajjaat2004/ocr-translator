(function(){
  var yearEl = document.getElementById('y');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  var apiStatusEl = document.getElementById('api-status');
  if (apiStatusEl) {
    var k = (window.__GEMINI_API_KEY__ || '').trim();
    apiStatusEl.textContent = k ? 'Ready' : 'API key missing on server';
    apiStatusEl.className = k ? 'status ok' : 'status bad';
  }

  var form = document.getElementById('upload-form');
  if (!form) return;
  var fileInput = document.getElementById('file-input');
  var btn = document.getElementById('upload-btn');
  var originalEl = document.getElementById('original');
  var translatedEl = document.getElementById('translated');
  var messageEl = document.getElementById('message');
  var langSelect = document.getElementById('language-select');
  var langLabel = document.getElementById('lang-label');

  function updateLangLabel(){
    var sel = langSelect.options[langSelect.selectedIndex];
    langLabel.textContent = sel ? sel.textContent : 'Hindi';
  }
  langSelect.addEventListener('change', updateLangLabel);
  updateLangLabel();

  form.addEventListener('submit', async function(e){
    e.preventDefault();
    messageEl.textContent = '';
    originalEl.textContent = '';
    translatedEl.textContent = '';
    var file = fileInput.files && fileInput.files[0];
    if (!file) { messageEl.textContent = 'Please choose an image or PDF first.'; messageEl.className = 'muted bad'; return; }
    btn.disabled = true; btn.textContent = 'Processing…';
    try {
      var data = new FormData();
      data.append('file', file);
      data.append('lang', langSelect.value);
      var res = await fetch('/upload', { method: 'POST', body: data });
      var json = null; try { json = await res.json(); } catch {}
      if (res.ok && json) {
        originalEl.textContent = json.original_text || '';
        translatedEl.textContent = json.translated_text || '';
        if (json.target_lang_name) langLabel.textContent = json.target_lang_name;
        messageEl.textContent = 'Done'; messageEl.className = 'muted ok';
      } else {
        var msg = (json && json.error) ? json.error : 'Upload failed.';
        messageEl.textContent = msg; messageEl.className = 'muted bad';
      }
    } catch (err) {
      console.error(err);
      messageEl.textContent = (err && err.message) ? err.message : 'Network error.';
      messageEl.className = 'muted bad';
    } finally {
      btn.disabled = false; btn.textContent = 'Upload';
    }
  });
})();
