/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Proxy API requests to the backend in non-production environments
  // In production, Vercel rewrites (vercel.json) handle this instead
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/backend-api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
