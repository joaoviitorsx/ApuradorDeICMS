import aiohttp
import asyncio

async def consultar_cnpj(cnpj):
    url = f"https://minhareceita.org/{cnpj}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    cnae = data.get("cnae_fiscal", "")
                    uf = data.get("uf", "")
                    simples = "Sim" if data.get("simples") else "Não"
                    status = data.get("descricao_situacao_cadastral", "")
                    return (cnae, status, uf, simples)
    except Exception as e:
        print(f"Erro ao consultar CNPJ {cnpj}: {e}")
    return ("", "", "", "")

async def processar_cnpjs(lista_cnpjs):
    resultados = {}
    tasks = []

    for cnpj in lista_cnpjs:
        tasks.append(consultar_cnpj(cnpj))

    respostas = await asyncio.gather(*tasks)

    for i, cnpj in enumerate(lista_cnpjs):
        resultados[cnpj] = respostas[i]

    return resultados
