import commonjs from '@rollup/plugin-commonjs';

const staticDir = 'app/static/';

export default [
    {
        input: staticDir + 'js/home.js',
        output: {
            file:  staticDir + 'dist/home.js',
            format: 'umd'
        },
        plugins: [
            commonjs(),
        ]
    },
    {
        input: staticDir + 'js/passes.js',
        output: {
            file: staticDir + 'dist/passes.js',
            format: 'umd'
        },
        plugins: [
            commonjs(),
        ]
    },
];