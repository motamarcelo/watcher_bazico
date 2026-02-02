CREATE OR REPLACE VIEW public.vw_estoque_vendas_mensal AS
WITH compras_mensal AS (
    SELECT
        i.produto_codigo AS sku,
        date_trunc('month', pc.data_pedido)::date AS mes,
        SUM(i.quantidade) AS qtd_comprada
    FROM pedidos_compra_itens i
    JOIN pedidos_compra pc ON pc.id = i.pedido_compra_id
    WHERE pc.data_pedido IS NOT NULL
    GROUP BY i.produto_codigo, date_trunc('month', pc.data_pedido)
),
vendas_mensal AS (
    SELECT
        sku,
        date_trunc('month', data_venda::date)::date AS mes,
        SUM(qtd_vendida) AS qtd_vendida
    FROM vw_vendas_sku_diarias
    GROUP BY sku, date_trunc('month', data_venda::date)
),
combinado AS (
    SELECT
        COALESCE(c.sku, v.sku) AS sku,
        COALESCE(c.mes, v.mes) AS mes,
        COALESCE(c.qtd_comprada, 0) AS qtd_comprada,
        COALESCE(v.qtd_vendida, 0) AS qtd_vendida
    FROM compras_mensal c
    FULL OUTER JOIN vendas_mensal v ON c.sku = v.sku AND c.mes = v.mes
)
SELECT
    sku,
    mes,
    qtd_comprada,
    qtd_vendida,
    SUM(qtd_comprada - qtd_vendida) OVER (
        PARTITION BY sku ORDER BY mes
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS estoque_acumulado
FROM combinado
ORDER BY sku, mes;
