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
        input: staticDir + 'js/main.js',
        output: {
            file:  staticDir + 'dist/bundle.js',
            sourcemap: true,
            format: 'umd',
            external: ['alpinejs']
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
];