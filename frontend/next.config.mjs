/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The backend base URL is read at runtime by the API client.
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1",
  },
};

export default nextConfig;
