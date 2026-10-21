import { Module } from '@nestjs/common';
import { DashboardController } from './dashboard.controller';
import { DashboardService } from './dashboard.service';
import { DataService } from './data.service';
import { HealthController } from './health.controller';
import { PedidosController } from './pedidos.controller';

@Module({
  controllers: [HealthController, DashboardController, PedidosController],
  providers: [DataService, DashboardService],
})
export class AppModule {}
