/* Shared top navigation + KaTeX formula rendering for Site 1. */
(function(){
  var NAV = [
    ['index.html','Inicio'],
    ['regiones.html','Regiones'],
    ['analisis.html?d=tiendas','Marcas','analisis.html'],
    ['mapa-consumo.html','Mapa'],
    ['online.html','Online'],
    ['centro-periferia.html','Centro-periferia'],
    ['metodologia.html','Metodologia']
  ];
  function build(){
    var bar = document.querySelector('.topbar');
    if(bar){
      var cur = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
      if(!cur) cur = 'index.html';
      bar.className = 'sitenav';
      var html = '<a class="nav-brand" href="index.html">Polarizacion del consumo <span>CO</span></a>'
               + '<div class="nav-links">';
      NAV.forEach(function(it){
        var href = it[0], label = it[1], match = (it[2] || it[0]).toLowerCase();
        var active = (match === cur) ? ' class="active"' : '';
        html += '<a href="' + href + '"' + active + '>' + label + '</a>';
      });
      html += '</div>';
      bar.innerHTML = html;
    }
    if(window.katex){
      document.querySelectorAll('.ktx').forEach(function(el){
        try{ katex.render(el.getAttribute('data-tex') || el.textContent, el, {displayMode:true, throwOnError:false}); }
        catch(e){}
      });
    }
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();
