'use strict';
const $=id=>document.getElementById(id);
const numero=n=>new Intl.NumberFormat('pt-BR').format(n);
let arquivo=null,token=null,ocupado=false,dragDepth=0;
function estado(value){document.body.dataset.state=value;}
function inicioDaTela(){window.scrollTo({top:0,behavior:'instant'});}
function etapa(n){[1,2,3,4].forEach(i=>{const el=$(`step${i}`);el.classList.toggle('active',i===n);el.classList.toggle('done',i<n);if(i===n)el.setAttribute('aria-current','step');else el.removeAttribute('aria-current');});}
function mensagemErro(raw){
 const text=String(raw||'');
 if(/senha|password|encrypt|protegido/i.test(text))return ['Este PDF está protegido.','Use uma cópia sem senha, exportada pelo Perseus, e tente novamente.'];
 if(/80|grande|tamanho|limite/i.test(text))return ['Este arquivo ultrapassa o limite.','Selecione um PDF de até 80 MB.'];
 if(/cabeçalho|estrutura|incompatível|período.*encontr|reconhecid|nenhuma tabela|metadados contraditórios/i.test(text))return ['Não reconhecemos este relatório.','Use o PDF “Alunos Coletados para Fatura”, exportado pelo Perseus, com texto selecionável.'];
 if(/%PDF|não.*PDF|arquivo.*PDF|vazio/i.test(text))return ['Precisamos de um PDF válido.','Selecione o relatório original do Perseus. Renomear outro arquivo para .pdf não o transforma em PDF.'];
 if(/salvar|espaço|permission|permissionerror|export|gerar/i.test(text))return ['Não foi possível preparar os arquivos.','Confira o espaço disponível e a permissão de gravação na pasta de resultados. Depois, processe o relatório novamente.'];
 if(/conexão|fetch|network|sessão|encontrado nesta/i.test(text))return ['A conexão com o programa local foi interrompida.','Abra o Perseus pelo iniciador local e recarregue esta página. Se a sessão terminou, selecione o PDF novamente.'];
 return ['Não foi possível concluir a leitura.','Confira se o PDF original abre normalmente e tente novamente. Se persistir, use os detalhes abaixo para solicitar ajuda.'];
}
function erro(raw,custom){const [title,message]=custom||mensagemErro(raw);$('error-title').textContent=title;$('error-message').textContent=message;$('error-technical').textContent=raw||'';$('error-details').hidden=!raw;$('error-details').open=false;$('error').hidden=false;estado('error');$('error-title').focus();}
function limparArquivo(){arquivo=null;$('pdf').value='';$('filename').textContent='Seu relatório começa aqui.';$('filehint').textContent='Arraste o PDF ou escolha um arquivo no seu computador.';$('processar').disabled=true;}
function escolher(file){
 if(ocupado||!file)return;
 $('error').hidden=true;
 if(!file.name.toLowerCase().endsWith('.pdf')||file.size===0||file.size>80*1024*1024){limparArquivo();erro('',file.size>80*1024*1024?['Este arquivo ultrapassa o limite.','Selecione um PDF de até 80 MB.']:['Precisamos de um PDF válido.','Escolha um arquivo PDF do Perseus que não esteja vazio.']);return;}
 arquivo=file;$('filename').textContent=file.name;$('filehint').textContent=`${new Intl.NumberFormat('pt-BR',{maximumFractionDigits:1}).format(file.size/1024/1024)} MB · Documento selecionado. Podemos começar.`;$('processar').disabled=false;estado('selected');
}
$('pdf').addEventListener('change',e=>escolher(e.target.files[0]));
$('drop').addEventListener('dragenter',e=>{e.preventDefault();if(ocupado)return;dragDepth++;$('drop').classList.add('drag');estado('dragging');});
$('drop').addEventListener('dragover',e=>{e.preventDefault();if(e.dataTransfer)e.dataTransfer.dropEffect='copy';});
$('drop').addEventListener('dragleave',e=>{e.preventDefault();dragDepth=Math.max(0,dragDepth-1);if(!dragDepth){$('drop').classList.remove('drag');estado(arquivo?'selected':'idle');}});
$('drop').addEventListener('drop',e=>{e.preventDefault();dragDepth=0;$('drop').classList.remove('drag');estado(arquivo?'selected':'idle');escolher(e.dataTransfer.files[0]);});
window.addEventListener('dragover',e=>e.preventDefault());window.addEventListener('drop',e=>e.preventDefault());
async function json(url,opts){let response;try{response=await fetch(url,opts);}catch{throw new Error('Conexão local interrompida.');}let data;try{data=await response.json();}catch{throw new Error('Resposta inválida do programa local.');}if(!response.ok)throw new Error(data.erro||'Não foi possível completar a operação.');return data;}
function texto(tag,value,className){const el=document.createElement(tag);el.textContent=value??'—';if(className)el.className=className;return el;}
function renderizarReferencia(job){
 const referencia=job.referencia||{},itens=job.consolidacao||[];
 const total=itens.reduce((s,item)=>s+Number(item.quantidade||0),0);
 const cor=/^[0-9A-F]{6}$/i.test(referencia.cor||'')?`#${referencia.cor}`:'#E7EFEA';
 const box=$('reference-summary');box.style.setProperty('--reference-color',cor);
 $('reference-title').textContent=referencia.titulo||'Referência';
 $('reference-competence').textContent=job.competencia_operacional?`COMPETENCIA: ${job.competencia_operacional}`:'';
 $('reference-total').textContent=numero(total);
 const cards=$('reference-cards');cards.replaceChildren();
 for(const item of itens){
   const quantidade=Number(item.quantidade||0),pct=total?quantidade/total*100:0;
   const card=document.createElement('article');card.className='reference-card';
   if(item.categoria==='NÃO LOCALIZADO'&&quantidade)card.classList.add('is-review');
   const topo=document.createElement('div');topo.className='reference-card-top';
   topo.append(texto('span',item.categoria,'reference-category'),texto('i','', 'reference-dot'));
   const valor=texto('strong',numero(quantidade));
   const proporcao=texto('small',`${new Intl.NumberFormat('pt-BR',{maximumFractionDigits:1}).format(pct)}% da referência`);
   card.append(topo,valor,proporcao);cards.appendChild(card);
 }
}
function concluir(job){
 const c=job.conferencia[0],m=job.metadados,r=job.resumo[0],diff=r['Diferença'],revisoes=r['Registros para revisão'];
 ocupado=false;$('loading').hidden=true;$('setup').hidden=true;$('result').hidden=false;$('error').hidden=true;etapa(3);$('result-title').focus();inicioDaTela();
 const pendencias=job.divergencias||[],temRevisao=revisoes>0||r['Alertas sem registro associado']>0;
 estado(diff!==0||temRevisao?'review':'success');
 $('result-file').textContent=job.arquivo;
 $('invoice').textContent=r['Competência da fatura'];$('collection').textContent=r['Período de coleta'];$('interval').textContent=`${c.Início} a ${c.Fim}`;
 $('informado').textContent=numero(c['Coletado informado']);$('extraido').textContent=numero(c['Linhas extraídas']);$('diferenca').textContent=(diff>0?'+':'')+numero(diff);$('revisoes').textContent=numero(revisoes);
 $('diferenca').className=diff!==0?'attention-text':'';$('revisoes').className=revisoes?'attention-text':'';
 $('outcome').textContent=diff!==0?'≠ Diferença de quantidade encontrada':temRevisao?'! Totais conferem. Há revisões pendentes.':'✓ Conferência sem diferença';
 $('outcome-description').textContent=diff!==0?`O relatório informa ${numero(c['Coletado informado'])} registros e encontramos ${numero(c['Linhas extraídas'])}. Confira a diferença e as pendências abaixo.`:temRevisao?`As quantidades coincidem. ${numero(revisoes)} registros precisam de revisão humana${r['Alertas sem registro associado']?' e há alertas de leitura adicionais':''}.`:'As quantidades coincidem e não foram identificadas pendências de leitura ou classificação.';
 renderizarReferencia(job);
 for(const [id,name] of [['download',job.excel],['download-pdf',job.pdf],['download-alunos-pdf',job.pdf_alunos],['download-json','resultado.json'],['download-csv','alunos.csv'],['download-all','resultado.zip']]){const link=$(id);link.href=`/download/${encodeURIComponent(job.id)}/${encodeURIComponent(name)}`;link.download=name;}
 $('review-count').textContent=`${numero(job.total_pendencias)} ${job.total_pendencias===1?'pendência':'pendências'}`;
 $('review-caption').textContent=job.total_pendencias?`${numero(revisoes)} registros para revisão${diff!==0?' e uma pendência de quantidade':''}. Abra cada item para conferir a explicação e a origem. O STATUS_CURSO não localizado permanece visível também no Excel e nos PDFs.`:'Nenhuma pendência de quantidade, leitura ou classificação identificada.';
 $('review-rows').replaceChildren();
 for(const row of pendencias){const item=document.createElement('details');item.className='review-item';const summary=document.createElement('summary');const name=texto('span',row.Aluno||'Conferência do relatório','review-name');name.appendChild(texto('small',row.Identificador?`Identificador: ${row.Identificador}`:'Relatório'));summary.append(name,texto('span',row.Curso||'—'),texto('span',row['Problema encontrado']||row['Motivo compreensível'],'review-reason'));item.appendChild(summary);const detail=document.createElement('div');detail.className='review-detail';detail.append(texto('p',row['Motivo compreensível']),texto('p',`Origem: ${row['Localização/origem']||'Resumo do relatório'}`));const technical=Object.entries(row).filter(([key,value])=>value&&!['Aluno','Identificador','Curso','Problema encontrado','Motivo compreensível','Localização/origem'].includes(key));if(technical.length){const more=document.createElement('details');more.appendChild(texto('summary','Ver detalhes técnicos'));for(const [key,value]of technical)more.appendChild(texto('p',`${key}: ${value}`));detail.appendChild(more);}item.appendChild(detail);$('review-rows').appendChild(item);}
 $('detail').textContent=`${numero(c['Identificadores distintos'])} identificadores distintos · ${numero(job.alertas)} alertas de leitura · ${numero(job.revisoes_classificacao)} classificações para revisão. Quantidade faturada transcrita do documento: ${numero(m.quantidade_faturada)}.`;
 $('execution').textContent=`Execução: ${m.execucao} · Processado em: ${m.processado_em}`;
}
async function acompanhar(id){
 while(true){const job=await json(`/api/trabalho/${encodeURIComponent(id)}`);if(job.estado==='concluido'){sessionStorage.removeItem('perseus-job');concluir(job);return;}if(job.estado==='erro'){sessionStorage.removeItem('perseus-job');throw new Error(job.detalhe||job.erro);}
 $('progress-title').textContent=job.etapa?.includes('Preparando')?'Preparando Excel, referência e PDFs':job.pagina?'Lendo e conferindo o relatório':'Recebendo seu documento';
 $('progress-text').textContent=job.pagina?`Página ${numero(job.pagina)} de ${numero(job.paginas_pdf)} do documento · ${numero(job.registros)} registros encontrados`:'O processamento começará assim que o PDF for recebido.';
 await new Promise(resolve=>setTimeout(resolve,900));}
}
function falhou(e){ocupado=false;$('loading').hidden=true;$('setup').hidden=false;$('result').hidden=true;$('processar').disabled=!arquivo;etapa(1);erro(e.message);}
function iniciarLeitura(){ocupado=true;$('error').hidden=true;$('setup').hidden=true;$('result').hidden=true;$('loading').hidden=false;$('processar').disabled=true;$('progress-title').textContent='Recebendo seu documento';$('progress-text').textContent='Preparando a leitura do PDF.';estado('processing');etapa(2);$('progress-title').focus();inicioDaTela();}
$('processar').addEventListener('click',async()=>{if(!arquivo||ocupado)return;iniciarLeitura();try{if(!token)token=(await json('/api/sessao')).token;const job=await json('/api/processar',{method:'POST',headers:{'Content-Type':'application/pdf','X-Local-Token':token,'X-Filename':encodeURIComponent(arquivo.name)},body:arquivo});sessionStorage.setItem('perseus-job',job.id);await acompanhar(job.id);}catch(e){falhou(e);}});
$('novo').addEventListener('click',()=>{limparArquivo();$('result').hidden=true;$('setup').hidden=false;$('error').hidden=true;estado('idle');etapa(1);$('pdf').focus();});
for(const id of ['download','download-pdf','download-alunos-pdf'])$(id).addEventListener('click',()=>etapa(4));
async function iniciar(){try{token=(await json('/api/sessao')).token;const id=sessionStorage.getItem('perseus-job');if(id){iniciarLeitura();await acompanhar(id);}}catch(e){sessionStorage.removeItem('perseus-job');falhou(e);}}
iniciar();
