import { BadGatewayException, Injectable, ServiceUnavailableException } from '@nestjs/common';

/**
 * Cliente do serviço de dados (FastAPI). Os dois moram no mesmo servidor, então a conversa
 * é por localhost: não passa pela internet nem pelo nginx.
 */
@Injectable()
export class DataService {
  private readonly base = process.env.DATA_URL ?? 'http://127.0.0.1:8000';

  async get<T = unknown>(path: string, params: Record<string, string | undefined> = {}): Promise<T> {
    const url = new URL(path, this.base);
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== '') url.searchParams.set(k, v);
    }
    let res: Response;
    try {
      res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    } catch {
      throw new ServiceUnavailableException('serviço de dados indisponível');
    }
    if (!res.ok) throw new BadGatewayException(`serviço de dados respondeu ${res.status}`);
    return (await res.json()) as T;
  }

  async ping(): Promise<{ status: string; fonte?: string }> {
    try {
      return await this.get('/health');
    } catch {
      return { status: 'indisponivel' };
    }
  }
}
