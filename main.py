

from fastapi import FastAPI, Request, HTTPException from fastapi.middleware.cors import CORSMiddleware from fastapi.responses import FileResponse, JSONResponse, HTMLResponse from fastapi.staticfiles import StaticFiles import os import uuid import subprocess import threading import time

app = FastAPI()

CORS setup

app.add_middleware( CORSMiddleware, allow_origins=[""], allow_methods=[""], allow_headers=["*"], )

Create downloads folder

DOWNLOAD_FOLDER = "downloads" os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

Mount static files

app.mount("/static", StaticFiles(directory="static"), name="static")

Serve index.html on root

@app.get("/", response_class=HTMLResponse) async def read_index(): try: with open("static/index.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read(), status_code=200) except Exception as e: return HTMLResponse( content=f"<pre>Homepage load error:\n{type(e).name}: {str(e)}</pre>", status_code=500 )

Serve robots.txt

@app.get("/robots.txt", include_in_schema=False) async def serve_robots(): return FileResponse("robots.txt", media_type="text/plain")

Auto-delete files after a delay

def delete_file_later(path, delay=10): def remove(): time.sleep(delay) if os.path.exists(path): os.remove(path) threading.Thread(target=remove, daemon=True).start()

Download video route

@app.post("/download") async def download_video(request: Request): try: data = await request.json() url = data.get("url")

if not url:
        raise HTTPException(status_code=400, detail="❌ URL required")

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

Serve downloaded video

@app.get("/downloaded/{filename}", response_class=FileResponse) async def serve_file(filename: str): path = os.path.join(DOWNLOAD_FOLDER, filename) if os.path.exists(path): return FileResponse(path, media_type="video/mp4", filename=filename) raise HTTPException(status_code=404, detail="File not found")

