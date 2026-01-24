import type { NextConfig } from 'next'

// Defensive: trim and extract only the first part (before any spaces)
// This prevents "URL BACKEND_URL=..." concatenation bugs from malformed env vars
const backendUrl = (process.env.BACKEND_URL || 'http://localhost:8000').trim().split(' ')[0]

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
