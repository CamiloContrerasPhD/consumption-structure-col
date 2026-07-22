/* Minimal EN/ES i18n for Site 2.
   Static text: add data-en="..." to an element; its existing (Spanish) innerHTML is captured as data-es.
   Placeholders: data-en-ph / data-es-ph. Dynamic text (D3 labels, tooltips): use I18N.t('es','en')
   and re-render on the 'langchange' event. Preference persists in localStorage. */
(function(){
  var KEY='site2_lang';
  function cur(){ return localStorage.getItem(KEY)==='en' ? 'en' : 'es'; }
  function apply(lang){
    lang = (lang==='en') ? 'en' : 'es';
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-en]').forEach(function(el){
      if(el.getAttribute('data-es')==null) el.setAttribute('data-es', el.innerHTML);
      el.innerHTML = (lang==='en') ? el.getAttribute('data-en') : el.getAttribute('data-es');
    });
    document.querySelectorAll('[data-en-ph]').forEach(function(el){
      if(el.getAttribute('data-es-ph')==null) el.setAttribute('data-es-ph', el.getAttribute('placeholder')||'');
      el.setAttribute('placeholder', (lang==='en') ? el.getAttribute('data-en-ph') : el.getAttribute('data-es-ph'));
    });
    localStorage.setItem(KEY, lang);
    document.dispatchEvent(new CustomEvent('langchange',{detail:{lang:lang}}));
  }
  window.I18N = {
    get lang(){ return cur(); },
    set: apply,
    toggle: function(){ apply(cur()==='en'?'es':'en'); },
    t: function(es,en){ return cur()==='en' ? en : es; }
  };

  /* ---- flag dropdown (same design as Site 1) ---- */
  var FLAG_CO =
    '<svg viewBox="0 0 24 16" width="24" height="16" aria-hidden="true">' +
    '<rect width="24" height="16" fill="#FCD116"/>' +
    '<rect y="8" width="24" height="4" fill="#003893"/>' +
    '<rect y="12" width="24" height="4" fill="#CE1126"/></svg>';
  var FLAG_UK =
    '<svg viewBox="0 0 60 30" width="24" height="16" aria-hidden="true">' +
    '<clipPath id="ukc2"><path d="M0,0 v30 h60 v-30 z"/></clipPath>' +
    '<clipPath id="ukt2"><path d="M30,15 h30 v15 z v-15 h-30 z h-30 v-15 z v15 h30 z"/></clipPath>' +
    '<g clip-path="url(#ukc2)">' +
    '<path d="M0,0 v30 h60 v-30 z" fill="#012169"/>' +
    '<path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/>' +
    '<path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#ukt2)" stroke="#C8102E" stroke-width="4"/>' +
    '<path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/>' +
    '<path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/>' +
    '</g></svg>';
  var FLAGS = { es: FLAG_CO, en: FLAG_UK };
  var NAMES = { es: 'Español', en: 'English' };
  var css =
    '.langsw{position:fixed;top:12px;right:16px;z-index:120;font-family:var(--mono,monospace)}' +
    '.langsw__btn{display:flex;align-items:center;gap:7px;background:#fff;border:1px solid var(--ink,#141414);' +
    'border-radius:4px;padding:5px 9px;cursor:pointer;font-size:11px;letter-spacing:.05em;text-transform:uppercase;' +
    'color:var(--ink,#141414);line-height:1;box-shadow:0 1px 4px rgba(0,0,0,.08)}' +
    '.langsw__btn svg{border-radius:2px;display:block;box-shadow:0 0 0 1px rgba(0,0,0,.12)}' +
    '.langsw__car{font-size:9px;opacity:.6;transition:transform .15s}' +
    '.langsw.open .langsw__car{transform:rotate(180deg)}' +
    '.langsw__menu{position:absolute;top:calc(100% + 6px);right:0;background:#fff;border:1px solid var(--ink,#141414);' +
    'border-radius:4px;overflow:hidden;min-width:148px;box-shadow:0 4px 16px rgba(0,0,0,.12);display:none}' +
    '.langsw.open .langsw__menu{display:block}' +
    '.langsw__opt{display:flex;align-items:center;gap:9px;width:100%;background:transparent;border:0;' +
    'padding:9px 12px;cursor:pointer;font-family:inherit;font-size:12px;color:var(--ink,#141414);text-align:left}' +
    '.langsw__opt:hover{background:var(--line2,#ededea)}' +
    '.langsw__opt[aria-current="true"]{background:var(--accent-tint,#e6f4f4);font-weight:600}' +
    '.sitenav{padding-right:104px}' +
    '@media(max-width:620px){.langsw{top:8px;right:8px}.sitenav{padding-right:0;margin-top:34px}}';

  function refreshWidget(){
    var box = document.querySelector('.langsw');
    if(!box) return;
    var lang = cur();
    box.querySelector('.langsw__btn').innerHTML =
      FLAGS[lang] + '<span>' + lang.toUpperCase() + '</span><span class="langsw__car">▼</span>';
    box.querySelectorAll('.langsw__opt').forEach(function(o){
      if(o.getAttribute('data-lang') === lang) o.setAttribute('aria-current','true');
      else o.removeAttribute('aria-current');
    });
  }
  function buildWidget(){
    if(document.querySelector('.langsw')) return;
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    var box = document.createElement('div'); box.className = 'langsw';
    var btn = document.createElement('button'); btn.className = 'langsw__btn'; btn.type = 'button';
    btn.setAttribute('aria-haspopup','true');
    var menu = document.createElement('div'); menu.className = 'langsw__menu';
    ['es','en'].forEach(function(code){
      var o = document.createElement('button'); o.className = 'langsw__opt'; o.type = 'button';
      o.setAttribute('data-lang', code);
      o.innerHTML = FLAGS[code] + '<span>' + NAMES[code] + '</span>';
      o.addEventListener('click', function(){
        box.classList.remove('open');
        if(code !== cur()) apply(code);   // cambio en vivo, sin recargar
      });
      menu.appendChild(o);
    });
    btn.addEventListener('click', function(e){ e.stopPropagation(); box.classList.toggle('open'); });
    document.addEventListener('click', function(){ box.classList.remove('open'); });
    box.appendChild(btn); box.appendChild(menu);
    document.body.appendChild(box);
    refreshWidget();
  }
  document.addEventListener('langchange', refreshWidget);

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', function(){ apply(cur()); buildWidget(); });
  else { apply(cur()); buildWidget(); }
})();
