/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                cyber: {
                    green: '#00ff41',
                    black: '#0b0c10',
                    dark: '#1f2833',
                    red: '#c5c6c7',
                    blue: '#66fcf1',
                    accent: '#45a29e'
                }
            },
        },
    },
    plugins: [],
}
