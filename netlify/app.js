(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  let rows = [], columns = [], fileMeta = null, columnTypes = {}, quality = {};
  const numberFmt = new Intl.NumberFormat(undefined, {maximumFractionDigits: 3});
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch]));
  const display = (value) => value == null ? "" : String(value);
  const isEmpty = value => value == null || String(value).trim() === "";
  const isBlank = value => value != null && String(value).trim() === "";
  const setText = (id, value) => { $(id).textContent = value; };
  const unique = values => [...new Set(values)];
  const toNumber = value => {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (value == null) return null;
    const s = String(value).trim().replace(/[$£€₹,%\s]/g, "").replace(/,/g, "");
    if (!s || !/^[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?$/i.test(s)) return null;
    const n = Number(s); return Number.isFinite(n) ? n : null;
  };
  const getValues = col => rows.map(r => r[col]);
  function safeCsvCell(value) {
    let s = display(value);
    if (/^[\s]*[=+@]/.test(s) || /^[\s]*-[^0-9.]/.test(s)) s = "'" + s;
    return '"' + s.replace(/"/g, '""') + '"';
  }
  function download(name, data, type) {
    const blob = data instanceof Blob ? data : new Blob([data], {type});
    const url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function csvFor(dataRows, cols) {
    return [cols.map(safeCsvCell).join(","), ...dataRows.map(r => cols.map(c => safeCsvCell(r[c])).join(","))].join("\r\n");
  }
  function setBusy(message) { $("fileStatus").textContent = message; $("fileStatus").classList.remove("loaded"); }
  function fail(message) { setBusy(message); }
  function normalizeRows(input) {
    const out = [];
    for (const source of input) {
      if (!source || typeof source !== "object") continue;
      const row = {};
      for (const col of columns) {
        const v = source[col];
        row[col] = isEmpty(v) ? null : v;
      }
      if (columns.some(c => row[c] != null)) out.push(row);
    }
    return out;
  }
  function readFile(file) {
    if (file.size > 200 * 1024 * 1024) return fail("File is over the 200MB limit.");
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["csv","xlsx","xls"].includes(ext)) return fail("Choose a CSV, XLSX, or XLS file.");
    setBusy("Reading and analyzing file…");
    fileMeta = {name:file.name, type:ext.toUpperCase(), size:file.size};
    if (ext === "csv") {
      Papa.parse(file, {header:true, skipEmptyLines:"greedy", dynamicTyping:false, complete: result => {
        const parsed = result.data || [];
        columns = result.meta.fields || Object.keys(parsed[0] || {});
        if (!columns.length) return fail("The file has no column headers.");
        rows = normalizeRows(parsed); finishLoad();
      }, error: err => fail(`Could not read CSV: ${err.message}`)});
    } else {
      const reader = new FileReader();
      reader.onerror = () => fail("The file could not be read.");
      reader.onload = e => {
        try {
          const wb = XLSX.read(e.target.result, {type:"array", cellDates:true});
          const sheet = wb.Sheets[wb.SheetNames[0]];
          const data = XLSX.utils.sheet_to_json(sheet, {defval:null, raw:true});
          columns = data.length ? Object.keys(data[0]) : (XLSX.utils.sheet_to_json(sheet, {header:1})[0] || []).map(String);
          if (!columns.length) return fail("The first worksheet has no data or headers.");
          rows = normalizeRows(data); finishLoad();
        } catch (err) { fail(`Could not read workbook: ${err.message}`); }
      };
      reader.readAsArrayBuffer(file);
    }
  }
  function parseDate(value) {
    if (value instanceof Date && !Number.isNaN(value.getTime())) return value;
    if (typeof value === "number" && value > 10000 && value < 100000) {
      const d = XLSX.SSF.parse_date_code(value); if (d) return new Date(d.y,d.m-1,d.d);
    }
    const s = String(value ?? "").trim(); if (!s) return null;
    let m = s.match(/^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})$/);
    if (m) { let day=+m[1], month=+m[2]-1, year=+m[3]; if(year<100) year+=year<50?2000:1900; const d=new Date(year,month,day); return d.getFullYear()===year&&d.getMonth()===month&&d.getDate()===day?d:null; }
    const d = new Date(s); return Number.isNaN(d.getTime()) ? null : d;
  }
  function inferTypes() {
    columnTypes = {};
    for (const col of columns) {
      const vals = getValues(col).filter(v => !isEmpty(v));
      if (!vals.length) { columnTypes[col] = "category"; continue; }
      const nums = vals.filter(v => toNumber(v) !== null).length;
      const dates = vals.filter(v => parseDate(v) !== null).length;
      if (dates / vals.length >= .8 && vals.some(v => /[-/.]/.test(String(v)))) columnTypes[col] = "date";
      else if (nums / vals.length >= .8) columnTypes[col] = "number";
      else columnTypes[col] = "category";
    }
  }
  function getQuality() {
    const seen = new Set(); let duplicateRows = 0;
    for (const r of rows) { const key = JSON.stringify(columns.map(c => r[c] instanceof Date ? r[c].toISOString() : r[c])); if (seen.has(key)) duplicateRows++; else seen.add(key); }
    let missing=0, blank=0;
    quality.byColumn = columns.map(col => {
      const vals=getValues(col), miss=vals.filter(v => v == null).length, blanks=vals.filter(isBlank).length;
      missing += miss; blank += blanks;
      return {column:col, missing:miss, blank:blanks, type:columnTypes[col], unique:unique(vals.filter(v=>!isEmpty(v)).map(v=>String(v))).length};
    });
    quality.missing=missing; quality.blank=blank; quality.duplicates=duplicateRows;
  }
  function finishLoad() {
    if (!rows.length || !columns.length) return fail("No usable data rows were found in this file.");
    inferTypes(); getQuality();
    $("emptyState").hidden = true; $("workspace").hidden = false;
    $("fileStatus").textContent = `Loaded: ${fileMeta.name} · ${fileMeta.type} · ${formatBytes(fileMeta.size)}`;
    $("fileStatus").classList.add("loaded");
    setText("rowCount", numberFmt.format(rows.length)); setText("columnCount", numberFmt.format(columns.length));
    setText("missingCount", numberFmt.format(quality.missing)); setText("blankCount", numberFmt.format(quality.blank));
    setText("duplicateCount", numberFmt.format(quality.duplicates)); setText("downloadDuplicates", numberFmt.format(quality.duplicates));
    const info = [fileMeta.name,fileMeta.type,`${rows.length} × ${columns.length}`,formatBytes(fileMeta.size),"UTF-8 / detected",formatBytes(estimateMemory())];
    document.querySelectorAll("#fileInfo small b").forEach((el,i)=>el.textContent=info[i]);
    populateSelectors(); renderPreview(); renderQuality(); renderAnalysis(); renderVisualizations(); renderCorrelation();
    document.querySelectorAll(".download-card button").forEach(b=>b.disabled=false);
  }
  function formatBytes(n) { if (!n) return "0 B"; const units=["B","KB","MB","GB"]; const i=Math.min(Math.floor(Math.log(n)/Math.log(1024)),3); return `${(n/1024**i).toFixed(i?1:0)} ${units[i]}`; }
  function estimateMemory() { try{return new Blob([JSON.stringify(rows)]).size;}catch{return 0;} }
  function renderPreview() {
    const query=$("searchInput").value.trim().toLowerCase(), limit=Number($("rowLimit").value)||10;
    const filtered=query?rows.filter(r=>columns.some(c=>display(r[c]).toLowerCase().includes(query))):rows;
    const shown=filtered.slice(0,limit), table=$("previewTable");
    table.innerHTML=`<thead><tr><th>#</th>${columns.map(c=>`<th>${escapeHtml(c)}</th>`).join("")}</tr></thead><tbody>${shown.map(r=>`<tr><th>${rows.indexOf(r)+1}</th>${columns.map(c=>`<td class="${columnTypes[c]==="number"?"num":""}">${escapeHtml(display(r[c]))}</td>`).join("")}</tr>`).join("")}</tbody>`;
    let caption=`Showing ${shown.length} of ${filtered.length} matching rows · ${columns.length} columns`;
    if(filtered.length>limit) caption+=` · Increase “Show rows” to see more`;
    document.querySelector("#panel-preview .caption").textContent=caption+". Empty file cells count as missing; whitespace-only text counts as blank.";
  }
  function renderQuality() {
    $("qualityTable").innerHTML=`<thead><tr><th>Column</th><th>Detected type</th><th>Missing values</th><th>Blank cells</th><th>Unique values</th></tr></thead><tbody>${quality.byColumn.map(q=>`<tr><th>${escapeHtml(q.column)}</th><td>${escapeHtml(q.type)}</td><td class="num">${q.missing}</td><td class="num">${q.blank}</td><td class="num">${q.unique}</td></tr>`).join("")}</tbody>`;
  }
  function fillSelect(id, opts, selected) {
    const el=$(id), old=selected ?? el.value; el.innerHTML=opts.map(c=>`<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
    if(opts.includes(old)) el.value=old;
  }
  function populateSelectors() {
    const numeric=columns.filter(c=>columnTypes[c]==="number"), cats=columns.filter(c=>columnTypes[c]==="category"), dates=columns.filter(c=>columnTypes[c]==="date");
    const select=(id,list)=>{fillSelect(id,list.length?list:columns);$(id).disabled=!list.length;};
    select("numberSelect",numeric); select("trendSelect",numeric); select("categorySelect",cats); select("dateSelect",dates); select("xSelect",numeric); select("ySelect",numeric.filter(c=>c!==$("xSelect").value));
  }
  function statsFor(col) {
    const vals=getValues(col).map(toNumber).filter(v=>v!==null).sort((a,b)=>a-b), n=vals.length;
    if(!n)return null;
    const mean=vals.reduce((a,b)=>a+b,0)/n, median=n%2?vals[(n-1)/2]:(vals[n/2-1]+vals[n/2])/2;
    const variance=vals.reduce((s,v)=>s+(v-mean)**2,0)/n;
    return {count:n,sum:vals.reduce((a,b)=>a+b,0),mean,min:vals[0],max:vals[n-1],median,std:Math.sqrt(variance),q1:vals[Math.floor((n-1)*.25)],q3:vals[Math.floor((n-1)*.75)]};
  }
  function renderAnalysis() {
    const nums=columns.filter(c=>columnTypes[c]==="number"), cats=columns.filter(c=>columnTypes[c]==="category"), dates=columns.filter(c=>columnTypes[c]==="date");
    fillSelect("numberSelect",nums.length?nums:columns); fillSelect("categorySelect",cats.length?cats:columns); fillSelect("dateSelect",dates.length?dates:columns);
    fillSelect("trendSelect",nums.length?nums:columns);
    const col=$("numberSelect").value, stat=statsFor(col), el=$("numberStats");
    if(!stat){el.innerHTML="<p>No numeric values were detected.</p>";$("numberSummary").textContent="";} else {
      el.innerHTML=[["Total",stat.sum],["Average",stat.mean],["Smallest",stat.min],["Largest",stat.max]].map(([k,v])=>`<div class="stat-card"><span>${k}</span><strong>${numberFmt.format(v)}</strong></div>`).join("");
      $("numberSummary").textContent=`For ${col}, the average is ${numberFmt.format(stat.mean)}; values range from ${numberFmt.format(stat.min)} to ${numberFmt.format(stat.max)}.`;
    }
    $("allStatsTable").innerHTML=`<thead><tr><th>Column</th><th>Count</th><th>Average</th><th>Median</th><th>Smallest</th><th>Largest</th><th>Std. deviation</th></tr></thead><tbody>${nums.map(c=>{const s=statsFor(c);return `<tr><th>${escapeHtml(c)}</th><td>${s.count}</td><td class="num">${numberFmt.format(s.mean)}</td><td class="num">${numberFmt.format(s.median)}</td><td class="num">${numberFmt.format(s.min)}</td><td class="num">${numberFmt.format(s.max)}</td><td class="num">${numberFmt.format(s.std)}</td></tr>`}).join("")}</tbody>`;
    renderCategoryChart(); renderTrend();
  }
  const chartLayout=(title)=>({title:{text:title,x:.02,font:{size:18}},paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{color:getComputedStyle(document.body).getPropertyValue("--ink").trim()},margin:{t:58,r:24,b:60,l:60},xaxis:{gridcolor:"#c8d1df",automargin:true},yaxis:{gridcolor:"#c8d1df",automargin:true},autosize:true});
  const chartConfig={responsive:true,displaylogo:false,toImageButtonOptions:{format:"png",filename:"datalens-chart",height:800,width:1200,scale:2}};
  function plot(id,data,layout) { if(window.Plotly) Plotly.react(id,data,layout,chartConfig); }
  function renderCategoryChart() {
    const col=$("categorySelect").value, counts=new Map(); if(!col)return;
    for(const r of rows){const v=r[col];if(!isEmpty(v))counts.set(String(v),(counts.get(String(v))||0)+1);}
    const top=[...counts.entries()].sort((a,b)=>b[1]-a[1]).slice(0,5);
    plot("categoryChart",[{type:"bar",x:top.map(x=>x[0]),y:top.map(x=>x[1]),marker:{color:["#4787e8","#b04de0","#e6a039","#39a982","#da5f84"]},hovertemplate:"%{x}<br>%{y} rows<extra></extra>"}],{...chartLayout("Most common values · "+col),xaxis:{...chartLayout("").xaxis,title:"Category"},yaxis:{...chartLayout("").yaxis,title:"Rows"}});
  }
  function renderTrend() {
    const dateCol=$("dateSelect").value, numCol=$("trendSelect").value; if(!dateCol||!numCol)return;
    const sums=new Map();
    for(const r of rows){const d=parseDate(r[dateCol]),n=toNumber(r[numCol]);if(!d||n===null)continue;const key=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;sums.set(key,(sums.get(key)||0)+n);}
    const sorted=[...sums.entries()].sort((a,b)=>a[0].localeCompare(b[0]));
    plot("trendChart",[{type:"scatter",mode:"lines+markers",x:sorted.map(x=>x[0]),y:sorted.map(x=>x[1]),line:{color:"#8351d4",width:3},marker:{size:8},hovertemplate:"%{x}<br>Total: %{y:,.3f}<extra></extra>"}],{...chartLayout(`Monthly ${numCol} total`),xaxis:{title:"Month",gridcolor:"#c8d1df"},yaxis:{title:numCol,gridcolor:"#c8d1df"}});
  }
  function renderVisualizations() {
    const nums=columns.filter(c=>columnTypes[c]==="number");
    fillSelect("xSelect",nums.length?nums:columns); fillSelect("ySelect",nums.filter(c=>c!==$("xSelect").value).length?nums.filter(c=>c!==$("xSelect").value):nums);
    const x=$("xSelect").value,y=$("ySelect").value,type=$("chartType").value;
    const hint={scatter:"Each dot is one row. Its place shows the two numbers for that row.",bar:"Each bar is one row. Taller bars mean bigger values.",line:"Follow the line from left to right. Higher points mean bigger values.",histogram:"Each bar counts how many rows have values in that range.",box:"The box shows the middle range; the line marks the median."};
    $("chartHint").textContent=hint[type];
    const xv=getValues(x).map((v,i)=>({i,v:toNumber(v)})).filter(o=>o.v!==null), yv=getValues(y).map(toNumber);
    let trace, layout=chartLayout(`${x} vs ${y}`);
    if(type==="histogram"){trace={type:"histogram",x:xv.map(o=>o.v),marker:{color:"#8b5cf6"},hovertemplate:"Range: %{x}<br>Rows: %{y}<extra></extra>"};layout={...layout,title:{text:`Distribution of ${x}`,x:.02},xaxis:{title:x,gridcolor:"#c8d1df"},yaxis:{title:"Rows",gridcolor:"#c8d1df"}};}
    else if(type==="box"){trace={type:"box",y:xv.map(o=>o.v),name:x,marker:{color:"#8b5cf6"},boxmean:true};layout={...layout,title:{text:`Range of ${x}`,x:.02},yaxis:{title:x,gridcolor:"#c8d1df"}};}
    else {const pts=xv.filter(o=>yv[o.i]!==null);trace={type:type==="bar"?"bar":"scatter",mode:type==="line"?"lines+markers":"markers",x:pts.map(o=>o.v),y:pts.map(o=>yv[o.i]),marker:{color:"#5487d6",size:9},line:{color:"#8351d4",width:2},customdata:pts.map(o=>o.i+1),hovertemplate:`Row %{customdata}<br>${escapeHtml(x)}: %{x}<br>${escapeHtml(y)}: %{y}<extra></extra>`};layout={...layout,xaxis:{title:x,gridcolor:"#c8d1df"},yaxis:{title:y,gridcolor:"#c8d1df"}};}
    plot("mainChart",[trace],layout);
  }
  function pearson(a,b) {
    const pairs=[];for(let i=0;i<rows.length;i++){const x=toNumber(rows[i][a]),y=toNumber(rows[i][b]);if(x!==null&&y!==null)pairs.push([x,y]);}
    if(pairs.length<2)return null;const mx=pairs.reduce((s,p)=>s+p[0],0)/pairs.length,my=pairs.reduce((s,p)=>s+p[1],0)/pairs.length;
    let num=0,dx=0,dy=0;for(const [x,y] of pairs){num+=(x-mx)*(y-my);dx+=(x-mx)**2;dy+=(y-my)**2;}return dx&&dy?num/Math.sqrt(dx*dy):null;
  }
  function renderCorrelation() {
    const nums=columns.filter(c=>columnTypes[c]==="number");
    if(!nums.length){$("correlationChart").innerHTML="<p>No numeric columns were detected.</p>";return;}
    const z=nums.map(a=>nums.map(b=>a===b?1:pearson(a,b)));
    plot("correlationChart",[{type:"heatmap",x:nums,y:nums,z,colorscale:[[0,"#31688e"],[.5,"#f7f7f7"],[1,"#b2182b"]],zmin:-1,zmax:1,text:z.map(r=>r.map(v=>v==null?"N/A":v.toFixed(2))),texttemplate:"%{text}",hovertemplate:"%{y} × %{x}<br>Correlation: %{z:.3f}<extra></extra>",colorbar:{title:"Correlation"}}],{...chartLayout("Numeric column relationships"),margin:{t:48,r:30,b:100,l:150},xaxis:{side:"bottom",automargin:true},yaxis:{automargin:true,autorange:"reversed"}});
    $("correlationTable").innerHTML=`<thead><tr><th></th>${nums.map(c=>`<th>${escapeHtml(c)}</th>`).join("")}</tr></thead><tbody>${nums.map((a,i)=>`<tr><th>${escapeHtml(a)}</th>${nums.map((b,j)=>`<td class="num">${z[i][j]==null?"—":z[i][j].toFixed(6)}</td>`).join("")}</tr>`).join("")}</tbody>`;
  }
  function showTab(name) {
    document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b.dataset.tab===name));
    document.querySelectorAll(".tab-panel").forEach(p=>p.hidden=p.id!==`panel-${name}`);
    setTimeout(()=>{document.querySelectorAll(`#panel-${name} .chart`).forEach(el=>{if(el.data)Plotly.Plots.resize(el);});},50);
    if(name==="analysis")renderAnalysis(); if(name==="visualizations")renderVisualizations(); if(name==="correlation")renderCorrelation();
  }
  async function downloadWorkbook() {
    if(!window.ExcelJS){download("datalens-report.xlsx",XLSX.write({SheetNames:["Data"],Sheets:{Data:XLSX.utils.json_to_sheet(rows)}},{bookType:"xlsx",type:"array"}),"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");return;}
    const wb=new ExcelJS.Workbook();wb.creator="DataLens";wb.created=new Date();
    const data=wb.addWorksheet("Data");data.addRow(columns);for(const r of rows)data.addRow(columns.map(c=>r[c] instanceof Date?r[c].toISOString():r[c]));
    const q=wb.addWorksheet("Quality Report");q.addRows([["Column","Detected type","Missing values","Blank cells","Unique values"],...quality.byColumn.map(x=>[x.column,x.type,x.missing,x.blank,x.unique])]);
    const o=wb.addWorksheet("Overview");o.addRows([["Metric","Value"],["Rows",rows.length],["Columns",columns.length],["Missing values",quality.missing],["Blank cells",quality.blank],["Duplicate rows",quality.duplicates],["File name",fileMeta.name]]);
    const buf=await wb.xlsx.writeBuffer();download("datalens-report.xlsx",buf,"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
  }
  $("themeToggle").addEventListener("click",()=>{document.body.classList.toggle("dark");$("themeToggle").textContent=document.body.classList.contains("dark")?"☀️":"🌙";if(rows.length){renderCategoryChart();renderTrend();renderVisualizations();renderCorrelation();}});
  $("fileInput").addEventListener("change",e=>{if(e.target.files[0])readFile(e.target.files[0]);e.target.value="";});
  const dz=$("dropZone");["dragenter","dragover"].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.add("drag");}));["dragleave","drop"].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.remove("drag");}));dz.addEventListener("drop",e=>{const f=e.dataTransfer.files[0];if(f)readFile(f);});
  document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>showTab(b.dataset.tab)));
  $("searchInput").addEventListener("input",renderPreview); $("rowLimit").addEventListener("change",renderPreview);
  $("numberSelect").addEventListener("change",renderAnalysis); $("categorySelect").addEventListener("change",renderCategoryChart); $("dateSelect").addEventListener("change",renderTrend); $("trendSelect").addEventListener("change",renderTrend);
  $("xSelect").addEventListener("change",()=>{populateSelectors();renderVisualizations();}); $("ySelect").addEventListener("change",renderVisualizations); $("chartType").addEventListener("change",renderVisualizations);
  $("downloadCsv").addEventListener("click",()=>download("dataset.csv",csvFor(rows,columns),"text/csv;charset=utf-8"));
  $("downloadQuality").addEventListener("click",()=>download("data-quality-report.csv",csvFor(quality.byColumn.map(q=>({Column:q.column,DetectedType:q.type,MissingValues:q.missing,BlankCells:q.blank,UniqueValues:q.unique})),["Column","DetectedType","MissingValues","BlankCells","UniqueValues"]),"text/csv;charset=utf-8"));
  $("downloadExcel").addEventListener("click",downloadWorkbook);
})();
