from fastapi import FastAPI, Request, HTTPException from fastapi.middleware.cors import CORSMiddleware from fastapi.responses import FileResponse, JSONResponse from fastapi.staticfiles import StaticFiles import os import uuid import subprocess import threading import time

app = FastAPI()

Enable CORS

app.add_middleware( CORSMiddleware, allow_origins=[""], allow_methods=[""], allow_headers=["*"], )

Create downloads folder if not exists

DOWNLOAD_FOLDER = "downloads" os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

Serve static files (index.html)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

Serve robots.txt

@app.get("/robots.txt", include_in_schema=False) async def serve_robots(): return FileResponse("robots.txt", media_type="text/plain")

Delete file after a delay

def delete_file_later(path, delay=10): def remove(): time.sleep(delay) if os.path.exists(path): os.remove(path) threading.Thread(target=remove, daemon=True).start()

Video download API

@app.post("/download") async def download_video(request: Request): try: data = await request.json() url = data.get("url")

if not url:
        raise HTTPException(status_code=400, detail="\u274c URL required")

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    result = subprocess.run(
        ["yt-dlp", "-f", "mp4", "-o", filepath, url],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Download failed: {result.stderr.decode()}")

    delete_file_later(filepath, delay=10)

    return {
        "status": "success",
        "file_url": f"/downloaded/{filename}",
        "filename": filename
    }

except Exception as e:
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(e)}
    )

Serve downloaded video files

@app.get("/downloaded/{filename}", response_class=FileResponse) async def serve_file(filename: str): path = os.path.join(DOWNLOAD_FOLDER, filename) if os.path.exists(path): return FileResponse(path, media_type="video/mp4", filename=filename) raise HTTPException(status_code=404, detail="File not found")

