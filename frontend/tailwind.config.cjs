/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["index.html"],
  theme: {
    extend: {
      colors: {
        'space-cadet': '#1D3461',
        'yale-blue': '#1F487E',
        'cg-blue': '#247BA0',
        'granite-gray': '#605F5E',
        'red-salsa': '#FB3640'
      },
    },
  },
  plugins: [],
  content: ["./index.html",'./src/**/*.{svelte,js,ts}']
}
