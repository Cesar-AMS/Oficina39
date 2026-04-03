from models import Anexo, OrdemAnexo


class AnexoRepository:
    def criar(self, anexo):
        from extensions import db

        db.session.add(anexo)
        return anexo

    def listar_por_entidade(self, entidade_tipo, entidade_id, incluir_legado=True):
        entidade = (entidade_tipo or '').strip().lower()
        anexos = (
            Anexo.query
            .filter_by(entidade_tipo=entidade, entidade_id=entidade_id)
            .order_by(Anexo.created_at.desc())
            .all()
        )
        if not incluir_legado or entidade != 'ordem':
            return anexos

        legados = (
            OrdemAnexo.query
            .filter_by(ordem_id=entidade_id)
            .order_by(OrdemAnexo.created_at.desc())
            .all()
        )
        return self._mesclar_anexos(anexos, legados)

    def obter_por_id(self, anexo_id):
        from extensions import db

        return db.session.get(Anexo, anexo_id)

    def obter_por_entidade(self, entidade_tipo, entidade_id, anexo_id, incluir_legado=True):
        entidade = (entidade_tipo or '').strip().lower()
        anexo = (
            Anexo.query
            .filter_by(id=anexo_id, entidade_tipo=entidade, entidade_id=entidade_id)
            .first()
        )
        if anexo or not incluir_legado or entidade != 'ordem':
            return anexo
        return OrdemAnexo.query.filter_by(id=anexo_id, ordem_id=entidade_id).first()

    def excluir(self, anexo):
        from extensions import db

        db.session.delete(anexo)

    def _mesclar_anexos(self, anexos_novos, anexos_legados):
        caminhos_vistos = {getattr(item, 'caminho_arquivo', None) for item in anexos_novos}
        combinados = list(anexos_novos)
        for anexo in anexos_legados:
            if anexo.caminho_relativo not in caminhos_vistos:
                combinados.append(anexo)
        combinados.sort(
            key=lambda item: getattr(item, 'created_at', None) or getattr(item, 'data_evento', None),
            reverse=True,
        )
        return combinados


anexo_repository = AnexoRepository()
