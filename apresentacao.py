"""Uma interpretação comum para interface, XLSX e PDF; não classifica alunos."""
from collections import Counter


def motivo_humano(motivo):
    regras = [
        ('Curso não localizado na legenda oficial: ', 'O curso {} não está na legenda oficial. O registro foi mantido como NÃO LOCALIZADO para revisão.'),
        ('Conflito de fontes: ', 'As fontes disponíveis atribuem categorias diferentes ao curso {}. O responsável precisa confirmar a categoria.'),
        ('Sigla sem mapa suficiente: ', 'Não há evidência suficiente para classificar o curso {}. Confirme sua categoria.'),
        ('Combinação contradiz mapa no histórico: ', 'A classificação histórica da combinação {} diverge das categorias dos cursos. Confirme o tratamento correto.'),
    ]
    for prefixo, frase in regras:
        if motivo.startswith(prefixo):
            return frase.format(motivo[len(prefixo):].replace('|', ', '))
    if motivo == 'Conjunto de categorias sem validação histórica de múltiplas':
        return 'Esta combinação de categorias não tem tratamento comprovado nas fontes. Não foi escolhida uma categoria automaticamente.'
    if motivo == 'Curso ausente, inválido ou item vazio':
        return 'O campo Curso está vazio ou contém um item incompleto. Confira o documento original.'
    if motivo.startswith('Quantidades diferentes'):
        return 'As listas de cursos, datas, status, unidades e tipos têm tamanhos diferentes. Confira os dados na origem.'
    if motivo.startswith('Identificador repetido'):
        return 'O identificador aparece em mais de uma linha deste período. Todas foram mantidas; confirme se a repetição é esperada.'
    return motivo


def chave(r):
    return (r.get('Página', r.get('pagina', '')), r.get('Tabela', r.get('tabela', '')), r.get('Linha', r.get('linha', '')))


def validar_resultado(resultado):
    registros = resultado['registros']
    competencia = resultado['metadados']['competencia_fatura']
    periodos = {c['Período de coleta'] for c in resultado['conferencia']}
    if any(r['Competência da fatura'] != competencia or r['Período de coleta'] not in periodos for r in registros):
        raise ValueError('Competência ou período dos registros não corresponde ao resumo.')
    for c in resultado['conferencia']:
        rows = [r for r in registros if r['Período de coleta'] == c['Período de coleta']]
        ids = {r['Identificador'] for r in rows if r['Identificador']}
        if (len(rows), len(ids), len(rows)-c['Coletado informado'],len(ids)-c['Coletado informado']) != (c['Linhas extraídas'],c['Identificadores distintos'],c['Diferença de linhas'],c['Diferença de identificadores']):
            raise ValueError('Conferência não corresponde aos registros; exportação interrompida.')
        if any(not isinstance(r['Identificador'], str) for r in rows):
            raise ValueError('Identificadores precisam permanecer como texto.')
    auditoria = resultado.get('classificacao', {}).get('auditoria')
    if auditoria is not None:
        if len(auditoria) != len(registros):
            raise ValueError('Classificação e extração têm quantidades diferentes.')
        if any(a['registro_original'] != r for a,r in zip(auditoria,registros)):
            raise ValueError('Classificação não corresponde ao registro extraído.')


def divergencias(resultado):
    """Uma entrada por registro/local, com todos os motivos; totais em entradas próprias."""
    registros = resultado['registros']
    indices = {chave(r):r for r in registros}
    grupos = {}
    def adicionar(r, motivo, origem, periodo=''):
        k = chave(r)
        if k not in grupos:
            grupos[k] = {'Aluno':r.get('Aluno',''), 'Identificador':r.get('Identificador',''), 'Curso':r.get('Curso',''),
                         'Página':k[0], 'Tabela':k[1], 'Linha':k[2], 'Período de coleta':r.get('Período de coleta',periodo),
                         '_motivos':[], '_origens':[], '_registro':k in indices}
        item = grupos[k]
        if motivo not in item['_motivos']:item['_motivos'].append(motivo)
        if origem not in item['_origens']:item['_origens'].append(origem)
    for alerta in resultado['revisao']:
        r = indices.get(chave(alerta), alerta)
        adicionar(r, alerta['motivo'], 'Leitura', alerta.get('periodo',''))
    for a in resultado.get('classificacao',{}).get('auditoria',[]):
        if a['status_final'] == 'REVISAR':
            for motivo in a['motivos_revisao']:adicionar(a['registro_original'],motivo,'Classificação')
    itens=[]
    for item in grupos.values():
        motivos=item.pop('_motivos'); origens=item.pop('_origens')
        item.update({'Origem':' / '.join(origens), 'Problema encontrado':'Revisar '+ ' e '.join(o.lower() for o in origens),
                     'Motivo compreensível':' '.join(motivo_humano(m) for m in motivos),
                     'Motivo da divergência':'; '.join(motivos),
                     'Localização/origem':', '.join(f'{nome} {item[nome]}' for nome in ('Página','Tabela','Linha') if item[nome] != '')})
        itens.append(item)
    for c in resultado['conferencia']:
        if c['Diferença de linhas'] or c['Diferença de identificadores']:
            texto=f"O relatório informa {c['Coletado informado']} registros; foram extraídas {c['Linhas extraídas']} linhas e {c['Identificadores distintos']} identificadores distintos. Diferença de linhas: {c['Diferença de linhas']:+d}. Confira o resumo e o detalhe do documento; nenhum registro foi criado para fechar o total."
            itens.insert(0,{'Aluno':'','Identificador':'','Curso':'','Página':'','Tabela':'','Linha':'','Período de coleta':c['Período de coleta'],
                            'Origem':'Conferência','Problema encontrado':'Diferença nos totais','Motivo compreensível':texto,
                            'Motivo da divergência':texto,'Localização/origem':'Resumo do período '+c['Período de coleta'],'_registro':False})
    return itens


def resumo_resultado(resultado):
    validar_resultado(resultado)
    itens=divergencias(resultado)
    res=[]
    auditoria=resultado.get('classificacao',{}).get('auditoria',[])
    for c in resultado['conferencia']:
        periodo=c['Período de coleta'];rows=[r for r in resultado['registros'] if r['Período de coleta']==periodo]
        revisados={chave(d) for d in itens if d['_registro'] and d['Período de coleta']==periodo}
        alertas=[d for d in itens if not d['_registro'] and d['Origem']!='Conferência' and d['Período de coleta'] in ('',periodo)]
        classificados=sum(a['status_final']=='CLASSIFICADO' and a['registro_original']['Período de coleta']==periodo for a in auditoria)
        status=('Divergência de quantidade' if c['Diferença de linhas'] or c['Diferença de identificadores'] else
                'Totais conferem; revisão pendente' if revisados or alertas else
                'Totais conferem; classificação não executada' if 'classificacao' not in resultado else 'Totais conferem; sem pendências identificadas')
        res.append({'Competência da fatura':resultado['metadados']['competencia_fatura'],'Período de coleta':periodo,
                    'Início':c['Início'],'Fim':c['Fim'],'Total informado':c['Coletado informado'],'Total encontrado':len(rows),
                    'Diferença':c['Diferença de linhas'],'Identificadores distintos':c['Identificadores distintos'],
                    'Registros conferidos (estrutura)':sum(not r['Revisar'] for r in rows),
                    'Classificados automaticamente':classificados,'Registros para revisão':len(revisados),
                    'Alertas sem registro associado':len(alertas),'Status geral':status})
    return res
