import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // Tudo que a API expõe mora embaixo de /api. É isso que o nginx encaminha para cá.
  app.setGlobalPrefix('api');
  const port = Number(process.env.PORT ?? 3001);
  // 127.0.0.1: só o nginx (na mesma máquina) alcança a API. Ninguém de fora bate direto na porta.
  await app.listen(port, '127.0.0.1');
  console.log(`atlas-api no ar em http://127.0.0.1:${port}/api`);
}
bootstrap();
