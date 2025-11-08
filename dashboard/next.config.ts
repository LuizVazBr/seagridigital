import type { NextConfig } from "next";
import withPWA from "next-pwa";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [],
    // ou apenas permitir qualquer localhost ou domínio
    unoptimized: false, 
  },
  basePath: '',
  eslint: { ignoreDuringBuilds: true },
};

export default withPWA({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
})(nextConfig);
