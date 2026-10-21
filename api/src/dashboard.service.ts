import { Injectable } from '@nestjs/common';
import { DataService } from './data.service';

/** Junta quatro consultas do serviço de dados numa resposta só, para o front fazer uma chamada. */
@Injectable()
export class DashboardService {
  constructor(private readonly data: DataService) {}

  async montar() {
    const [resumo, categorias, fornecedores, mensal] = await Promise.all([
      this.data.get('/insights/resumo'),
      this.data.get('/insights/categorias'),
      this.data.get('/insights/fornecedores', { top: '5' }),
      this.data.get('/insights/mensal'),
    ]);
    return { resumo, categorias, fornecedores, mensal, gerado_em: new Date().toISOString() };
  }
}
