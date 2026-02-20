/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        anchor: {
          navy:    '#102A43',
          blue:    '#1F3C88',
          cyan:    '#2CB1BC',
          green:   '#3EBD93',
          light:   '#F4F7FA',
          dark:    '#1F2933',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
