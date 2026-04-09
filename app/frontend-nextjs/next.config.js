/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  rewrites: async () => {
    return {
      beforeFiles: [
        // Proxy API calls to Python backend
        {
          source: '/api/:path*',
          destination: `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/:path*`,
        },
      ],
    };
  },
};

module.exports = nextConfig;
