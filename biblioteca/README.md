# Biblioteca de divergências

Esta pasta separa três tipos de conhecimento que antes estavam misturados:

1. **regra de negócio confirmada**;
2. **compatibilidade histórica** usada para explicar/reproduzir referências antigas;
3. **pendências reais** ainda sem resposta.

`mapeamentos_operacionais.json` é versionado e auditável. Dentro dele:

- `confirmados_negocio`: fatos confirmados pela área, atualmente `LPI → GRADUAÇÃO`, `TEOC → GRADUAÇÃO`, `EFB → GRADUAÇÃO` e `PCG → POS`;
- `significados_confirmados`: contexto empresarial, incluindo que `DI` representa compra de disciplina isolada;
- `mapeamentos_historicos_compatibilidade`: classificações observadas nos quadros antigos, mas ainda não promovidas a regra empresarial;
- `combinacoes_historicas_compatibilidade`: combinações específicas usadas historicamente;
- `pendencias_conhecidas`: itens ainda sem solução, atualmente `SETRA` e o valor `15` encontrado no campo Curso.

`nao_localizados.json` é criado automaticamente no computador durante o uso. Guarda apenas **siglas e contagens**, sem nomes de alunos, e não é enviado ao GitHub.

A ordem conceitual é:

1. regra de negócio confirmada;
2. legenda oficial `regras_status_curso.json`;
3. compatibilidade histórica, quando necessária para reproduzir uma referência antiga;
4. sem base segura → registrar como pendência para revisão.

A biblioteca não cria nem remove alunos e não altera o motor de extração do PDF.
