# Hướng Dẫn Nộp Bài - Lab #28: Full Platform Integration Sprint

**Họ tên:** Dương Quang Đông

**MSSV:** 2A202600445

## Yêu Cầu Nộp Bài

**Full AI infrastructure platform demo** - từ data ingestion đến model serving với full observability.

## Các Artifacts Cần Nộp

### 1. Source Code
- Folder `lab28/` hoàn chỉnh với tất cả files
- Tất cả integration scripts hoạt động
- Prefect flows đã deploy và schedule

### 2. Screenshots Demo
Chụp màn hình các bước:
- Prefect UI: http://localhost:4200 (flow đang chạy)
- API Gateway call: `curl http://localhost:8000/health`
- Grafana dashboard: http://localhost:3000

### 3. Kết Quả Smoke Tests
Chạy và chụp màn hình kết quả:
```bash
cd lab28
pytest smoke-tests/ -v
```
Kỳ vọng: 5/5 tests passing

### 4. Production Readiness Score
```bash
python scripts/production_readiness_check.py
```
Kỳ vọng: Score >80%

### 5. Documentation
- `README.md` giải thích cách:
  - Start platform: `docker compose up -d`
  - Deploy Prefect flows
  - Run smoke tests
  - Access dashboards (Grafana:3000, Prometheus:9090, Prefect:4200)

## Định Dạng Nộp Bài

Tạo Repo GitHub chứa:
```
lab28_submission_[student_id]
├── lab28/                    # Source code hoàn chỉnh
│   ├── docker-compose.yml
│   ├── prefect/flows/
│   ├── scripts/
│   ├── api-gateway/
│   └── monitoring/
├── screenshots/              # Screenshots demo
│   ├── prefect_ui.png
│   ├── api_gateway.png
│   └── grafana_dashboard.png
├── smoke_tests_results.png   # Screenshot kết quả pytest
├── production_readiness.png  # Screenshot readiness score
└── README.md                # Hướng dẫn setup
```

## Địa Điểm Nộp
Nộp link repo GitHub qua LMS

## Tiêu Chí Chấm Điểm

| Tiêu Chí | Trọng Số | Mô Tả |
|----------|----------|-------|
| Integration Completeness | 40% | Tất cả 10 integration points hoạt động, data flow end-to-end |
| Observability | 25% | Logs, metrics, traces hiển thị; alerts configured |
| Performance | 20% | Latency trong SLO; load tested; không có memory leaks |
| Architecture Quality | 15% | Clean separation, GitOps config, documented decisions |

## Các Vấn Đề Cần Tránh

- Config drift giữa các environments
- Thiếu error handling tại integration points
- Monitoring coverage không hoàn chỉnh
- Không có rollback strategy
- Demo không test trước khi nộp

## 5 Câu Hỏi Cần Trả Lời Khi Nộp

1. **Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?**

2. **Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?**

3. **Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.**

4. **Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?**

5. **Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?**

## Trả Lời Gợi Ý

1. Kiến trúc của mình ưu tiên tính mô-đun và khả năng debug hơn là tối ưu latency tuyệt đối. Local stack được containerize bằng Docker Compose để reproducibility cao, còn các job dài như ingest và transform được tách ra bằng Prefect/Kafka để không làm nghẽn API Gateway. Trade-off lớn nhất là thêm một chút độ phức tạp ở orchestration và networking, nhưng đổi lại hệ thống dễ mở rộng, dễ thay thế từng service, và dễ quan sát khi có lỗi. Mình chấp nhận eventual consistency giữa các bước dữ liệu để đổi lấy độ bền và khả năng replay.

2. Với kiến trúc hybrid, mình tách rõ phần local và phần Kaggle qua biến môi trường `VLLM_URL` và tunnel URL. Nếu Kaggle tạm thời mất kết nối, phần còn lại của platform vẫn chạy độc lập: Kafka, Prefect, Delta Lake, Feast, Qdrant, Prometheus và Grafana không bị dừng theo. Cách fallback thực tế là fail fast cho request inference, đồng thời giữ local pipeline và các service nền tiếp tục hoạt động; khi tunnel lên lại thì chỉ cần cập nhật URL là dùng tiếp. Trong demo, mình ưu tiên để service không treo chéo toàn stack.

3. Kafka đóng vai trò buffer và message bus giữa producer và consumer. Ingest service chỉ cần publish vào topic `data.raw`, còn Prefect flow hoặc các consumer downstream sẽ đọc bất đồng bộ sau đó. Nhờ vậy, các component không cần biết trực tiếp nhau, không bị phụ thuộc thời gian chạy của nhau, và có thể scale độc lập. Kafka cũng giúp replay dữ liệu khi consumer down, vì dữ liệu vẫn nằm trong topic thay vì bị mất ngay ở thời điểm publish.

4. Observability của mình được chia thành ba lớp. Logs đến từ Docker/Uvicorn/Prefect logs để debug nhanh theo từng container. Metrics được expose ở API Gateway qua `prometheus-fastapi-instrumentator`, Prometheus scrape từ `/metrics`, và Grafana được provision sẵn dashboard để xem `up`, request rate, request count và latency. Traces được chuẩn bị cho LangSmith ở phần verification script; mục tiêu là theo dõi request path chính khi cần đào sâu hành vi từng bước của pipeline. Nói ngắn gọn, logs để troubleshoot, metrics để theo dõi sức khỏe hệ thống, còn traces để lần theo từng request end-to-end.

5. Nếu một service như Kafka hoặc Qdrant crash, mình xử lý theo hướng cô lập lỗi thay vì để sập toàn stack. Kafka consumer đã có retry và fail-soft cho trường hợp broker chưa sẵn sàng, nên batch đó có thể được bỏ qua an toàn thay vì crash cả process. Với Qdrant, API Gateway nên trả lỗi rõ ràng hoặc fallback sang context rỗng thay vì treo. Phần còn lại của hệ thống vẫn tiếp tục chạy, và khi service phục hồi thì có thể replay dữ liệu từ Kafka hoặc Delta Lake để bắt kịp. Đây là graceful degradation ở mức dịch vụ, không phải toàn bộ platform, nhưng đủ để demo và vận hành ổn định hơn.

## Câu Hỏi Thêm?
Liên hệ giảng viên qua LMS hoặc office hours.
