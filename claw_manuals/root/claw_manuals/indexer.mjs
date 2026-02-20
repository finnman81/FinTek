import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

const base = '/data/.openclaw/workspace/water_manuals_dataset';
const jsonPath = path.join(base, 'manual_index.json');
const csvPath  = path.join(base, 'manual_index.csv');

function loadIndex(){
  if(!fs.existsSync(jsonPath)) return [];
  const txt = fs.readFileSync(jsonPath,'utf8').trim();
  if(!txt) return [];
  return JSON.parse(txt);
}
function saveIndex(idx){
  fs.writeFileSync(jsonPath, JSON.stringify(idx,null,2)+'\n','utf8');
  saveCsv(idx);
}
function csvEscape(v){
  if(v===null||v===undefined) return '';
  const s = String(v);
  if(/[\n",]/.test(s)) return '"'+s.replace(/"/g,'""')+'"';
  return s;
}
function saveCsv(idx){
  const headers = ['id','category','org','brand','title','model_or_series','doc_type','language','publication_date','file_name','relative_path','pages','sha256','file_bytes','primary_url','alt_urls'];
  const lines = [headers.join(',')];
  for(const e of idx){
    const row = headers.map(h=>{
      if(h==='alt_urls') return JSON.stringify(e.alt_urls||[]);
      return e[h] ?? '';
    }).map(csvEscape).join(',');
    lines.push(row);
  }
  fs.writeFileSync(csvPath, lines.join('\n')+'\n','utf8');
}

function sha256File(p){
  const h = crypto.createHash('sha256');
  const fd = fs.openSync(p,'r');
  const buf = Buffer.allocUnsafe(1024*1024);
  let bytes=0;
  while(true){
    const n = fs.readSync(fd, buf, 0, buf.length, null);
    if(n<=0) break;
    bytes += n;
    h.update(buf.subarray(0,n));
  }
  fs.closeSync(fd);
  return {sha256:h.digest('hex'), bytes};
}

// Heuristic page count: count occurrences of '/Type /Page' excluding '/Pages'
function pageCountHeuristic(p){
  const data = fs.readFileSync(p);
  const txt = data.toString('latin1');
  const m = txt.match(/\/Type\s*\/Page\b/g);
  return m ? m.length : '';
}

function nextId(idx){
  let max=0;
  for(const e of idx){
    const m = String(e.id||'').match(/M(\d+)/);
    if(m) max = Math.max(max, parseInt(m[1],10));
  }
  return 'M'+String(max+1).padStart(4,'0');
}

function relFromBase(p){
  const rel = path.relative(base,p);
  return rel.startsWith('..') ? p : rel;
}

function addEntry(args){
  const idx = loadIndex();
  const {sha256, bytes} = sha256File(args.file_path);
  const pages = pageCountHeuristic(args.file_path);

  const existing = idx.find(e => e.sha256 === sha256);
  if(existing){
    const url = args.primary_url;
    existing.alt_urls = Array.from(new Set([...(existing.alt_urls||[]), url].filter(Boolean)));
    saveIndex(idx);
    return {status:'deduped', id: existing.id, sha256, pages, bytes};
  }

  const id = nextId(idx);
  const entry = {
    id,
    category: args.category,
    org: args.org,
    brand: args.brand || '',
    title: args.title,
    model_or_series: args.model_or_series || '',
    doc_type: args.doc_type || 'manual',
    language: args.language || 'en',
    publication_date: args.publication_date || '',
    file_name: path.basename(args.file_path),
    relative_path: relFromBase(args.file_path),
    pages,
    sha256,
    file_bytes: bytes,
    primary_url: args.primary_url,
    alt_urls: (args.alt_urls && args.alt_urls.length) ? args.alt_urls : []
  };
  idx.push(entry);
  saveIndex(idx);
  return {status:'added', id, sha256, pages, bytes};
}

function main(){
  const cmd = process.argv[2];
  if(cmd !== 'add'){
    console.error('Usage: node indexer.mjs add --file_path ... --category ... --org ... --title ... --primary_url ... [--brand ...] [--model_or_series ...] [--doc_type ...] [--language ...] [--publication_date ...]');
    process.exit(2);
  }
  const args = {};
  for(let i=3;i<process.argv.length;i++){
    const a = process.argv[i];
    if(a.startsWith('--')){
      const k=a.slice(2);
      const v=process.argv[i+1];
      args[k]=v;
      i++;
    }
  }
  for(const req of ['file_path','category','org','title','primary_url']){
    if(!args[req]){ console.error('Missing --'+req); process.exit(2); }
  }
  const out = addEntry(args);
  process.stdout.write(JSON.stringify(out));
}

main();
