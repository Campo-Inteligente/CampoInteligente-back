import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(api_key="vrxpoQtgLpMp7NOTzx_9nHG6Zox26j2vd3Kr9wzUjfkofrKMGaxzkSYM719BNYAwDD-9aDHirmT3BlbkFJ_6Emf-HlutjWl6ALaEv3ymz7f_q-0oIp0dgsJLwAUDSlzUj_KT49KpKsj6_ie9KowKnf0zICEA")
    resp = await client.models.list()
    print(resp)

asyncio.run(main())
