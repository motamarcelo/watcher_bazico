CREATE OR REPLACE VIEW public.vw_compras_vendas_mensal AS
WITH compras_mensal AS (
    SELECT
        i.produto_codigo AS sku,
        date_trunc('month', pc.data_pedido)::date AS mes,
        SUM(i.quantidade) AS qtd_comprada,
        SUM(i.quantidade * i.valor_unitario) AS valor_compras
    FROM pedidos_compra_itens i
    JOIN pedidos_compra pc ON pc.id = i.pedido_compra_id
    WHERE pc.data_pedido IS NOT NULL
    GROUP BY i.produto_codigo, date_trunc('month', pc.data_pedido)
),
vendas_mensal AS (
    SELECT
        sku,
        date_trunc('month', data_venda::date)::date AS mes,
        SUM(qtd_vendida) AS qtd_vendida,
        SUM(valor_total_vendas) AS valor_vendas
    FROM vw_vendas_sku_diarias
    GROUP BY sku, date_trunc('month', data_venda::date)
)
SELECT
    COALESCE(c.sku, v.sku) AS sku,
    COALESCE(c.mes, v.mes) AS mes,
    COALESCE(v.qtd_vendida, 0) AS qtd_vendida,
    COALESCE(v.valor_vendas, 0) AS valor_vendas,
    COALESCE(c.qtd_comprada, 0) AS qtd_comprada,
    COALESCE(c.valor_compras, 0) AS valor_compras,
    COALESCE(c.qtd_comprada, 0) - COALESCE(v.qtd_vendida, 0) AS saldo_mensal
FROM compras_mensal c
FULL OUTER JOIN vendas_mensal v ON c.sku = v.sku AND c.mes = v.mes
ORDER BY COALESCE(c.sku, v.sku), COALESCE(c.mes, v.mes);
