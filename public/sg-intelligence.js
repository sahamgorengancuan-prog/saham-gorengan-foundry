/* SahamGorengan intelligence: safe, no HTML injection from Telegram or data feeds. */
(()=>{'use strict';
const rupiah=v=>new Intl.NumberFormat('id-ID',{maximumFractionDigits:0}).format(v);
const pct=v=>(v>0?'+':'')+new Intl.NumberFormat('id-ID',{maximumFractionDigits:2}).format(v)+'%';
const text=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v};
function create(tag,cls,value){let x=document.createElement(tag);if(cls)x.className=cls;if(value!==undefined)x.textContent=value;return x}
function dateLabel(s){try{return new Date(s).toLocaleString('id-ID',{day:'numeric',month:'long',year:'numeric',timeZone:'Asia/Jakarta'})}catch{return s||'—'}}
async function load(url){const r=await fetch(url+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('unavailable');return r.json()}
function performance(d){
 if(d.schema!==1||!Array.isArray(d.entries))return;
 const nums=d.entries.map(v=>Number(v.pct));
 if(!nums.every(Number.isFinite))return;
 const hasRows=nums.length>0;
 if(hasRows&&Math.abs(nums.reduce((a,b)=>a+b,0)-Number(d.total_pct))>.02)return;
 const total=hasRows?nums.reduce((a,b)=>a+b,0):Number(d.total_pct);
 const average=hasRows?total/nums.length:Number(d.average_pct);
 if(!Number.isFinite(total)||!Number.isFinite(average))return;
 text('sg-perf-total',pct(total));
 text('sg-perf-avg',pct(average));
 const winners=hasRows?nums.filter(x=>x>0).length:d.wins;
 const count=hasRows?nums.length:d.count;
 text('sg-perf-wins',Number.isFinite(Number(winners))&&Number.isFinite(Number(count))&&count>0?winners+' / '+count:'Belum dirinci');
 text('sg-perf-period',d.period||'Laporan mingguan');
 text('sg-perf-label',hasRows?'Laporan pemilik · dihitung ulang':'Ringkasan pemilik · belum terverifikasi');
 const grid=document.getElementById('sg-perf-pills');grid.replaceChildren();
 if(!hasRows)grid.append(create('span','sg-pill','Rincian ticker belum disertakan'));
 d.entries.slice(0,12).forEach(e=>{if(!/^[A-Z]{4,5}$/.test(e.ticker))return;grid.append(create('span','sg-pill'+(Number(e.pct)<0?' neg':''),e.ticker+'  '+pct(Number(e.pct))))});
 const note=document.getElementById('sg-perf-note');if(note)note.textContent=d.disclaimer||'Akumulasi bukan return portofolio. Performa historis tidak menjamin hasil masa depan.';
}
function watch(d){
 const target=document.getElementById('sg-watchcards');
 if(!target||!d||d.schema!==1||d.format!=='ticker_only'||!Array.isArray(d.candidates))return;
 // No price, volume, indicator or score is read, rendered or persisted client-side.
 if(!['authorized_private_backend','provisional_backend_permission_pending'].includes(d.source)||d.status!=='ready')return;
 const names=[...new Set(d.candidates.map(x=>String(x?.ticker||'')))].filter(x=>/^[A-Z]{4,5}$/.test(x)).slice(0,3);
 if(!names.length)return;
 target.replaceChildren();
 names.forEach((ticker,i)=>{
  const card=create('article','sg-watchcard sg-watchcard-ticker');
  card.append(create('span','sg-rank','RADAR #'+(i+1)),
              create('h3','sg-ticker-code',ticker));
  target.append(card);
 });
}

function scanStatus(d){
 if(!d||d.schema!==1||d.frequency!=='hourly')return;
 const when=String(d.generated_at||'').slice(0,16).replace('T',' · ');
 const scanned=Math.max(0,Number(d.universe_count)||0);
 const eligible=Math.max(0,Number(d.qualifying_count)||0);
 const label=document.getElementById('sg-watch-timestamp');
 const stamp=Date.parse(String(d.generated_at||''));
 const isStale=!Number.isFinite(stamp)||Date.now()-stamp>3*60*60*1000||stamp>Date.now()+5*60*1000;
 if(isStale){
  if(label)label.textContent='Pembaruan tertunda · audit terakhir '+when+' WIB';
  const cards=document.getElementById('sg-watchcards');
  if(cards){
   cards.replaceChildren();
   const box=create('div','sg-watch-empty');
   box.append(create('strong','','Pembaruan data sedang tertunda'),
              create('p','','Audit terakhir sudah melewati batas 3 jam. Kandidat lama disembunyikan sampai pembaruan berikutnya terverifikasi.'));
   cards.append(box);
  }
  return;
 }
 if(label)label.textContent='Audit '+when+' WIB · '+scanned+' saham diperiksa';
 const empty=document.querySelector('#sg-watchcards .sg-watch-empty');
 if(empty){
  const head=empty.querySelector('strong'),msg=empty.querySelector('p');
  if(scanned===0){
   if(head)head.textContent='Radar aktif · data pasar belum terhubung';
   if(msg)msg.textContent='Pemeriksaan otomatis setiap jam sudah aktif, tetapi feed OHLCV berizin belum tersedia. Tidak ada saham yang direkayasa atau diterbitkan sebelum data valid.';
  }else if(eligible===0){
   if(head)head.textContent=scanned+' saham diperiksa · belum ada sinyal lengkap';
   if(msg)msg.textContent='Tidak ada saham yang memenuhi seluruh syarat Stochastic 8-3-3, MA5, MA20, volume dan candle bullish pada pemeriksaan terakhir.';
  }
 }
}
function refreshSGPanels(){
 Promise.allSettled([load('/data/sg-performance.json'),load('/data/sg-watchlist.json'),load('/data/sg-status.json')]).then(out=>{
  if(out[0].status==='fulfilled')performance(out[0].value);
  if(out[1].status==='fulfilled')watch(out[1].value);
  if(out[2].status==='fulfilled')scanStatus(out[2].value);
  else scanStatus({schema:1,frequency:'hourly',generated_at:'',universe_count:0,qualifying_count:0});
 });
}
document.addEventListener('DOMContentLoaded',()=>{
 initMobileUX();
 initYouTubeCinema();
 refreshSGPanels();
 window.setInterval(refreshSGPanels,60*60*1000);
});

function initMobileUX(){
 const trigger=document.querySelector('.sg-menu-trigger');
 const menu=document.getElementById('sg-mobile-nav');
 const scrim=document.querySelector('.sg-menu-scrim');
 const dock=[...document.querySelectorAll('.sg-mobile-dock a[data-dock]')];
 if(!trigger||!menu||!scrim||!dock.length)return;
 let expanded=false;
 function toggle(open,restore=false){
  expanded=!!open;
  menu.classList.toggle('sg-open',expanded);
  document.documentElement.classList.toggle('sg-menu-open',expanded);
  trigger.setAttribute('aria-expanded',String(expanded));
  trigger.setAttribute('aria-label',expanded?'Tutup menu navigasi':'Buka menu navigasi');
  scrim.tabIndex=expanded?0:-1;
  if(expanded){const first=menu.querySelector('a');if(first)first.focus({preventScroll:true})}
  else if(restore)trigger.focus({preventScroll:true});
 }
 trigger.addEventListener('click',()=>toggle(!expanded,!expanded));
 scrim.addEventListener('click',()=>toggle(false,true));
 menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>toggle(false)));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&expanded)toggle(false,true)});
 const desktop=window.matchMedia('(min-width:1001px)');
 if(desktop.addEventListener)desktop.addEventListener('change',e=>{if(e.matches)toggle(false)});
 else if(desktop.addListener)desktop.addListener(e=>{if(e.matches)toggle(false)});
 // Lightweight scroll spy: dock is four predictable one-tap anchors.
 const ids=['home','performa-mingguan','watchlist-teknikal','youtube','premium'];
 let queued=false;
 function setActive(){
  queued=false;
  let current='home';
  for(const id of ids){
   const el=document.getElementById(id);
   if(el&&el.getBoundingClientRect().top<innerHeight*.45)current=id;
  }
  for(const a of dock){
   const active=a.dataset.dock===current;
   a.classList.toggle('is-active',active);
   if(active)a.setAttribute('aria-current','location');
   else a.removeAttribute('aria-current');
  }
 }
 function schedule(){
  if(queued)return;
  queued=true;
  requestAnimationFrame(setActive);
 }
 document.addEventListener('scroll',schedule,{passive:true});
 window.addEventListener('resize',schedule,{passive:true});
 window.addEventListener('hashchange',()=>{toggle(false);schedule()});
 schedule();
}


