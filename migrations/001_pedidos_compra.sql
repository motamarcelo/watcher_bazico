-- Tabela de pedidos de compra (dados do Bling V3)
CREATE TABLE IF NOT EXISTS public.pedidos_compra (
    id bigint PRIMARY KEY,
    numero varchar(20),
    data_pedido date,
    data_prevista date,
    fornecedor_id bigint,
    fornecedor_nome varchar(255),
    situacao_valor integer,
    valor_total_produtos numeric(15,2),
    valor_total numeric(15,2),
    desconto_valor numeric(15,2),
    ordem_compra varchar(50),
    observacoes text,
    observacoes_internas text,
    data_etl timestamp DEFAULT now()
);

-- Itens do pedido de compra
CREATE TABLE IF NOT EXISTS public.pedidos_compra_itens (
    id serial PRIMARY KEY,
    pedido_compra_id bigint NOT NULL REFERENCES public.pedidos_compra(id) ON DELETE CASCADE,
    produto_id bigint,
    produto_codigo varchar(100),
    produto_nome varchar(255),
    descricao text,
    codigo_fornecedor varchar(100),
    unidade varchar(10),
    quantidade numeric(10,3),
    valor_unitario numeric(15,2),
    aliquota_ipi numeric(5,2),
    data_etl timestamp DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pedidos_compra_data ON public.pedidos_compra(data_pedido);
CREATE INDEX IF NOT EXISTS idx_pedidos_compra_fornecedor ON public.pedidos_compra(fornecedor_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_compra_itens_pedido ON public.pedidos_compra_itens(pedido_compra_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_compra_itens_produto ON public.pedidos_compra_itens(produto_id);
