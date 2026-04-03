from models import OrdemStatusLog, StatusLog


class StatusLogRepository:
    def criar(self, log):
        from extensions import db

        db.session.add(log)
        return log

    def listar_por_entidade(self, entidade_tipo, entidade_id, incluir_legado=True):
        logs = (
            StatusLog.query
            .filter_by(entidade_tipo=(entidade_tipo or '').strip().lower(), entidade_id=entidade_id)
            .order_by(StatusLog.created_at.desc())
            .all()
        )
        if not incluir_legado or (entidade_tipo or '').strip().lower() != 'ordem':
            return logs

        legados = (
            OrdemStatusLog.query
            .filter_by(ordem_id=entidade_id)
            .order_by(OrdemStatusLog.data_evento.desc())
            .all()
        )
        return self._mesclar_logs(logs, legados)

    def _mesclar_logs(self, logs_novos, logs_legados):
        chave_vista = set()
        combinados = []

        for log in logs_novos:
            chave = self._chave_unica(
                status_anterior=log.status_anterior,
                status_novo=log.status_novo,
                data_ref=log.created_at,
                observacao=(log.motivo or (log.metadata_json or {}).get('observacao')),
            )
            chave_vista.add(chave)
            combinados.append(log)

        for log in logs_legados:
            chave = self._chave_unica(
                status_anterior=log.status_anterior,
                status_novo=log.status_novo,
                data_ref=log.data_evento,
                observacao=log.observacao,
            )
            if chave not in chave_vista:
                combinados.append(log)

        combinados.sort(
            key=lambda item: getattr(item, 'created_at', None) or getattr(item, 'data_evento', None),
            reverse=True,
        )
        return combinados

    @staticmethod
    def _chave_unica(status_anterior, status_novo, data_ref, observacao):
        minuto = data_ref.strftime('%Y%m%d%H%M') if data_ref else 'sem_data'
        return (
            (status_anterior or '').strip(),
            (status_novo or '').strip(),
            minuto,
            (observacao or '').strip(),
        )


status_log_repository = StatusLogRepository()
