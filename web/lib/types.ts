export type Resumo = {
  total_pedidos: number;
  valor_total: number;
  ticket_medio: number;
  atrasados: number;
  prazo_medio_entrega_dias: number | null;
  por_status: Record<string, number>;
};
export type Categoria = { categoria: string; pedidos: number; valor_total: number };
export type Fornecedor = { fornecedor: string; pedidos: number; valor_total: number };
export type Mensal = { mes: string; pedidos: number; valor_total: number };
export type Dashboard = {
  resumo: Resumo;
  categorias: Categoria[];
  fornecedores: Fornecedor[];
  mensal: Mensal[];
  gerado_em: string;
};
export type Pedido = {
  id: number;
  numero: string;
  fornecedor: string;
  categoria: string;
  descricao: string;
  quantidade: number;
  valor_total: number;
  status: string;
  solicitante: string;
  setor: string;
  criado_em: string;
  previsao_entrega: string;
  entregue_em: string | null;
};
export type Pagina<T> = { total: number; itens: T[] };
export type Saude = { api: string; data: string; fonte?: string };
