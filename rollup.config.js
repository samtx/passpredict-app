import commonjs from '@rollup/plugin-commonjs';
import { terser } from 'rollup-plugin-terser';
import filesize from 'rollup-plugin-filesize';


const staticDir = 'app/static/';

const production = process.env.NODE_ENV == 'production';
if (production) {
    console.log('Production mode')
} else {
    console.log('Development mode')
}

export default [
    {
        input: staticDir + 'js/home.js',
        output: {
            file:  staticDir + 'dist/home.js',
            format: 'umd'
        },
        plugins: [
            commonjs(),
            filesize(),
            production && terser(),
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
            filesize(),
            production && terser(),
        ]
    },
    // {
    //     input: staticDir + 'js/base.js',
    //     output: {
    //         file: staticDir + 'dist/base.js',
    //         format: 'umd'
    //     },
    //     plugins: [
    //         commonjs(),
    //     ]
    // },
];