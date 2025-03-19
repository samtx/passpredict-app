import commonjs from '@rollup/plugin-commonjs';
import { terser } from 'rollup-plugin-terser';
import filesize from 'rollup-plugin-filesize';
import replace from '@rollup/plugin-replace';
import svelte from 'rollup-plugin-svelte';
import resolve from '@rollup/plugin-node-resolve';
import css from "rollup-plugin-import-css";
import preprocess from 'svelte-preprocess';
import dotenv from 'dotenv';

dotenv.config();

const staticDir = 'static/';

const production = process.env.NODE_ENV == 'production';
if (production) {
    console.log('Production mode')
} else {
    console.log('Development mode')
}
const mapboxToken = production ? process.env.MAPBOX_ACCESS_TOKEN : process.env.MAPBOX_DEFAULT_TOKEN

export default [
    {
        input: staticDir + 'js/main.js',
        output: {
            file:  staticDir + 'dist/bundle.js',
            sourcemap: true,
            format: 'umd',
            name: 'Passpredict',
        },
        plugins: [
            svelte({
                compilerOptions: {
                    dev: production ? false : true,
                },
                preprocess: preprocess(),
                emitCss: true
            }),
            mapboxToken && replace({
                preventAssignment: true,
                values: {
                    MAPBOX_ACCESS_TOKEN: mapboxToken
                },
            }),
            css({ output: staticDir + 'dist/bundle.css' }),
            commonjs(),
            filesize(),
            resolve({ browser: true }),
            production && terser(),

        ]
    },
];