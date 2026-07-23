/* Shared top navigation + language switch + KaTeX formula rendering for Site 2. */
(function(){
  var BRAND = {es:'Estructura del consumo', en:'Consumption structure'};
  var NAV = [
    {href:'index.html',       es:'Inicio',      en:'Home'},
    {href:'complejidad.html', es:'Complejidad', en:'Complexity'},
    {href:'marcas.html',      es:'Marcas',      en:'Brands'},
    {href:'oportunidad.html', es:'Oportunidad', en:'Opportunity'},
    {href:'acceso.html',      es:'Acceso',      en:'Access'},
    {href:'integracion.html', es:'Integración', en:'Integration'},
    {href:'riesgo.html',      es:'Riesgo',      en:'Risk'},
    {href:'clusters.html',    es:'Clusters',    en:'Clusters'},
    {href:'red.html',         es:'Red',         en:'Network'},
    {href:'incertidumbre.html', es:'Incertidumbre', en:'Uncertainty'},
    {href:'metodologia.html', es:'Metodología', en:'Methodology'},
    {href:'https://camilocontrerasphd.github.io/political-polarization-consumption-col/',
     es:'Proyecto 1 ↗', en:'Project 1 ↗', match:'__ext__', ext:true}
  ];
  function L(){ return (window.I18N && I18N.lang==='en') ? 'en' : 'es'; }
  function build(){
    var bar = document.querySelector('.topbar') || document.querySelector('.sitenav');
    if(bar){
      var cur = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
      if(!cur) cur = 'index.html';
      var lang = L();
      var wasOpen = bar.classList && bar.classList.contains('open');
      bar.className = 'sitenav' + (wasOpen ? ' open' : '');
      var html = '<a class="nav-brand" href="index.html">'+BRAND[lang]+' <span>CO</span></a>'
               + '<div class="nav-links">';
      NAV.forEach(function(it){
        var active = ((it.match || it.href).toLowerCase() === cur) ? ' class="active"' : '';
        var ext = it.ext ? ' target="_blank" rel="noopener"' : '';
        html += '<a href="' + it.href + '"' + active + ext + '>' + it[lang] + '</a>';
      });
      html += '</div>';
      html += '<button class="navburger" aria-label="'+(lang==='en'?'Menu':'Menú')+'">'
            + '<span></span><span></span><span></span></button>';
      bar.innerHTML = html;
      var burger = bar.querySelector('.navburger');
      if(burger) burger.addEventListener('click', function(){ bar.classList.toggle('open'); });
    }
    if(window.katex){
      document.querySelectorAll('.ktx').forEach(function(el){
        try{ katex.render(el.getAttribute('data-tex') || el.textContent, el, {displayMode:true, throwOnError:false}); }
        catch(e){}
      });
    }
  }
  function boot(){ build(); document.addEventListener('langchange', build); }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
