const $=id=>document.getElementById(id);
let arquivo=null,token=null,ocupado=false;
const numero=n=>new Intl.NumberFormat('pt-BR').format(n);
const erro=msg=>{$('error').textContent=msg;$('error').hidden=false;};
function escolher(file){
 if(ocupado)return;
 $('error').hidden=true;
 if(!file)return;
 if(!file.name.toLowerCase().endsWith('.pdf')||file.size===0||file.size>80*1024*1024){arquivo=null;$('processar').disabled=true;erro('Escolha um PDF com até 80 MB.');return;}
 arquivo=file;$('filename').textContent=file.name;$('filehint').textContent=`${(file.size/1024/1024).toFixed(1)} MB · pronto para processar`;$('processar').disabled=false;
}
$('pdf').addEventListener('change',e=>escolher(e.target.files[0]));
for(const event of ['dragenter','dragover'])$('drop').addEventListener(event,e=>{e.preventDefault();$('drop').classList.add('drag');});
for(const event of ['dragleave','drop'])$('drop').addEventListener(event,e=>{e.preventDefault();$('drop').classList.remove('drag');});
$('drop').addEventListener('drop',e=>escolher(e.dataTransfer.files[0]));
function etapa(n){[1,2,3,4].forEach(i=>{const el=$(`step${i}`);el.classList.toggle('active',i===n);el.classList.toggle('done',i<n);if(i===n)el.setAttribute('aria-current','step');else el.removeAttribute('aria-current');});}
async function json(url,opts){let r;try{r=await fetch(url,opts);}catch{throw new Error('A conexão com o programa local foi interrompida. Confira se a janela do Python continua aberta e recarregue esta página para retomar o acompanhamento.');}const data=await r.json();if(!r.ok)throw new Error(data.erro||'Não foi possível completar a operação.');return data;}
function concluir(job){
 job.excel=job.excel||"alunos.xlsx";job.casos_revisao=job.casos_revisao??((job.alertas||0)+(job.revisoes_classificacao||0));job.divergencias=job.divergencias||[];
 ocupado=false;$('loading').hidden=true;$('result').hidden=false;etapa(3);
 const c=job.conferencia[0],m=job.metadados,r=job.resumo[0],diff=r['Diferença'];
 $('result-title').textContent=`Fatura ${r['Competência da fatura']} · Coleta ${r['Período de coleta']}`;
 $('result-file').textContent=`${job.arquivo} · Execução ${m.execucao} · ${m.processado_em}`;
 $('informado').textContent=numero(c['Coletado informado']);$('extraido').textContent=numero(c['Linhas extraídas']);$('diferenca').textContent=(diff>0?'+':'')+numero(diff);
 const revisoes=job.revisoes_classificacao||0;
 const ok=diff===0&&r['Registros para revisão']===0&&r['Alertas sem registro associado']===0;
 $('outcome').className=ok?'ok':'warn';
 $('outcome').textContent=r['Status geral'];
 $('detail').textContent=`${numero(c['Identificadores distintos'])} identificadores distintos · ${numero(job.alertas)} alertas de leitura · ${numero(revisoes)} classificações para revisão · Intervalo ${c.Início} a ${c.Fim}. Quantidade faturada informada: ${numero(m.quantidade_faturada)}; esse valor é apenas transcrito do PDF e não é calculado por este MVP.`;
 $('download').href=`/download/${job.id}/${job.excel}`;$('download').download=job.excel;$('excel-name').textContent=job.excel;$('download-json').href=`/download/${job.id}/resultado.json`;$('download-csv').href=`/download/${job.id}/alunos.csv`;$('download-all').href=`/download/${job.id}/resultado.zip`;
 $('download-pdf').href=`/download/${job.id}/${job.pdf}`;$('download-pdf').download=job.pdf;
 $('revisoes').textContent=numero(job.casos_revisao);
 $('diferenca').className=diff===0?'success-text':'danger-text';
 $('revisoes').className=job.casos_revisao?'attention-text':'success-text';
 $('review-caption').textContent=job.total_pendencias?(job.divergencias.length?`Mostrando ${job.divergencias.length} de ${numero(job.total_pendencias)} pendências. Consulte todas na aba Divergências do Excel.`:"Reinicie o Perseus e processe o PDF novamente para exibir a prévia e gerar o novo Excel."):'Nenhuma divergência de quantidade, leitura ou classificação identificada.';
 $('review-rows').replaceChildren();for(const r of job.divergencias){const tr=document.createElement('tr');for(const campo of ['Aluno','Curso','Motivo compreensível','Localização/origem']){const td=document.createElement('td');td.textContent=r[campo]||'—';tr.appendChild(td);}$('review-rows').appendChild(tr);}
 $('rows').replaceChildren();for(const r of job.amostra){const tr=document.createElement('tr');for(const campo of ['Aluno','Curso','Data da Coleta','Página']){const td=document.createElement('td');td.textContent=r[campo];tr.appendChild(td);}$('rows').appendChild(tr);}
}
async function acompanhar(id){
 const job=await json(`/api/trabalho/${id}`);
 if(job.estado==='concluido'){sessionStorage.removeItem('perseus-job');concluir(job);return;}
 if(job.estado==='erro'){sessionStorage.removeItem('perseus-job');throw new Error(job.erro);}
 $('progress-text').textContent=job.pagina?`${job.etapa || "Lendo tabelas"} · página ${job.pagina} de ${job.paginas_pdf} do documento · ${numero(job.registros)} registros encontrados. A leitura considera o primeiro bloco, não necessariamente todas as páginas.`:'Recebendo o PDF.';
 await new Promise(resolve=>setTimeout(resolve,900));return acompanhar(id);
}
function falhou(e){ocupado=false;$('loading').hidden=true;$('setup').hidden=false;$('processar').disabled=!arquivo;etapa(1);erro(e.message||'O sistema local não respondeu. Verifique se o Python continua aberto.');}
$('processar').addEventListener('click',async()=>{
 if(!arquivo||ocupado)return;
 ocupado=true;$('error').hidden=true;$('setup').hidden=true;$('loading').hidden=false;$('result').hidden=true;$('processar').disabled=true;etapa(2);
 try{if(!token)token=(await json('/api/sessao')).token;const job=await json('/api/processar',{method:'POST',headers:{'Content-Type':'application/pdf','X-Local-Token':token,'X-Filename':encodeURIComponent(arquivo.name)},body:arquivo});sessionStorage.setItem('perseus-job',job.id);await acompanhar(job.id);}catch(e){falhou(e);}
});
$('novo').addEventListener('click',()=>{arquivo=null;$('pdf').value='';$('filename').textContent='Escolha ou arraste seu PDF';$('filehint').textContent='PDF de até 80 MB';$('processar').disabled=true;$('result').hidden=true;$('setup').hidden=false;etapa(1);});
async function iniciar(){try{token=(await json('/api/sessao')).token;const id=sessionStorage.getItem('perseus-job');if(id){ocupado=true;$('setup').hidden=true;$('loading').hidden=false;etapa(2);await acompanhar(id);}}catch(e){sessionStorage.removeItem('perseus-job');falhou(e);}}iniciar();

$('download').addEventListener('click',()=>etapa(4));

$('download-pdf').addEventListener('click',()=>etapa(4));
