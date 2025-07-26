import os, threading, time, subprocess, uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Mount static directory
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.on_event("startup")
def show_structure():
    print("STATIC DIR CONTENTS:", os.listdir("static"))

@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except Exception as e:
        return HTMLResponse(
            content=f"<pre>ERROR:\n{type(e).__name__}: {e}</pre>",
            status_code=500
        )

@app.get("/robots.txt", include_in_schema=False)
async def robots():
    return FileResponse("robots.txt", media_type="text/plain")

def delete_file_later(path, delay=10):
    def rm():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=rm, daemon=True).start()

@app.post("/download")
async def download_video(request: Request):
    try:
        data = await request.json()
        url = data.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="❌ URL required")
        filename = f"{uuid.uuid4()}.mp4"
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        result = subprocess.run(["yt-dlp", "-f", "mp4", "-o", path, url],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise HTTPException(status_code=500,
                                detail=f"Download failed: {result.stderr.decode()}")
        delete_file_later(path, delay=10)
        return {"status": "success", "file_url": f"/downloaded/{filename}", "filename": filename}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/downloaded/{filename}", response_class=FileResponse)
async def serve_file(filename: str):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="File not found")
