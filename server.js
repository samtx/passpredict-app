// https://gist.github.com/davemo/4027855
// https://stackoverflow.com/a/21663820
// https://github.com/chimurai/http-proxy-middleware/issues/31#issuecomment-143770591
// https://www.npmjs.com/package/http-proxy-middleware#options

const express   = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const options = {
    target: 'http://localhost:8000',
    pathRewrite: {
        '^/api': ''
    }
}

const proxy = createProxyMiddleware(options);

const app = express();
app.use('/api', proxy);

// app.use(express.static(__dirname + '/public'));
app.get('/', function (req, res) {
    res.send('Hello from home page!')
})

app.listen(3000, () => {
    console.log('Listening on localhost:3000');
});

module.exports = app;