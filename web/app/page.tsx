'use client';

import { useEffect, useState } from 'react';
import type { Dashboard, Pagina, Pedido, Saude } from '../lib/types';

const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
const STATUS = ['', 'pendente', 'aprovado', 'entregue', 'atrasado', 'cancelado'];

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} respondeu ${r.status}`);
  return r.json() as Promise<T>;
}

function Pill({ nome, estado }: { nome: string; estado: string }) {
  return (
    <span className={`pill ${estado === 'ok' ? 'ok' : 'fora'}`}>
      {nome}: {estado === 'ok' ? 'no ar' : 'fora do ar'}
    </span>
  );
}

export default function Page() {
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [saude, setSaude] = useState<Saude | null>(null);
  const [pedidos, setPedidos] = useState<Pagina<Pedido> | null>(null);
  const [status, setStatus] = useState('');
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([get<Dashboard>('/api/dashboard'), get<Saude>('/api/health')])
      .then(([d, s]) => {
        setDash(d);
        setSaude(s);
      })
      .catch((e: Error) => setErro(e.message));
  }, []);

  useEffect(() => {
    const q = new URLSearchParams({ limit: '8' });
    if (status) q.set('status', status);
    get<Pagina<Pedido>>(`/api/pedidos?${q}`)
      .then(setPedidos)
      .catch(() => setPedidos(null));
  }, [status]);

  const maxCat = Math.max(1, ...(dash?.categorias.map((c) => c.valor_total) ?? [1]));
  const maxMes = Math.max(1, ...(dash?.mensal.map((m) => m.valor_total) ?? [1]));

  return (
    <main>
      <header>
        <div>
          <h1>MonitoraME</h1>
          <p className="sub">Painel de dados abertos</p>
        </div>
        <div className="pills">
          <Pill nome="web" estado="ok" />
          <Pill nome="api" estado={saude?.api ?? 'indisponivel'} />
          <Pill nome="dados" estado={saude?.data ?? 'indisponivel'} />
          {saude?.fonte && <span className="pill neutro">fonte: {saude.fonte}</span>}
        </div>
      </header>

      {erro && (
        <p className="erro">
          Não consegui falar com a API ({erro}). Ela está rodando? Veja docs/COMO-FUNCIONA.md.
        </p>
      )}

      {dash && (
        <>
          <section className="cards">
            <div className="card"><span>Valor comprado</span><strong>{brl.format(dash.resumo.valor_total)}</strong></div>
            <div className="card"><span>Pedidos</span><strong>{dash.resumo.total_pedidos}</strong></div>
            <div className="card"><span>Ticket médio</span><strong>{brl.format(dash.resumo.ticket_medio)}</strong></div>
            <div className="card alerta"><span>Atrasados</span><strong>{dash.resumo.atrasados}</strong></div>
          </section>

          <section className="duas">
            <div className="painel">
              <h2>Gasto por categoria</h2>
              {dash.categorias.map((c) => (
                <div className="barra" key={c.categoria}>
                  <span>{c.categoria}</span>
                  <div><i style={{ width: `${(c.valor_total / maxCat) * 100}%` }} /></div>
                  <b>{brl.format(c.valor_total)}</b>
                </div>
              ))}
            </div>
            <div className="painel">
              <h2>Gasto por mês</h2>
              <div className="meses">
                {dash.mensal.map((m) => (
                  <div key={m.mes} title={`${m.mes}: ${brl.format(m.valor_total)} em ${m.pedidos} pedidos`}>
                    <i style={{ height: `${(m.valor_total / maxMes) * 100}%` }} />
                    <span>{m.mes.slice(5)}</span>
                  </div>
                ))}
              </div>
              <h2 className="mt">Top fornecedores</h2>
              <ol>
                {dash.fornecedores.map((f) => (
                  <li key={f.fornecedor}>{f.fornecedor} <b>{brl.format(f.valor_total)}</b></li>
                ))}
              </ol>
            </div>
          </section>
        </>
      )}

      <section className="painel">
        <div className="linha">
          <h2>Pedidos recentes</h2>
          <label>
            status{' '}
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUS.map((s) => (
                <option key={s} value={s}>{s || 'todos'}</option>
              ))}
            </select>
          </label>
        </div>
        <table>
          <thead>
            <tr><th>Número</th><th>Fornecedor</th><th>Item</th><th>Valor</th><th>Status</th></tr>
          </thead>
          <tbody>
            {pedidos?.itens.map((p) => (
              <tr key={p.id}>
                <td>{p.numero}</td>
                <td>{p.fornecedor}</td>
                <td>{p.quantidade}× {p.descricao}</td>
                <td>{brl.format(p.valor_total)}</td>
                <td><span className={`st ${p.status}`}>{p.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
        {pedidos && <p className="sub">{pedidos.total} pedidos nesse filtro</p>}
      </section>
    </main>
  );
}
