const apiBase = process.env.NEXT_PUBLIC_API_URL;

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow long-running proxied requests (motion generation takes 1-3 min)
  experimental: {
    proxyTimeout: 300000,
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**" },
      { protocol: "http", hostname: "localhost" },
    ],
  },
  async rewrites() {
    if (apiBase) {
      return [
        {
          source: "/api/:path*",
          destination: `${apiBase}/api/:path*`,
        },
        {
          source: "/media/:path*",
          destination: `${apiBase}/media/:path*`,
        },
      ];
    }

    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/media/:path*",
        destination: "http://localhost:8000/media/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
