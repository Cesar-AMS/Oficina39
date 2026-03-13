# Operação Diária + Backup/Restore

## Rotina diária recomendada
- Conferir ordens em `Consultar OS`.
- Garantir profissional preenchido nas ordens em andamento.
- Finalizar ordens concluídas no dia.
- Validar relatórios de produção e operacional.

## Backup manual (API)
### Verificar status
- `GET /api/config/backup/status`

### Executar backup imediato
- `POST /api/config/backup/executar`

## Validação de backup
- Confirmar retorno com nome de arquivo e tamanho (`tamanho_bytes` > 0).
- Confirmar arquivo na pasta de backups do projeto.

## Restore (procedimento seguro)
1. Parar a aplicação.
2. Fazer cópia de segurança do `database.db` atual.
3. Substituir `database.db` pelo backup validado.
4. Subir a aplicação.
5. Executar checklist mínimo:
   - `GET /api/ordens/`
   - `GET /api/config/contador`
   - abrir página inicial e `Consultar OS`.

## Comando de smoke test
- `python -m unittest tests/test_smoke_api.py`
