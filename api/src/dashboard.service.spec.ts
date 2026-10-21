import { DashboardService } from './dashboard.service';
import { DataService } from './data.service';

describe('DashboardService', () => {
  it('junta as quatro consultas e carimba o horário', async () => {
    const get = jest.fn(async (path: string) => ({ path }));
    const service = new DashboardService({ get } as unknown as DataService);

    const r = await service.montar();

    expect(get).toHaveBeenCalledTimes(4);
    expect(r.resumo).toEqual({ path: '/insights/resumo' });
    expect(r.mensal).toEqual({ path: '/insights/mensal' });
    expect(typeof r.gerado_em).toBe('string');
  });
});
