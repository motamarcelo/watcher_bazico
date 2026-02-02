from datetime import datetime

from db import get_connection


def _parse_date(value):
    """Converte data do Bling, tratando '0000-00-00' e vazios como None."""
    if not value or value == "0000-00-00":
        return None
    return value


def upsert_pedidos_compra(pedidos: list[dict]) -> dict:
    """Faz upsert dos pedidos de compra e seus itens no Supabase."""
    conn = get_connection()
    cur = conn.cursor()
    agora = datetime.now()

    inseridos = 0
    atualizados = 0
    erros = []

    for pedido in pedidos:
        try:
            pedido_id = pedido.get("id")
            fornecedor = pedido.get("fornecedor") or {}
            situacao = pedido.get("situacao") or {}

            cur.execute(
                """
                INSERT INTO pedidos_compra
                    (id, numero, data_pedido, data_prevista, fornecedor_id,
                     situacao_valor, valor_total_produtos, valor_total,
                     desconto_valor, ordem_compra, observacoes, observacoes_internas, data_etl)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    numero = EXCLUDED.numero,
                    data_pedido = EXCLUDED.data_pedido,
                    data_prevista = EXCLUDED.data_prevista,
                    fornecedor_id = EXCLUDED.fornecedor_id,
                    situacao_valor = EXCLUDED.situacao_valor,
                    valor_total_produtos = EXCLUDED.valor_total_produtos,
                    valor_total = EXCLUDED.valor_total,
                    desconto_valor = EXCLUDED.desconto_valor,
                    ordem_compra = EXCLUDED.ordem_compra,
                    observacoes = EXCLUDED.observacoes,
                    observacoes_internas = EXCLUDED.observacoes_internas,
                    data_etl = EXCLUDED.data_etl
                """,
                (
                    pedido_id,
                    pedido.get("numero"),
                    _parse_date(pedido.get("data")),
                    _parse_date(pedido.get("dataPrevista")),
                    fornecedor.get("id"),
                    situacao.get("valor"),
                    pedido.get("totalProdutos"),
                    pedido.get("total"),
                    (pedido.get("desconto") or {}).get("valor"),
                    pedido.get("ordemCompra"),
                    pedido.get("observacoes"),
                    pedido.get("observacoesInternas"),
                    agora,
                ),
            )

            # Deleta itens antigos e insere os novos
            cur.execute(
                "DELETE FROM pedidos_compra_itens WHERE pedido_compra_id = %s",
                (pedido_id,),
            )

            for item in pedido.get("itens") or []:
                produto = item.get("produto") or {}
                cur.execute(
                    """
                    INSERT INTO pedidos_compra_itens
                        (pedido_compra_id, produto_id, produto_codigo, produto_nome,
                         descricao, codigo_fornecedor, unidade, quantidade,
                         valor_unitario, aliquota_ipi, data_etl)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        pedido_id,
                        produto.get("id"),
                        produto.get("codigo"),
                        produto.get("nome"),
                        item.get("descricao"),
                        item.get("codigoFornecedor"),
                        item.get("unidade"),
                        item.get("quantidade"),
                        item.get("valor"),
                        item.get("aliquotaIPI"),
                        agora,
                    ),
                )

            conn.commit()
            if cur.rowcount > 0:
                inseridos += 1
            else:
                atualizados += 1

        except Exception as e:
            conn.rollback()
            erros.append({"pedido_id": pedido.get("id"), "erro": str(e)})

    cur.close()
    conn.close()

    return {
        "total": len(pedidos),
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }
