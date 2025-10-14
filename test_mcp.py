import asyncio
from fastmcp import Client
import json

# 测试查询列表
QUERIES = [
    "人工智能 虚拟现实 三维重建",
    "虚拟现实 三维重建",
    "虚拟现实",
    "三维重建",
    "人工智能"
]

# SSE 服务器 URL（匹配你的 mcp.run(port=8898)）
SSE_URL = "/sse"

async def test_batch_crawler():
    print(f"连接到 SSE 服务器: {SSE_URL}")
    print(f"查询列表: {QUERIES}")

    async with Client(SSE_URL) as client:
        # Step 1: 列出可用工具（可选，验证工具存在）
        tools = await client.list_tools()
        print(f"可用工具: {tools}")

        # Step 2: 调用工具
        print("发起工具调用...")
        start_time = time.time()
        result = await client.call_tool("run_baidu_scholar_crawler", {"queries": QUERIES})
        elapsed = time.time() - start_time
        print(f"调用完成，用时: {elapsed:.2f} 秒")

        # Step 3: 处理结果（result.content[0].text 是字符串，通常 JSON）
        if result.content:
            result_text = result.content[0].text
            print(f"原始结果: {result_text[:500]}...")  # 打印部分，避免过长
            
            try:
                result_json = json.loads(result_text)
                success_count = sum(1 for r in result_json.get("results", []) if r.get("status") == "success")
                print(f"\n解析结果: 总体状态 {result_json.get('status')}，成功查询数: {success_count}/{len(QUERIES)}")
                # 可进一步打印 details: print(json.dumps(result_json, ensure_ascii=False, indent=2))
            except json.JSONDecodeError:
                print("结果非 JSON 格式:")
                print(result_text)
        else:
            print("无结果返回。")

if __name__ == "__main__":
    import time  # 用于计时
    asyncio.run(test_batch_crawler())