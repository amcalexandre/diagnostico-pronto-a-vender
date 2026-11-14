// Gera docs/index.html (documento completo para alojamento) a partir de index.html (fonte do artefacto).
const fs = require('fs');
const src = fs.readFileSync('index.html', 'utf8');
const i = src.indexOf('<div class="wrap">');
if (i < 0) throw new Error('marcador <div class="wrap"> em falta');
const head = src.slice(0, i).replace(/<meta name="claude:viewport-fit-sides"[^>]*>\n?/, '');
const desc = 'Diagnóstico gratuito para proprietários: avalie o seu imóvel em 30 critérios e saiba se está pronto para entrar no mercado.';
const out = `<!doctype html>
<html lang="pt-PT">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="${desc}">
<meta property="og:title" content="A sua casa está pronta para entrar no mercado?">
<meta property="og:description" content="${desc}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://amcalexandre.github.io/diagnostico-pronto-a-vender/icone.png">
<link rel="icon" type="image/png" href="icone.png">
<link rel="apple-touch-icon" href="icone.png">
<style>body{margin:0}img{max-width:100%}</style>
${head}</head>
<body>
${src.slice(i)}</body>
</html>
`;
fs.mkdirSync('docs', { recursive: true });
fs.writeFileSync('docs/index.html', out);
console.log('docs/index.html', out.length, 'bytes');
