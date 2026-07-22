/* Shared rendering for the Colombia consumption-polarization site. Requires d3 v7 + window.SITE. */
(function(){
const S = window.SITE;
const CL = {l:'#3367a6', r:'#bb2b3f'};
const SUBCAT_COLORS = ['#3a6ea5','#c8453a','#3f9b6e','#d9962f','#7a5ea8','#1f9aa6','#bd5d86','#8a8f3a','#a0703a','#5f6b76'];
window.SUBCAT_COLORS = SUBCAT_COLORS;
window.PCC = { S, CL };

// margin in points; sign -> color
function col(pts){ return pts>0?CL.r : pts<0?CL.l : '#999'; }
function fmt(v){ return (v>0?'+':'')+(+v).toFixed(1); }

/* ---------- HUB: mini histogram per domain ---------- */
window.drawHistogram = function(mount, brands, xmax){
  const W=300,H=120,m={t:6,r:6,b:16,l:6}, iw=W-m.l-m.r, ih=H-m.t-m.b;
  const nb=21, bins=new Array(nb).fill(0);
  const step=(2*xmax)/nb;
  brands.forEach(b=>{ let i=Math.floor((b.index*100+xmax)/step); i=Math.max(0,Math.min(nb-1,i)); bins[i]++; });
  const mx=Math.max(1,...bins);
  const svg=d3.select(mount).append('svg').attr('viewBox',`0 0 ${W} ${H}`);
  const g=svg.append('g').attr('transform',`translate(${m.l},${m.t})`);
  const bw=iw/nb;
  g.selectAll('rect').data(bins).join('rect')
    .attr('x',(d,i)=>i*bw+1).attr('width',bw-1.6)
    .attr('y',d=>ih-(d/mx)*ih).attr('height',d=>(d/mx)*ih)
    .attr('rx',1)
    .attr('fill',(d,i)=>{ const c=(i+0.5)*step-xmax; return Math.abs(c)<step?'#b9b2a3':col(c); });
  g.append('line').attr('x1',iw/2).attr('x2',iw/2).attr('y1',0).attr('y2',ih)
    .attr('stroke','#b3a994').attr('stroke-dasharray','3 3').attr('stroke-width',1);
};

/* ---------- ANALYSIS: scatter ---------- */
window.drawScatter = function(mount, domainKey){
  const dom = S.domains[domainKey];
  const brands = dom.brands.map(d=>({...d, pts:d.index*100}));
  const subcats = dom.subcats;
  const cmap = {}; subcats.forEach((s,i)=>cmap[s]=SUBCAT_COLORS[i%SUBCAT_COLORS.length]);

  const M={t:16,r:24,b:52,l:62}, W=900,H=486, iw=W-M.l-M.r, ih=H-M.t-M.b;
  const xmax=Math.max(20, Math.ceil(d3.max(brands,d=>Math.abs(d.pts))/5)*5);
  const x=d3.scaleLinear().domain([-xmax,xmax]).range([0,iw]);
  const ext=d3.extent(brands,d=>d.n_stores);
  let logy=true;
  const yS=()=> (logy?d3.scaleLog():d3.scaleLinear()).domain([Math.max(1,ext[0]*0.8),ext[1]*1.18]).range([ih,0]).clamp(true);
  let y=yS();

  const svg=d3.select(mount).append('svg').attr('viewBox',`0 0 ${W} ${H}`);
  const g=svg.append('g').attr('transform',`translate(${M.l},${M.t})`);
  g.append('rect').attr('width',iw/2).attr('height',ih).attr('fill','#f1f4f9');
  g.append('rect').attr('x',iw/2).attr('width',iw/2).attr('height',ih).attr('fill','#faf2f3');
  const gx=g.append('g').attr('class','axis').attr('transform',`translate(0,${ih})`);
  const gy=g.append('g').attr('class','axis');
  g.append('line').attr('class','zero').attr('x1',x(0)).attr('x2',x(0)).attr('y1',0).attr('y2',ih);
  g.append('text').attr('class','axis-label').attr('x',iw/2).attr('y',ih+42).attr('text-anchor','middle')
    .text('Indice de polarizacion (margen De La Espriella - Cepeda, en puntos)');
  g.append('text').attr('class','axis-label').attr('transform','rotate(-90)').attr('x',-ih/2).attr('y',-46)
    .attr('text-anchor','middle').text('Numero de locales (escala log)');

  const dots=g.append('g').selectAll('circle').data(brands).join('circle')
    .attr('class','dot-c').attr('r',6).attr('cx',d=>x(d.pts))
    .attr('fill',d=>cmap[d.subcat]).attr('fill-opacity',.72);
  const labels=g.append('g').selectAll('text').data(brands).join('text')
    .attr('font-size',10.5).attr('text-anchor','middle').attr('opacity',0)
    .style('font-family',"'Inter',sans-serif").style('font-weight','600').style('paint-order','stroke').style('stroke','#fff').style('stroke-width','3px')
    .attr('fill',d=>col(d.pts)).text(d=>d.brand);

  function place(){ y=yS();
    gx.call(d3.axisBottom(x).ticks(9).tickFormat(fmt).tickSize(-ih));
    gy.call(d3.axisLeft(y).ticks(6,'~s').tickSize(-iw));
    dots.attr('cy',d=>y(d.n_stores));
    labels.attr('x',d=>x(d.pts)).attr('y',d=>y(d.n_stores)-9);
  }
  place();

  const tip=d3.select('#tip');
  const side=d=>d.pts>0?'mas De La Espriella':d.pts<0?'mas Cepeda':'equilibrado';
  dots.on('mousemove',(e,d)=>{
      tip.style('opacity',1).style('left',(e.clientX+14)+'px').style('top',(e.clientY+12)+'px')
        .html(`<div class="b">${d.brand}</div><div class="m">${d.subcat} &middot; ${d.n_stores} locales</div>
               <div style="margin-top:4px;color:${col(d.pts)}">${fmt(d.pts)} pts (${side(d)})</div>`);
      d3.select(e.currentTarget).classed('hi',true).attr('r',8);
    })
    .on('mouseleave',(e)=>{tip.style('opacity',0);d3.select(e.currentTarget).classed('hi',false).attr('r',6);});

  let active='', query='';
  function apply(){
    dots.classed('dim',d=>{ const okC=!active||d.subcat===active, okQ=!query||d.brand.toLowerCase().includes(query); return !(okC&&okQ); });
    labels.attr('opacity',d=>{
      const matchQ=query&&d.brand.toLowerCase().includes(query);
      const matchC=active&&d.subcat===active&&!query;
      return (matchQ||matchC)?1:0; });
  }
  // chips
  const chipBox=d3.select(mount.replace('#chart','#chips'));
  chipBox.selectAll('.chip').data(subcats).join('button').attr('class','chip')
    .html(d=>`<span class="dot" style="background:${cmap[d]}"></span>${d}`)
    .on('click',function(e,c){active=active===c?'':c; chipBox.selectAll('.chip').classed('active',d=>d===active); apply();});

  return {
    search:(q)=>{query=(q||'').trim().toLowerCase();apply();},
    reset:()=>{active='';query='';chipBox.selectAll('.chip').classed('active',false);apply();},
    toggleLog:(v)=>{logy=v;place();},
  };
};

/* ---------- MAP: choropleth of municipios ---------- */
window.leanColor = d3.scaleLinear()
  .domain([-30,-15,-4,0,4,15,30])
  .range(['#1a4a82','#4393c3','#c9dcea','#f3f1ec','#f4c2b6','#d6604d','#9c1f2e'])
  .clamp(true);

window.drawMap = function(mount){
  const geo = window.GEO_MUNI;
  const W=720,H=820;
  const svg=d3.select(mount).append('svg').attr('viewBox',`0 0 ${W} ${H}`);
  const proj=d3.geoMercator().fitSize([W,H],geo);
  const path=d3.geoPath(proj);
  const tip=d3.select('#tip');
  svg.append('g').selectAll('path').data(geo.features).join('path')
    .attr('d',path)
    .attr('fill',d=>leanColor(d.properties.lean*100))
    .attr('stroke','#fff').attr('stroke-width',0.25)
    .style('cursor','pointer')
    .on('mousemove',(e,d)=>{
      const p=d.properties, pts=p.lean*100;
      tip.style('opacity',1).style('left',(e.clientX+14)+'px').style('top',(e.clientY+12)+'px')
        .html(`<div class="b">${p.name}</div><div class="m">${p.dept} &middot; ${p.region}</div>
          <div style="margin-top:3px;color:${col(pts)}">${fmt(pts)} pts &middot; ${(+p.votval).toLocaleString('es')} votos</div>
          ${p.top&&p.top.length?`<div class="m" style="margin-top:4px">Marcas: ${p.top.join(', ')}</div>`:''}`);
      d3.select(e.currentTarget).attr('stroke','#222').attr('stroke-width',1).raise();
    })
    .on('mouseleave',(e)=>{tip.style('opacity',0);d3.select(e.currentTarget).attr('stroke','#fff').attr('stroke-width',0.25);});
  return {color:window.leanColor};
};

/* ---------- STORE DOT-MAP: locales as points over a faint political choropleth ---------- */
window.DOM_COLOR = {0:'#3f9b6e', 1:'#d9962f', 2:'#7a5ea8', 3:'#c8453a', 4:'#3a6ea5'};   // tiendas / comida / servicios / moda / automotriz
window.drawStoreMap = function(mount){
  const geo=window.GEO_MUNI, pts=window.GEO_STORES, sub=window.GEO_AGG.meta.subcats, DOM=window.GEO_AGG.meta.domains;
  const W=720,H=820;
  const svg=d3.select(mount).append('svg').attr('viewBox',`0 0 ${W} ${H}`);
  const proj=d3.geoMercator().fitSize([W,H],geo); const path=d3.geoPath(proj);
  const tip=d3.select('#tip');
  // faint political base
  svg.append('g').selectAll('path').data(geo.features).join('path')
    .attr('d',path)
    .attr('fill',d=>d3.interpolateRgb(leanColor(d.properties.lean*100),'#ffffff')(0.55))
    .attr('stroke','#fff').attr('stroke-width',0.25)
    .style('cursor','pointer')
    .on('mousemove',(e,d)=>{const p=d.properties,pts=p.lean*100;
      tip.style('opacity',1).style('left',(e.clientX+14)+'px').style('top',(e.clientY+12)+'px')
        .html(`<div class="b">${p.name}</div><div class="m">${p.dept}</div>
          <div style="margin-top:3px;color:${col(pts)}">${fmt(pts)} pts</div>
          ${p.top&&p.top.length?`<div class="m" style="margin-top:3px">${p.top.join(', ')}</div>`:''}`);})
    .on('mouseleave',()=>tip.style('opacity',0));
  const dotG=svg.append('g').style('pointer-events','none');
  function colorOf(d,si,dom){ return dom==null ? DOM_COLOR[d] : SUBCAT_COLORS[si%SUBCAT_COLORS.length]; }
  function render(domIdx){
    const data = domIdx==null ? pts : pts.filter(p=>p[2]===domIdx);
    const sel=dotG.selectAll('circle').data(data,(d,i)=>i);
    sel.join(
      en=>en.append('circle').attr('cx',d=>proj([d[0],d[1]])[0]).attr('cy',d=>proj([d[0],d[1]])[1])
            .attr('r',2.1).attr('fill',d=>colorOf(d[2],d[3],domIdx)).attr('fill-opacity',.8).attr('stroke','#fff').attr('stroke-width',.3),
      up=>up.attr('fill',d=>colorOf(d[2],d[3],domIdx)),
      ex=>ex.remove());
  }
  render(null);
  return {setDomain:render, sub, DOM};
};
})();
