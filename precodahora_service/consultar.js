// consultar.js

const PrecoDaHora = require('precodahora-api');

// Pega os argumentos da linha de comando
// Ex: node consultar.js sugestao "tomate"
const [,, tipo, arg1, arg2, arg3] = process.argv;

async function main() {
    // Instale a API localmente no projeto Django com `npm i precodahora-api`
    const client = new PrecoDaHora();

    try {
        let response;
        if (tipo === 'sugestao') {
            if (!arg1) throw new Error('O item para sugestão é obrigatório.');
            response = await client.sugestao({ item: arg1 });
        } else if (tipo === 'produto') {
            if (!arg1 || !arg2 || !arg3) throw new Error('GTIN, latitude e longitude são obrigatórios.');
            response = await client.produto({
                gtin: arg1,
                latitude: parseFloat(arg2),
                longitude: parseFloat(arg3),
                horas: 72,
                raio: 15,
                ordenar: 'preco.asc',
                pagina: 1,
                processo: 'carregar',
                totalRegistros: 0,
                totalPaginas: 0,
                pageview: 'lista'
            });
        } else {
            throw new Error("Tipo de consulta inválido. Use 'sugestao' ou 'produto'.");
        }
        
        // Imprime o resultado como uma string JSON para o Python capturar
        console.log(JSON.stringify(response.data));

    } catch (error) {
        // Imprime o erro como JSON para o Python capturar
        console.error(JSON.stringify({ error: error.message, details: error.stack }));
        process.exit(1); // Sai com código de erro
    }
}

main();
