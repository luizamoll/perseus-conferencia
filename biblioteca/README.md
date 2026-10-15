# Biblioteca de divergências

Esta pasta separa três tipos de conhecimento:

1. **regra de negócio confirmada**;
2. **compatibilidade histórica** usada para explicar/reproduzir referências antigas;
3. **pendências reais** ainda sem resposta.

`mapeamentos_operacionais.json` é versionado e auditável. Dentro dele:

- `confirmados_negocio`: `LPI → GRADUAÇÃO`, `TEOC → GRADUAÇÃO`, `EFB → GRADUAÇÃO`, `PCG → POS` e `SETRA → GRADUAÇÃO`;
- `significados_confirmados`: contexto empresarial, incluindo que `SETRA` é Graduação em Segurança do Trabalho e que `DI` representa compra de disciplina isolada;
- `mapeamentos_historicos_compatibilidade`: classificações observadas nos quadros antigos, mas não promovidas automaticamente a regra futura;
- `combinacoes_historicas_compatibilidade`: combinações específicas usadas historicamente;
- `pendencias_conhecidas`: atualmente o valor `15` encontrado no campo Curso.

Sobre `15`: existe confirmação de que o aluno do registro cursa MBA Gestão de trans, mas isso **não confirma que o código 15 signifique MBA**. Por isso ele continua pendente. Como aparece junto de `CEXT`, `CSAP` e `GN`, o registro permanece classificado como DI com revisão; a referência original de setembro também o classificou como DI.

`nao_localizados.json` é criado automaticamente no computador durante o uso. Guarda apenas **siglas e contagens**, sem nomes ou identificadores de alunos, e não é enviado ao GitHub.

A ordem conceitual é:

1. regra de negócio confirmada;
2. legenda oficial `regras_status_curso.json`;
3. compatibilidade histórica, somente quando a competência estiver explicitamente autorizada;
4. sem base segura → registrar como pendência.

A biblioteca não cria nem remove alunos e não altera o motor de extração do PDF.
