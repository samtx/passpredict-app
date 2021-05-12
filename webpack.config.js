module.exports = {
    entry: {
        home: './app/static/js/home.js',
        passes: './app/static/js/passes.js',
    },
    output: {
        filename: '[name].js',
        path: __dirname + '/app/static/dist',
    },
};