import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Use environment variable or fallback to Docker service name
    const backendUrl = process.env.INTERNAL_API_URL || 'http://resume-genius-backend:8000';
    
    return [
      {
        source: '/api/proxy/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;