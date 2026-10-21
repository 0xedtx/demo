import { Controller, Get, Query } from '@nestjs/common';
import { DataService } from './data.service';

@Controller('pedidos')
export class PedidosController {
  constructor(private readonly data: DataService) {}

  @Get()
  listar(
    @Query('status') status?: string,
    @Query('categoria') categoria?: string,
    @Query('limit') limit?: string,
    @Query('offset') offset?: string,
  ) {
    return this.data.get('/pedidos', { status, categoria, limit, offset });
  }
}
