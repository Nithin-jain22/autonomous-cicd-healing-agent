import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#7C5CFF',
        'primary-glow': '#9F87FF',
        accent: '#00E0B8',
        danger: '#FF4D6D',
        warning: '#FFB020',
        bgmain: '#0B0F1A',
        bgsurface: '#111827',
        bgelevated: '#1F2937',
        bghover: '#1A2235',
        'text-primary': '#F9FAFB',
        'text-secondary': '#9CA3AF',
        'text-muted': '#6B7280',
      },
      boxShadow: {
        card: '0 10px 30px rgba(0,0,0,0.4)',
      },
      borderRadius: {
        card: '16px',
      },
    },
  },
  plugins: [],
} satisfies Config
