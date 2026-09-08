# Biblioteca de divergências

Esta pasta separa as **exceções operacionais** da legenda oficial de cursos.

- `mapeamentos_operacionais.json`: regras confirmadas pelos quadros de Referência de agosto e setembro de 2026. É versionado e auditável.
- `nao_localizados.json`: criado automaticamente no computador durante o uso. Guarda apenas **siglas e contagens**, sem nomes de alunos, e não é enviado ao GitHub.

A ordem de decisão é:

1. combinação exata da biblioteca, quando existir;
2. mapeamento de sigla da biblioteca, quando existir;
3. legenda oficial `regras_status_curso.json`;
4. sigla ausente: registrar na biblioteca de não localizados para revisão.

A biblioteca não cria nem remove alunos e não altera o motor de extração do PDF.
