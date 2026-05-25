import os
import json
import requests

UPLOAD_API_URL = "https://seller-isq-ingestion-api-w2yrp7i6za-el.a.run.app/"
UPLOAD_DIR     = "upload_ready"


def upload_specs(mcat_id: int) -> dict:
    file_path = os.path.join(UPLOAD_DIR, f"upload_{mcat_id}.json")
    if not os.path.exists(file_path):
        return {"success": False, "error": f"Upload file not found: {file_path}"}
    with open(file_path, "r", encoding="utf-8") as f:
        upload_json = json.load(f)
    try:
        response = requests.post(
            UPLOAD_API_URL,
            headers={"Content-Type": "application/json"},
            json={"payload": upload_json},
            timeout=60,
        )
        response.raise_for_status()

        # Success message upload file mein append karo
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            
            # File ko dict mein wrap karo agar list hai
            output = {
                "upload_payload": existing,
                "upload_result": {
                    "status": "success",
                    "status_code": response.status_code,
                    "api_response": response.json(),
                    "uploaded_at": __import__("datetime").datetime.now().isoformat()
                }
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Upload result saved to {file_path}")
        except Exception as e:
            print(f"Could not save upload result: {e}")

        return {"success": True, "status_code": response.status_code, "response": response.json()}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": str(e), "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}
