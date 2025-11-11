#!/usr/bin/env python3
"""
SDR API Gateway Server
Provides RESTful and gRPC APIs for SDR ground station control and monitoring

Author: 蔡秀吉 (Hsiu-Chi Tsai)
Date: 2025-10-27
Version: 1.0.0

Implementation Status: 🟡 SIMULATED
- Core API structure implemented
- Hardware interfaces are mocked (USRP drivers need real hardware)
- Production deployment requires actual USRP devices

Requirements Satisfied:
- FR-SDR-005: RESTful API Exposure
- FR-INT-002: Control Plane API
- NFR-SEC-001: Authentication & Authorization
"""

from fastapi import FastAPI, HTTPException, Depends, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn
import asyncio
import logging
import os
import secrets
import zmq
import zmq.asyncio
import numpy as np
import json
import threading
from collections import deque

# =============================================================================
# Configuration
# =============================================================================

# Security: Load SECRET_KEY from environment variable or K8s Secret
# Generate a secure random key if not set (for development only)
SECRET_KEY = os.environ.get("SDR_API_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(32)
    logging.warning(
        "SECRET_KEY not set in environment. Using generated key for this session. "
        "Set SDR_API_SECRET_KEY environment variable for production."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Simulated USRP Device Pool
USRP_DEVICES = {
    "usrp-001": {"model": "B210", "serial": "3234ABC", "status": "online"},
    "usrp-002": {"model": "X310", "serial": "5678DEF", "status": "online"},
    "usrp-003": {"model": "N320", "serial": "9101GHI", "status": "offline"},
}

# Simulated Station Configurations
STATIONS = {}

# LEO NTN IQ Sample Integration (FR-INT-004)
LEO_ZMQ_ENDPOINT = os.environ.get("LEO_ZMQ_ENDPOINT", "tcp://leo-ntn-simulator:5555")
IQ_SAMPLE_STATS = {
    "connected": False,
    "frames_received": 0,
    "last_frame_id": None,
    "last_timestamp": None,
    "last_sample_rate": None,
    "last_num_samples": None,
    "last_doppler_hz": None,
    "last_delay_ms": None,
    "last_fspl_db": None,
    "total_samples_received": 0,
    "average_snr_db": None,
    "average_power_db": None,
    "errors": 0,
}
IQ_SAMPLE_BUFFER = deque(maxlen=100)  # Keep last 100 frames in memory

# =============================================================================
# Data Models (Pydantic)
# =============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class StationConfig(BaseModel):
    """SDR Station Configuration Model (FR-SDR-001, FR-SDR-002)"""
    station_id: str = Field(
        ...,
        description="Unique station identifier",
        pattern="^[a-zA-Z0-9_-]{1,64}$",
        min_length=1,
        max_length=64
    )
    usrp_device: str = Field(
        ...,
        description="USRP device ID",
        pattern="^usrp-[0-9]{3}$"
    )
    frequency_band: str = Field(
        ...,
        description="C, Ku, or Ka",
        pattern="^(C|Ku|Ka)$"
    )
    center_frequency_ghz: float = Field(..., ge=1.0, le=40.0)
    sample_rate_msps: float = Field(..., ge=1.0, le=200.0)
    antenna_config: Dict[str, Any] = Field(..., description="Antenna parameters")
    modulation_scheme: str = Field(
        "QPSK",
        description="QPSK, 8PSK, 16APSK, 32APSK",
        pattern="^(QPSK|8PSK|16APSK|32APSK)$"
    )
    oran_integration: bool = Field(False, description="Enable O-RAN data plane")
    oran_endpoint: Optional[str] = Field(
        None,
        description="gRPC endpoint for O-RAN DU",
        pattern="^[a-zA-Z0-9.-]+:[0-9]{1,5}$"
    )


class StationStatus(BaseModel):
    """SDR Station Status Model (FR-SDR-005, FR-INT-003)"""
    station_id: str
    status: str  # "running", "stopped", "error"
    usrp_connected: bool
    signal_snr_db: Optional[float] = None
    ebn0_db: Optional[float] = None
    packet_error_rate: Optional[float] = None
    usrp_temperature_c: Optional[float] = None
    data_rate_mbps: Optional[float] = None
    last_updated: datetime


class MetricsResponse(BaseModel):
    """Prometheus-compatible metrics (NFR-INT-003)"""
    station_id: str
    metrics: Dict[str, float]
    timestamp: datetime


class IQSampleStats(BaseModel):
    """LEO NTN IQ Sample Statistics (FR-INT-004)"""
    connected: bool
    frames_received: int
    last_frame_id: Optional[int] = None
    last_timestamp: Optional[float] = None
    last_sample_rate: Optional[float] = None
    last_num_samples: Optional[int] = None
    last_doppler_hz: Optional[float] = None
    last_delay_ms: Optional[float] = None
    last_fspl_db: Optional[float] = None
    total_samples_received: int
    average_snr_db: Optional[float] = None
    average_power_db: Optional[float] = None
    errors: int
    zmq_endpoint: str


# =============================================================================
# Security (NFR-SEC-001)
# =============================================================================

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User database initialization
# Security: Load admin credentials from environment variables
# Default demo credentials are used ONLY if environment variables are not set
ADMIN_USERNAME = os.environ.get("SDR_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("SDR_ADMIN_PASSWORD", "secret")
ADMIN_EMAIL = os.environ.get("SDR_ADMIN_EMAIL", "admin@example.com")

if ADMIN_PASSWORD == "secret":
    logging.warning(
        "Using default demo password. Set SDR_ADMIN_PASSWORD environment variable for production."
    )


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


fake_users_db = {
    ADMIN_USERNAME: {
        "username": ADMIN_USERNAME,
        "full_name": "SDR Administrator",
        "email": ADMIN_EMAIL,
        "hashed_password": get_password_hash(ADMIN_PASSWORD),
        "disabled": False,
    }
}


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="SDR Ground Station API",
    version="1.0.0",
    description="RESTful API for SDR platform control and O-RAN integration",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# LEO NTN ZMQ Integration (FR-INT-004)
# =============================================================================

async def zmq_iq_sample_receiver():
    """Background task to receive IQ samples from LEO NTN Simulator via ZMQ"""
    logger.info(f"🛰️  Starting ZMQ IQ sample receiver: {LEO_ZMQ_ENDPOINT}")

    context = zmq.asyncio.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages

    try:
        socket.connect(LEO_ZMQ_ENDPOINT)
        IQ_SAMPLE_STATS["connected"] = True
        logger.info(f"✅ Connected to LEO NTN Simulator at {LEO_ZMQ_ENDPOINT}")

        while True:
            try:
                # Receive multipart message: [metadata_json, iq_samples_bytes]
                metadata_json = await socket.recv_string()
                iq_samples_bytes = await socket.recv()

                # Parse metadata
                metadata = json.loads(metadata_json)

                # Convert IQ samples from bytes to numpy array
                iq_samples = np.frombuffer(iq_samples_bytes, dtype=np.complex64)

                # Update statistics
                IQ_SAMPLE_STATS["frames_received"] += 1
                IQ_SAMPLE_STATS["last_frame_id"] = metadata["frame_id"]
                IQ_SAMPLE_STATS["last_timestamp"] = metadata["timestamp"]
                IQ_SAMPLE_STATS["last_sample_rate"] = metadata["sample_rate"]
                IQ_SAMPLE_STATS["last_num_samples"] = metadata["num_samples"]
                IQ_SAMPLE_STATS["last_doppler_hz"] = metadata["doppler_hz"]
                IQ_SAMPLE_STATS["last_delay_ms"] = metadata["delay_ms"]
                IQ_SAMPLE_STATS["last_fspl_db"] = metadata["fspl_db"]
                IQ_SAMPLE_STATS["total_samples_received"] += len(iq_samples)

                # Calculate signal statistics
                power = np.mean(np.abs(iq_samples) ** 2)
                power_db = 10 * np.log10(power + 1e-12)  # Avoid log(0)
                IQ_SAMPLE_STATS["average_power_db"] = power_db

                # Store in buffer (for potential future use)
                IQ_SAMPLE_BUFFER.append({
                    "metadata": metadata,
                    "power_db": power_db,
                    "num_samples": len(iq_samples),
                })

                # Log every 100 frames
                if IQ_SAMPLE_STATS["frames_received"] % 100 == 0:
                    logger.info(
                        f"📊 Received {IQ_SAMPLE_STATS['frames_received']} frames | "
                        f"Power: {power_db:.2f} dB | "
                        f"Doppler: {metadata['doppler_hz']/1e3:.1f} kHz"
                    )

            except Exception as e:
                IQ_SAMPLE_STATS["errors"] += 1
                logger.error(f"❌ Error processing IQ sample: {e}")
                await asyncio.sleep(0.1)  # Brief pause on error

    except Exception as e:
        IQ_SAMPLE_STATS["connected"] = False
        logger.error(f"❌ Failed to connect to LEO NTN Simulator: {e}")
        logger.error(f"   Ensure {LEO_ZMQ_ENDPOINT} is accessible")
    finally:
        socket.close()
        context.term()


@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    logger.info("🚀 Starting SDR API Gateway Server")
    logger.info(f"🛰️  LEO NTN Endpoint: {LEO_ZMQ_ENDPOINT}")

    # Launch ZMQ receiver as background task
    asyncio.create_task(zmq_iq_sample_receiver())


# =============================================================================
# Authentication Endpoints
# =============================================================================

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2-compatible token login endpoint (NFR-SEC-001)

    Default credentials (demo only):
    - Username: admin
    - Password: secret
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# =============================================================================
# SDR Station Management Endpoints (FR-SDR-005)
# =============================================================================

@app.post("/api/v1/sdr/stations", status_code=status.HTTP_201_CREATED, tags=["Stations"])
async def create_station(
    config: StationConfig,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new SDR ground station configuration (FR-SDR-004)

    This endpoint:
    1. Validates configuration
    2. Reserves USRP device
    3. Initializes GNU Radio flowgraph (simulated)
    4. Optionally configures O-RAN data plane

    🟡 SIMULATED: Actual USRP initialization requires hardware
    """
    if config.station_id in STATIONS:
        raise HTTPException(status_code=400, detail="Station ID already exists")

    if config.usrp_device not in USRP_DEVICES:
        raise HTTPException(status_code=404, detail="USRP device not found")

    if USRP_DEVICES[config.usrp_device]["status"] != "online":
        raise HTTPException(status_code=503, detail="USRP device offline")

    # 🟡 SIMULATED: In production, this would:
    # - Initialize UHD (USRP Hardware Driver)
    # - Load GNU Radio flowgraph
    # - Configure antenna controller
    logger.info(f"Creating station {config.station_id} with USRP {config.usrp_device}")

    STATIONS[config.station_id] = {
        "config": config.dict(),
        "status": "stopped",
        "created_at": datetime.utcnow(),
        "created_by": current_user.username,
    }

    return {"message": "Station created successfully", "station_id": config.station_id}


@app.get("/api/v1/sdr/stations", response_model=List[str], tags=["Stations"])
async def list_stations(current_user: User = Depends(get_current_active_user)):
    """List all configured SDR stations"""
    return list(STATIONS.keys())


@app.get("/api/v1/sdr/stations/{station_id}/status", response_model=StationStatus, tags=["Stations"])
async def get_station_status(
    station_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get real-time status of an SDR station (FR-INT-003)

    Returns telemetry including:
    - Signal quality metrics (SNR, EbN0, PER)
    - USRP hardware status
    - Data throughput

    🟡 SIMULATED: Returns mock data. Production would query USRP and GNU Radio.
    """
    if station_id not in STATIONS:
        raise HTTPException(status_code=404, detail="Station not found")

    # 🟡 SIMULATED: Mock telemetry data
    import random
    status = StationStatus(
        station_id=station_id,
        status=STATIONS[station_id]["status"],
        usrp_connected=True,
        signal_snr_db=round(random.uniform(10.0, 25.0), 2),
        ebn0_db=round(random.uniform(8.0, 20.0), 2),
        packet_error_rate=round(random.uniform(0.0001, 0.01), 5),
        usrp_temperature_c=round(random.uniform(35.0, 55.0), 1),
        data_rate_mbps=round(random.uniform(50.0, 150.0), 2),
        last_updated=datetime.utcnow(),
    )

    return status


@app.put("/api/v1/sdr/stations/{station_id}/frequency", tags=["Stations"])
async def update_frequency(
    station_id: str,
    center_frequency_ghz: float = Body(..., ge=1.0, le=40.0, embed=True),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update center frequency for a station (FR-SDR-002)

    Dynamically retunes the USRP without restarting the station.

    🟡 SIMULATED: Production would call uhd::usrp::set_rx_freq()
    """
    if station_id not in STATIONS:
        raise HTTPException(status_code=404, detail="Station not found")

    logger.info(f"Updating {station_id} frequency to {center_frequency_ghz} GHz")

    # 🟡 SIMULATED: Would execute USRP frequency tuning
    STATIONS[station_id]["config"]["center_frequency_ghz"] = center_frequency_ghz

    return {"message": "Frequency updated", "new_frequency_ghz": center_frequency_ghz}


@app.post("/api/v1/sdr/stations/{station_id}/start", tags=["Stations"])
async def start_station(
    station_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Start SDR signal processing (FR-SDR-001, FR-SDR-002)

    Initiates:
    1. USRP streaming
    2. GNU Radio flowgraph execution
    3. O-RAN data plane (if enabled)

    🟡 SIMULATED: Production would start actual SDR processes
    """
    if station_id not in STATIONS:
        raise HTTPException(status_code=404, detail="Station not found")

    if STATIONS[station_id]["status"] == "running":
        raise HTTPException(status_code=400, detail="Station already running")

    logger.info(f"Starting station {station_id}")

    # 🟡 SIMULATED: Would execute:
    # - gnuradio_top_block.start()
    # - If O-RAN enabled: establish gRPC stream to O-DU

    STATIONS[station_id]["status"] = "running"
    STATIONS[station_id]["started_at"] = datetime.utcnow()

    return {"message": "Station started", "station_id": station_id}


@app.post("/api/v1/sdr/stations/{station_id}/stop", tags=["Stations"])
async def stop_station(
    station_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Stop SDR signal processing"""
    if station_id not in STATIONS:
        raise HTTPException(status_code=404, detail="Station not found")

    logger.info(f"Stopping station {station_id}")

    # 🟡 SIMULATED: Would execute gnuradio_top_block.stop()
    STATIONS[station_id]["status"] = "stopped"

    return {"message": "Station stopped"}


@app.delete("/api/v1/sdr/stations/{station_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Stations"])
async def delete_station(
    station_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete SDR station configuration"""
    if station_id not in STATIONS:
        raise HTTPException(status_code=404, detail="Station not found")

    if STATIONS[station_id]["status"] == "running":
        raise HTTPException(status_code=400, detail="Stop station before deleting")

    del STATIONS[station_id]
    logger.info(f"Deleted station {station_id}")


# =============================================================================
# Monitoring & Metrics Endpoints (NFR-INT-003)
# =============================================================================

@app.get("/api/v1/sdr/stations/{station_id}/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_station_metrics(
    station_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get Prometheus-compatible metrics (NFR-INT-003)

    Returns time-series metrics for monitoring and alerting.
    """
    if station_id not in STATIONS:
        raise HTTPException(status_code=404, detail="Station not found")

    # 🟡 SIMULATED: Mock metrics
    import random
    metrics = MetricsResponse(
        station_id=station_id,
        metrics={
            "sdr_signal_snr_db": round(random.uniform(10.0, 25.0), 2),
            "sdr_packet_error_rate": round(random.uniform(0.0001, 0.01), 5),
            "sdr_data_rate_mbps": round(random.uniform(50.0, 150.0), 2),
            "usrp_temperature_celsius": round(random.uniform(35.0, 55.0), 1),
        },
        timestamp=datetime.utcnow(),
    )

    return metrics


@app.get("/metrics", tags=["Monitoring"])
async def prometheus_metrics():
    """
    Prometheus scrape endpoint (NFR-INT-003)

    Returns metrics in Prometheus text format for monitoring.

    Example:
    ```
    # HELP sdr_signal_snr_db Signal-to-Noise Ratio in dB
    # TYPE sdr_signal_snr_db gauge
    sdr_signal_snr_db{station="station-001"} 18.5
    ```
    """
    # 🟡 SIMULATED: Would use prometheus_client library
    import random

    output = []
    output.append("# HELP sdr_signal_snr_db Signal-to-Noise Ratio in dB")
    output.append("# TYPE sdr_signal_snr_db gauge")

    for station_id in STATIONS.keys():
        snr = round(random.uniform(10.0, 25.0), 2)
        output.append(f'sdr_signal_snr_db{{station="{station_id}"}} {snr}')

    output.append("# HELP sdr_stations_total Total number of configured stations")
    output.append("# TYPE sdr_stations_total gauge")
    output.append(f"sdr_stations_total {len(STATIONS)}")

    return "\n".join(output)


# =============================================================================
# Health Check Endpoints (FR-SDR-004)
# =============================================================================

@app.get("/healthz", tags=["Health"])
async def health_check():
    """Kubernetes liveness probe"""
    return {"status": "healthy"}


@app.get("/readyz", tags=["Health"])
async def readiness_check():
    """Kubernetes readiness probe"""
    # 🟡 SIMULATED: Would check USRP connectivity, database, etc.
    usrp_online = sum(1 for dev in USRP_DEVICES.values() if dev["status"] == "online")

    if usrp_online == 0:
        raise HTTPException(status_code=503, detail="No USRP devices online")

    return {
        "status": "ready",
        "usrp_devices_online": usrp_online,
        "stations_configured": len(STATIONS),
    }


# =============================================================================
# USRP Device Management Endpoints
# =============================================================================

@app.get("/api/v1/usrp/devices", tags=["USRP"])
async def list_usrp_devices(current_user: User = Depends(get_current_active_user)):
    """List available USRP devices (FR-SDR-003)"""
    return USRP_DEVICES


# =============================================================================
# LEO NTN IQ Sample Endpoints (FR-INT-004)
# =============================================================================

@app.get("/api/v1/leo/iq-stats", response_model=IQSampleStats, tags=["LEO NTN"])
async def get_iq_sample_statistics():
    """Get real-time IQ sample statistics from LEO NTN Simulator (FR-INT-004)

    Returns live statistics about the IQ sample stream including:
    - Connection status
    - Frame and sample counts
    - Latest channel parameters (Doppler, delay, path loss)
    - Signal power measurements

    This endpoint does NOT require authentication to allow monitoring.
    """
    return IQSampleStats(
        **IQ_SAMPLE_STATS,
        zmq_endpoint=LEO_ZMQ_ENDPOINT
    )


@app.get("/api/v1/leo/iq-buffer", tags=["LEO NTN"])
async def get_iq_sample_buffer(limit: int = 10):
    """Get recent IQ sample metadata from buffer (FR-INT-004)

    Returns the last N frames of metadata (without actual IQ samples).
    Useful for debugging and monitoring the LEO channel conditions.

    Args:
        limit: Number of recent frames to return (default: 10, max: 100)

    This endpoint does NOT require authentication to allow monitoring.
    """
    limit = min(limit, 100)  # Cap at buffer size
    buffer_list = list(IQ_SAMPLE_BUFFER)
    return {
        "buffer_size": len(buffer_list),
        "recent_frames": buffer_list[-limit:] if buffer_list else []
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info("🚀 Starting SDR API Gateway Server")
    logger.info("📚 API Documentation: http://localhost:8000/api/v1/docs")
    logger.info("🔐 Default login: admin / secret")
    logger.info("🟡 SIMULATED MODE: USRP hardware interfaces are mocked")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
