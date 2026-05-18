# scripts/09_verify_observability.py
import requests, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

def check_prometheus():
    resp = requests.get("http://localhost:9090/api/v1/query",
                        params={"query": 'http_requests_total{job="api-gateway"}'})
    data = resp.json()
    assert data["status"] == "success"
    print("Integration 9 OK: Prometheus metrics flowing")

def check_langsmith():
    from langsmith import Client, traceable
    client = Client(api_key=os.environ["LANGCHAIN_API_KEY"])
    project = os.environ.get("LANGCHAIN_PROJECT", "lab28")

    # Tạo 1 trace test để verify kết nối
    @traceable(project_name=project)
    def test_run(query: str) -> str:
        return f"test response for: {query}"

    test_run("integration test")

    import time; time.sleep(2)  # wait for trace to be recorded
    runs = list(client.list_runs(project_name=project, limit=1))
    assert len(runs) > 0
    print("Integration 10 OK: LangSmith traces visible")

check_prometheus()
check_langsmith()
