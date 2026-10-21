/** @type {import('next').NextConfig} */
const nextConfig = {
  // 'standalone' gera uma pasta enxuta com server.js: é ela que sobe para o servidor.
  output: 'standalone',
  // Em desenvolvimento (e no 'npm start' local) o front chama /api/... e o Next repassa para a API.
  // Em produção quem faz isso é o nginx, antes de a requisição chegar aqui.
  async rewrites() {
    const api = process.env.API_ORIGIN ?? 'http://127.0.0.1:3001';
    return [{ source: '/api/:path*', destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
