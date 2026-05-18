# LAB 28 - Status & Next Steps

## Tình trạng hiện tại

Dựa trên code và artifacts trong repo, project đang ở mức **đã dựng xong phần nền tảng chính**, nhưng **chưa được xác nhận end-to-end**.

### Đã có sẵn

- `docker-compose.yml` cho Kafka, Prefect, Qdrant, Redis, Prometheus, Grafana và API Gateway.
- `prefect/flows/kafka_to_delta.py` cho luồng Kafka -> Delta Lake.
- Các script tích hợp:
  - `scripts/01_ingest_to_kafka.py`
  - `scripts/03_delta_to_feast.py`
  - `scripts/05_embed_to_qdrant.py`
  - `scripts/09_verify_observability.py`
  - `scripts/production_readiness_check.py`
- Smoke tests ở `smoke-tests/test_e2e.py`.
- Tài liệu hướng dẫn ở `README.md`, `LAB28_GUIDE.md`, `SUBMISSION.md`.
- Có parquet artifacts trong `delta-lake/raw`, cho thấy ít nhất một phần pipeline đã từng chạy.

### Chưa hoàn tất / còn rủi ro

- Chưa thấy bằng chứng smoke tests và readiness check đã pass ổn định.
- Phần Kaggle tunnel vẫn là dependency bên ngoài, cần xác nhận URL thực tế đang hoạt động.
- API Gateway đang nối vào `VLLM_URL` theo dạng base URL, nhưng `.env` hiện có thể đã chứa `/v1`; cần chuẩn hoá để tránh gọi sai endpoint.
- Observability và LangSmith tracing chưa có bằng chứng được verify end-to-end.

## Ước lượng tiến độ

- **Hoàn thiện hiện tại:** khoảng **70%**.
- **Lý do:** phần kiến trúc, script, và tài liệu đã có; phần còn lại chủ yếu là verify, harden, và chốt submission artifacts.

## Plan hoàn thiện

### P0 - Bắt buộc để demo chạy được

- [ ] Chuẩn hoá biến môi trường cho Kaggle tunnel trong `.env`.
- [ ] Sửa và kiểm tra base URL của `VLLM_URL` trong API Gateway để không bị lặp `/v1`.
- [ ] Khởi động local stack và xác nhận các service chính đều healthy.
- [ ] Chạy Kaggle notebook để đảm bảo vLLM và embedding service có URL ổn định.
- [ ] Chạy luồng end-to-end: ingest -> Kafka -> Prefect -> Delta Lake -> Feast -> Qdrant.
- [ ] Chạy `pytest smoke-tests/ -v` và ghi nhận kết quả.
- [ ] Chạy `python scripts/production_readiness_check.py` và đạt score > 80%.

### P1 - Cứng hoá hệ thống

- [ ] Thêm retry/timeout/error handling rõ ràng cho API Gateway.
- [ ] Xử lý graceful fallback nếu Qdrant, Redis, hoặc Kaggle endpoint tạm thời không sẵn sàng.
- [ ] Xác nhận Prometheus scrape metrics và Grafana dashboard hiển thị đúng.
- [ ] Bật và verify LangSmith tracing cho request path chính.
- [ ] Cập nhật README bằng runbook ngắn, rõ ràng, đúng thứ tự chạy.

### P2 - Chuẩn bị nộp bài

- [ ] Chụp screenshot Prefect UI khi flow đang chạy.
- [ ] Chụp screenshot `curl http://localhost:8000/health` và một request chat thành công.
- [ ] Chụp screenshot Grafana dashboard.
- [ ] Chụp screenshot kết quả smoke tests.
- [ ] Chụp screenshot production readiness score.
- [ ] Rà lại `SUBMISSION.md` và đóng gói repo theo đúng cấu trúc nộp.

## Thứ tự thực thi khuyến nghị

1. Fix URL/env cho Kaggle -> Gateway.
2. Bring up local stack.
3. Chạy Kaggle notebook và xác nhận tunnel.
4. Chạy pipeline end-to-end.
5. Chạy smoke tests và readiness check.
6. Chụp screenshots và hoàn thiện submission.

## Definition of Done

- Local stack lên được bằng `docker compose up -d`.
- API Gateway trả `200` ở `/health`.
- `smoke-tests/test_e2e.py` pass.
- `production_readiness_check.py` đạt trên 80%.
- Có đầy đủ screenshot và hướng dẫn nộp bài.