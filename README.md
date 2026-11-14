# Diagnóstico Pronto a Vender

Diagnóstico gratuito para proprietários: critérios ponderados em seis áreas, resultado de 0 a 100 e classe de A a E.

- `index.html`: fonte da página.
- `docs/index.html`: versão publicada, gerada com `node build.js`.
- `docs/cp/NN.json`: base própria de códigos postais (concelho e freguesia), um ficheiro por cada dois primeiros algarismos.
- `dados/`: scripts que geram essa base.

A página não guarda nem envia dados e não depende de serviços externos. O visitante decide no fim se envia o resumo por WhatsApp.

## Base de códigos postais

Fontes:
- Carta Administrativa Oficial de Portugal (CAOP) 2025, Direção-Geral do Território: limites das freguesias.
- Endereços INSPIRE do Instituto Nacional de Estatística, I.P., distribuídos pelo OpenAddresses (CC BY 4.0).

Método: cada endereço do INE é colocado na freguesia cujo polígono o contém; cada código postal fica com a freguesia onde cai a maioria dos seus endereços.

Para atualizar (por exemplo, com uma nova CAOP):
1. Numa pasta de trabalho, pôr os `.gpkg` da CAOP em `caop/` e o ficheiro de endereços como `enderecos.geojson.gz`.
2. `python dados/gerar_base_cp.py <pasta de trabalho> <pasta de trabalho>/out`
3. `python dados/gerar_ficheiros.py <pasta de trabalho>/out/cp_freguesia.json docs/cp`
4. `node build.js` e publicar.
