import commonjs from '@rollup/plugin-commonjs';
import { terser } from 'rollup-plugin-terser';
import filesize from 'rollup-plugin-filesize';
import replace from '@rollup/plugin-replace';
import dotenv from 'dotenv';

dotenv.config();

const staticDir = 'static/';

const production = process.env.NODE_ENV == 'production';
const mapboxToken = production ? process.env.MAPBOX_ACCESS_TOKEN : process.env.MAPBOX_ACCESS_TOKEN_DEV
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
            sourcemap: true,
            format: 'umd'
        },
        plugins: [
            mapboxToken && replace({
                preventAssignment: true,
                values: {
                    MAPBOX_ACCESS_TOKEN: mapboxToken
                },
            }),
            commonjs(),
            filesize(),
            production && terser(),
        ]
    },
    {
        input: staticDir + 'js/passes.js',
        output: {
            file: staticDir + 'dist/passes.js',
            sourcemap: true,
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