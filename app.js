if(window.top!==window.self){document.documentElement.style.display='none';try{window.top.location.replace(window.self.location.href)}catch(e){}}
'use strict';
// The English home page is a separate static page (/en/, built by tools/build_en_home.py);
// the language follows the page.
const lang = document.documentElement.lang === 'en' ? 'en' : 'uk';
const mobileBtn=document.getElementById('menuToggle');const mobileNav=document.getElementById('mobileNav');
mobileBtn?.addEventListener('click',()=>{const next=mobileBtn.getAttribute('aria-expanded')!=='true';mobileBtn.setAttribute('aria-expanded',String(next));mobileBtn.setAttribute('aria-label',next?'Закрити меню':'Відкрити меню');mobileNav.classList.toggle('is-open',next);});
mobileNav?.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{mobileNav.classList.remove('is-open');mobileBtn.setAttribute('aria-expanded','false');}));
const progress=document.getElementById('readingProgress');
let ticking=false;
window.addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(()=>{const height=document.documentElement.scrollHeight-innerHeight;progress.style.width=(height>0?(scrollY/height*100):0)+'%';ticking=false;});ticking=true;}},{passive:true});
if('IntersectionObserver' in window){const obs=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');obs.unobserve(e.target)}})},{threshold:.07});document.querySelectorAll('[data-reveal]').forEach(el=>obs.observe(el));}else{document.querySelectorAll('[data-reveal]').forEach(el=>el.classList.add('visible'));}
document.getElementById('year').textContent=new Date().getFullYear();
function feedback(form,message){const el=document.getElementById(form.id==='towerForm'?'towerFeedback':'partnerFeedback');el.textContent=message;el.scrollIntoView({behavior:'smooth',block:'nearest'});}
const maxBytes=8*1024*1024;
const FORM_ENDPOINT='https://formsubmit.co/ajax/gluschenko.art@gmail.com';
for(const form of document.querySelectorAll('form[data-netlify="true"]')){
 form.dataset.openedAt=String(Date.now());
 form.addEventListener('submit',e=>{
   const isLocal=location.protocol==='file:'||['localhost','127.0.0.1'].includes(location.hostname);
   if(form.id==='towerForm'){
     const files=Array.from(form.querySelectorAll('input[type=file]')).flatMap(input=>Array.from(input.files));
     const total=files.reduce((sum,f)=>sum+f.size,0);
     if(total>maxBytes){e.preventDefault();feedback(form,lang==='uk'?'Сумарний розмір файлів перевищує 8 МБ. Використайте посилання на архів або зменште файли.':'Total attachments exceed 8 MB. Please use a cloud-folder link or smaller files.');return;}
   }
   if(isLocal){e.preventDefault();feedback(form,lang==='uk'?'Це локальна демонстрація. Форми працюють лише на опублікованому сайті.':'This is a local preview. Forms work only on the published site.');return;}
   // Secure AJAX submission (FormSubmit delivers imwt.space submissions only via its AJAX endpoint)
   e.preventDefault();
   if(form.dataset.sending==='1') return;
   const uk=lang==='uk';
   const hp=form.querySelector('input[name="_honey"]');
   const tooFast=(Date.now()-(Number(form.dataset.openedAt)||0))<3000;
   if((hp&&hp.value)||tooFast){ location.href='/success.html'; return; }
   const btn=form.querySelector('button[type="submit"]');
   form.dataset.sending='1'; if(btn){btn.disabled=true;btn.setAttribute('aria-busy','true');}
   feedback(form,uk?'Надсилаємо…':'Sending…');
   const data=new FormData(form);
   for(const k of ['_captcha','_next','form-name','website','company_website']) data.delete(k);
   for(const [k,v] of [...data.entries()]){ if(v instanceof File && v.size===0) data.delete(k); }
   const ctrl=new AbortController(); const timer=setTimeout(()=>ctrl.abort(),45000);
   fetch(FORM_ENDPOINT,{method:'POST',headers:{'Accept':'application/json'},body:data,signal:ctrl.signal,referrerPolicy:'strict-origin-when-cross-origin'})
    .then(r=>r.json().catch(()=>({})).then(j=>({ok:r.ok,j})))
    .then(({ok,j})=>{ if(ok&&String(j.success)==='true'){ location.href='/success.html'; } else { throw new Error(j.message||'send failed'); } })
    .catch(()=>{ feedback(form,uk?'Не вдалося надіслати. Спробуйте ще раз або напишіть нам: gluschenko.art@gmail.com':'Could not send. Please try again or email us: gluschenko.art@gmail.com'); })
    .finally(()=>{ clearTimeout(timer); form.dataset.sending='0'; if(btn){btn.disabled=false;btn.removeAttribute('aria-busy');} });
 });
}