/* YouTube Cinema: RSS-backed, lazy, muted, viewport-only playback.
   YouTube's embed and browser rules control whether autoplay is permitted.
   Native controls and open-in-YouTube links always remain available. */
function initYouTubeCinema(){
 const host=document.getElementById('youtube');
 const track=document.getElementById('sg-yt-track');
 const raw=document.getElementById('sg-youtube-feed');
 if(!host||!track||!raw)return;
 let catalog;
 try{catalog=JSON.parse(raw.textContent)}catch{return}
 if(catalog?.schema!==1||catalog?.channel_id!=='UCZ8_zgmlXXlNqGfOJwD__jw'||!catalog?.videos)return;
 const tabs=[...host.querySelectorAll('.sg-yt-tab')];
 const arrows=[...host.querySelectorAll('.sg-yt-arrow')];
 const sections={latest:'Video terbaru',trending:'Video trending',relevant:'Video relevan'};
 let category='latest',activeCard=null,activeFrame=null,lastManualId='',queued=false;
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 const observed=window.matchMedia('(max-width:640px)');
 let io=null;
 const safeVideo=v=>v&&/^[A-Za-z0-9_-]{11}$/.test(v.id)&&typeof v.title==='string';
 const make=(tag,cls,txt)=>{
  const el=document.createElement(tag);
  if(cls)el.className=cls;
  if(txt!==undefined)el.textContent=txt;
  return el;
 };
 const formatViews=n=>Number(n).toLocaleString('id-ID')+' tayangan';
 const formatDate=str=>{
  try{return new Date(str).toLocaleDateString('id-ID',{day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Jakarta'})}
  catch{return '';}
 };
 function stop(){
  if(activeFrame){
   // Destroy the embedded player so audio/video cannot continue offscreen.
   activeFrame.remove();activeFrame=null;
  }
  if(activeCard){
   activeCard.classList.remove('sg-yt-playing');
   activeCard=null;
  }
 }
 function start(card,manual=false){
  const id=card?.dataset?.id;
  if(!/^[A-Za-z0-9_-]{11}$/.test(id||''))return;
  if(document.hidden)return;
  if(activeCard===card)return;
  stop();
  const frame=card.querySelector('.sg-yt-frame');
  if(!frame)return;
  const iframe=document.createElement('iframe');
  iframe.title='Pemutar YouTube '+(card.querySelector('h3')?.textContent||id);
  iframe.setAttribute('allow','autoplay; encrypted-media; picture-in-picture; web-share');
  iframe.setAttribute('allowfullscreen','');
  iframe.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  iframe.setAttribute('loading','eager');
  iframe.src='https://www.youtube-nocookie.com/embed/'+id+
   '?autoplay=1&mute=1&playsinline=1&controls=1&enablejsapi=1&rel=0&origin='+encodeURIComponent(location.origin);
  frame.append(iframe);
  card.classList.add('sg-yt-playing');
  activeFrame=iframe;activeCard=card;
  if(manual)lastManualId=id;
 }
 function buildCard(v,i){
  const card=make('article','sg-yt-card');
  card.dataset.id=v.id;
  const frame=make('div','sg-yt-frame');
  const img=document.createElement('img');
  img.src='https://i.ytimg.com/vi/'+v.id+'/hqdefault.jpg';
  img.alt='Thumbnail: '+v.title;
  img.loading=i<2?'eager':'lazy';img.decoding='async';
  img.referrerPolicy='no-referrer';
  img.addEventListener('error',()=>{img.src='https://i.ytimg.com/vi/'+v.id+'/mqdefault.jpg'},{once:true});
  const play=make('button','sg-yt-play');
  play.type='button';play.setAttribute('aria-label','Putar '+v.title);
  play.append(make('span','','▶'));
  play.addEventListener('click',()=>{
   lastManualId=v.id;
   start(card,true);
  });
  frame.append(img,play,make('span','sg-yt-flag','VIDEO'));
  const info=make('div','sg-yt-info');
  info.append(make('span','sg-yt-meta',formatDate(v.date)+' · '+formatViews(v.views)));
  info.append(make('h3','',v.title));
  const link=make('a','sg-yt-open','Tonton di YouTube ↗');
  link.href='https://www.youtube.com/watch?v='+v.id;
  link.target='_blank';link.rel='noopener noreferrer';
  info.append(link);
  card.append(frame,info);
  return card;
 }
 function render(next){
  const items=catalog.videos[next];
  if(!Array.isArray(items))return;
  stop();lastManualId='';
  category=next;
  tabs.forEach(tab=>{
   const on=tab.dataset.category===next;
   tab.classList.toggle('is-selected',on);
   tab.setAttribute('aria-selected',String(on));
   tab.tabIndex=on?0:-1;
  });
  const fresh=items.filter(safeVideo).slice(0,6).map(buildCard);
  if(!fresh.length)return;
  track.replaceChildren(...fresh);
  track.setAttribute('aria-label',sections[next]||'Video YouTube');
  track.scrollTo({left:0,behavior:'instant'});
  updateArrows();
  watchCards();
  schedule();
 }
 function updateArrows(){
  const max=track.scrollWidth-track.clientWidth;
  for(const arrow of arrows){
   const direction=Number(arrow.dataset.direction);
   arrow.disabled=max<5||(direction<0?track.scrollLeft<3:track.scrollLeft>=max-3);
  }
 }
 function canPlay(card){
  if(document.hidden||!card||!host.isConnected)return false;
  const box=card.querySelector('.sg-yt-frame')?.getBoundingClientRect();
  const section=host.getBoundingClientRect();
  const clip=track.getBoundingClientRect();
  if(!box||section.bottom<110||section.top>innerHeight-80)return false;
  const xmin=Math.max(box.left,clip.left,0);
  const xmax=Math.min(box.right,clip.right,innerWidth);
  const ymin=Math.max(box.top,0);
  const ymax=Math.min(box.bottom,innerHeight);
  const visibleW=Math.max(0,xmax-xmin),visibleH=Math.max(0,ymax-ymin);
  return box.width>=200&&box.height>=200&&
      visibleW/box.width>=.64&&visibleH/box.height>=.67;
 }
 function reconcile(){
  queued=false;
  if(document.hidden){stop();return}
  const cards=[...track.querySelectorAll('.sg-yt-card')];
  const visible=cards.filter(canPlay);
  if(!visible.length){stop();lastManualId='';return}
  const active=activeCard;
  if(active&&visible.includes(active))return;
  const mid=Math.max(0,(innerWidth||320)/2);
  visible.sort((a,b)=>Math.abs(a.getBoundingClientRect().left+a.offsetWidth/2-mid)-
                     Math.abs(b.getBoundingClientRect().left+b.offsetWidth/2-mid));
  if(visible[0]?.dataset.id===lastManualId)return;
  start(visible[0]);
 }
 function schedule(){
  if(queued)return;
  queued=true;
  window.requestAnimationFrame(reconcile);
 }
 function watchCards(){
  if(io){io.disconnect();io=null}
  if('IntersectionObserver' in window){
   io=new IntersectionObserver(schedule,{threshold:[0,.4,.67,.95]});
   io.observe(host);
   track.querySelectorAll('.sg-yt-card').forEach(el=>io.observe(el));
  }
 }
 tabs.forEach(tab=>tab.addEventListener('click',()=>render(tab.dataset.category)));
 const tabset=host.querySelector('.sg-yt-tabs');
 tabset?.addEventListener('keydown',e=>{
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
  e.preventDefault();
  const idx=tabs.findIndex(t=>t.dataset.category===category);
  const next=e.key==='Home'?0:e.key==='End'?tabs.length-1:
   (idx+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
  tabs[next]?.focus();tabs[next]?.click();
 });
 arrows.forEach(arrow=>arrow.addEventListener('click',()=>{
  const first=track.querySelector('.sg-yt-card');
  const step=(first?.getBoundingClientRect().width||track.clientWidth*.85)+15;
  track.scrollBy({left:step*Number(arrow.dataset.direction),behavior:reduced.matches?'instant':'smooth'});
 }));
 track.addEventListener('scroll',()=>{updateArrows();schedule()},{passive:true});
 window.addEventListener('scroll',schedule,{passive:true});
 window.addEventListener('resize',()=>{updateArrows();schedule()},{passive:true});
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();else schedule()});
 window.addEventListener('pagehide',stop);
 // Initial thumbnails remain useful without API/JS; runtime upgrades to interactive tabs.
 render(category);
}

})();
