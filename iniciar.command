#!/bin/zsh
cd "${0:A:h}" || exit 1
perseus_python="/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ ! -x "$perseus_python" ]]; then
  perseus_python="${0:A:h}/.venv/bin/python"
fi
if [[ ! -x "$perseus_python" ]]; then
  echo "Python não encontrado. Siga a instalação indicada no README.md."
  read "?Pressione Enter para fechar."
  exit 1
fi
exec "$perseus_python" app.py "$@"
