from typing import Dict
from fastapi import FastAPI, HTTPException, Depends
from transmission_rpc import Client
from .torrents import search, get_magnet_link
import dotenv
import os
from time import sleep
import random
import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

dotenv.load_dotenv()

# Load environment variables
host = os.getenv("TRANS_HOST")
port = os.getenv("TRANS_PORT")
username = os.getenv("TRANS_USERNAME")
password = os.getenv("TRANS_PASSWORD")

secret_key = os.getenv("JWT_KEY", os.getenv("JWT_KEY"))
algorithm = "HS256"


def create_jwt_token(username: str) -> str:
    # Define token expiration time (e.g., 1 hour)
    expiration = datetime.utcnow() + timedelta(days=30)

    # Define the token payload
    payload = {
        "sub": username,  # Subject of the token
        "exp": expiration  # Expiration time of the token
    }

    # Generate and return the token
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


# OAuth2PasswordBearer is used to specify the token type
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    try:
        # Decode the token
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

client = Client(host=host, port=port, username=username, password=password)
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, or specify a list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods, or specify a list of allowed methods
    allow_headers=["*"],  # Allow all headers, or specify a list of allowed headers
)


@app.get("/trans/status")
async def get_transmission_status(username: str = Depends(verify_token)):
    try:
        session_stats = client.session_stats()
        return session_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get transmission status")

@app.get("/trans/torrent")
async def get_transmission_torrents(username: str = Depends(verify_token)):
    try:
        torrents = client.get_torrents()
        return torrents
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get torrents")

@app.get("/trans/torrent/{torrent_id}")
async def get_transmission_torrent(torrent_id: str, username: str = Depends(verify_token)):
    try:
        torrent = client.get_torrent(torrent_id)
        return torrent
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get torrent")

@app.post("/trans/torrent")
async def add_transmission_torrent(body: dict, username: str = Depends(verify_token)):
    try:
        # Get the data from the request body
        magnet_link = body.get("magnet_link")
        content_type = body.get("type")

        if content_type == "movie":
            download_dir = os.getenv("MOVIE_DIR")
        elif content_type == "tv_show":
            download_dir = os.getenv("TV_SHOW_DIR")
        else:
            raise HTTPException(status_code=400, detail="Invalid content type")
        
        if not magnet_link:
            raise HTTPException(status_code=400, detail="Magnet link is required")

        torrent = client.add_torrent(torrent=magnet_link, download_dir=download_dir)

        return torrent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/trans/torrent/{torrent_id}")
async def delete_transmission_torrent(torrent_id: str, username: str = Depends(verify_token)):
    try:
        torrent = client.get_torrent(torrent_id)
        client.remove_torrent(torrent_id)
        return {"message": "Torrent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trans/torrent/start")
async def start_transmission_torrent(username: str = Depends(verify_token)):
    try:
        client.start_all()
        return {"message": "All Torrents started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trans/torrent/start/{torrent_id}")
async def start_transmission_torrent(torrent_id: str, username: str = Depends(verify_token)):
    try:
        result = client.start_torrent(torrent_id)
        return {"message": "Torrent started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trans/torrent/stop/{torrent_id}")
async def stop_transmission_torrent(torrent_id: str, username: str = Depends(verify_token)):
    try:
        client.stop_torrent(torrent_id)
        return {"message": "Torrent stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trans/set-speed")
async def set_speed(body: dict, username: str = Depends(verify_token)):
    try:
        download_speed = body.get("download_speed")
        upload_speed = body.get("upload_speed")

        # Convert bytes to KB
        download_speed = download_speed
        upload_speed = upload_speed

        client.set_session(speed_limit_down=download_speed, speed_limit_up=upload_speed, speed_limit_down_enabled=True, speed_limit_up_enabled=True)
        return {"message": "Speed limits set successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/torrents/search")
async def search_torrent(query: str, username: str = Depends(verify_token)):
    try:
        torrents = search(query)
        return torrents
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/torrents/magnet")
async def get_magnet(query: str, username: str = Depends(verify_token)):
    try:
        magnet_link = get_magnet_link(query)
        return magnet_link
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(body: dict):
    sleep(random.randint(1, 3))
    try:
        # See if username and password are set
        username = body.get("username")
        password = body.get("password")

        if not username or not password:
            raise HTTPException(status_code=400, detail="Unauthorized")
        
        if username == os.getenv("API_USERNAME") and password == os.getenv("API_PASSWORD"):
            # Generate JWT token
            token = create_jwt_token(username)
            return {"access_token": token}
        
        raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))