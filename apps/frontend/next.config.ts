import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Use environment variable or fallback to Docker service name
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

    return [
      {
        source: "/api/proxy/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
