const https = require('https');
const fs = require('fs');
const next = require('next');

const port = 3040;
const app = next({ dev: false, conf: { /* suas configs aqui */ } });
const handle = app.getRequestHandler();

const httpsOptions = {
  key: fs.readFileSync('/root/ssl/localhost.key'),
  cert: fs.readFileSync('/root/ssl/localhost.crt'),
};

app.prepare().then(() => {
  https.createServer(httpsOptions, (req, res) => {
    handle(req, res);
  }).listen(port, () => {
    console.log(`HTTPS server rodando em https://localhost:${port}`);
  });
});
