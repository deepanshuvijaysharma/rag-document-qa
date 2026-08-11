"""Live E2E Integration Verification Script against running FastAPI backend."""

import os
import json
import urllib.request

def run_verification():
    print("=== LIVE E2E INTEGRATION VERIFICATION ===")

    # 1. Health Check
    health_req = urllib.request.urlopen("http://127.0.0.1:8000/health")
    health_res = json.loads(health_req.read().decode())
    print("1. Health Status:", health_res)
    assert health_res["status"] == "ok"

    # 2. PDF Document Ingestion
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../documents/sample_employee_handbook.pdf"))
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    head = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="sample_employee_handbook.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
    tail = f'\r\n--{boundary}--\r\n'
    body = head.encode("utf-8") + pdf_bytes + tail.encode("utf-8")

    up_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/documents/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    up_res = json.loads(urllib.request.urlopen(up_req).read().decode())
    print("2. Ingest Upload Result:", up_res)
    doc_id = up_res["document_id"]
    assert up_res["filename"] == "sample_employee_handbook.pdf"
    assert up_res["page_count"] == 2
    assert up_res["chunk_count"] == 2

    # 3. List Documents
    list_req = urllib.request.urlopen("http://127.0.0.1:8000/api/documents")
    list_res = json.loads(list_req.read().decode())
    print("3. Active Documents Count:", list_res["total_count"])
    assert list_res["total_count"] >= 1

    # 4. Grounded RAG Q&A Request
    chat_payload = json.dumps({
        "message": "What is the annual leave policy?"
    }).encode("utf-8")

    chat_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/chat",
        data=chat_payload,
        headers={"Content-Type": "application/json"}
    )
    chat_res = json.loads(urllib.request.urlopen(chat_req).read().decode())
    print("4. RAG Answer:", chat_res["answer"])
    print("4. Source Citations:", chat_res["sources"])

    assert len(chat_res["sources"]) >= 1
    assert chat_res["sources"][0]["filename"] == "sample_employee_handbook.pdf"
    assert chat_res["sources"][0]["page_number"] == 1

    # 5. Delete Document & Purge Vectors
    del_req = urllib.request.Request(f"http://127.0.0.1:8000/api/documents/{doc_id}", method="DELETE")
    del_res = json.loads(urllib.request.urlopen(del_req).read().decode())
    print("5. Delete Status:", del_res)
    assert del_res["status"] == "deleted"

    print("=== ALL LIVE E2E INTEGRATION CHECKS PASSED 100% ===")

if __name__ == "__main__":
    run_verification()
