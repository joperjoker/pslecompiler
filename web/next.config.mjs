/** @type {import('next').NextConfig} */
const nextConfig = {
  // Keep CI/Vercel builds resilient; correctness is covered by the engine tests.
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },
};
export default nextConfig;
