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
 const target=document.getElementById('sg-watchcards');if(!target||!d||!Array.isArray(d.candidates))return;
 const valid=d.candidates.filter(x=>/^[A-Z]{4,5}$/.test(x.ticker)&&Number.isFinite(Number(x.close))&&x.date&&x.pattern&&x.checks&&Object.values(x.checks).every(Boolean)).slice(0,3);
 text('sg-watch-timestamp',valid.length?'Data penutupan '+dateLabel(d.asof):'Menunggu data EOD valid');
 if(!valid.length)return;
 target.replaceChildren();
 for(let i=0;i<valid.length;i++){
  const x=valid[i],card=create('article','sg-watchcard');card.append(create('span','sg-rank','KANDIDAT TEKNIKAL #'+(i+1)),create('h3','',x.ticker),create('strong','sg-cardprice','Rp'+rupiah(Number(x.close))),create('div','sg-cardmeta','Penutupan '+dateLabel(x.date)+' · Skor '+x.score+'/100'));
  card.append(create('div','sg-rule','Stoch K/D '+x.k+' / '+x.d+' · MA5 '+rupiah(x.ma5)+' · MA20 '+rupiah(x.ma20)+' · Volume '+x.volume_ratio+'× · '+x.pattern));
  target.append(card);
 }
 // Google may render client-side text; server-side title and description stay stable and editorial.
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
 refreshSGPanels();
 window.setInterval(refreshSGPanels,60*60*1000);
});
})();
