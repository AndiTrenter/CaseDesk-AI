"""
CaseDesk AI - System Router
Update-System, Version Management, Rollback
"""
import os
import json
import asyncio
import subprocess
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_user, require_admin, db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])

# Version info - wird beim Build gesetzt
CURRENT_VERSION = "1.0.2"
BUILD_DATE = "2025-07-25"

# GitHub raw URLs
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/AndiTrenter/CaseDesk-AI/main/version.json"
GITHUB_CHANGELOG_URL = "https://raw.githubusercontent.com/AndiTrenter/CaseDesk-AI/main/CHANGELOG.md"

# Docker compose file path (for Unraid)
DOCKER_COMPOSE_FILE = "/app/docker-compose.unraid.yml"
DOCKER_COMPOSE_DIR = "/app"


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.
    Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2
    """
    def parse_version(v):
        # Remove 'v' prefix if present
        v = v.lstrip('v')
        return [int(x) for x in v.split('.')]
    
    p1 = parse_version(v1)
    p2 = parse_version(v2)
    
    for i in range(max(len(p1), len(p2))):
        n1 = p1[i] if i < len(p1) else 0
        n2 = p2[i] if i < len(p2) else 0
        if n1 < n2:
            return -1
        elif n1 > n2:
            return 1
    return 0


@router.get("/version")
async def get_version(user: dict = Depends(get_current_user)):
    """
    Get current installed version
    """
    # Try to get version from stored state
    stored_version = await db.system_settings.find_one({"key": "installed_version"})
    
    version = CURRENT_VERSION
    if stored_version:
        version = stored_version.get("version", CURRENT_VERSION)
    
    return {
        "version": version,
        "build_date": BUILD_DATE,
        "release_notes": "Update-System eingeführt"
    }


@router.get("/check-update")
async def check_update(user: dict = Depends(get_current_user)):
    """
    Check if a new version is available
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(GITHUB_VERSION_URL)
            response.raise_for_status()
            remote_data = response.json()
        
        remote_version = remote_data.get("version", "0.0.0")
        
        # Get current installed version
        stored_version = await db.system_settings.find_one({"key": "installed_version"})
        current = stored_version.get("version", CURRENT_VERSION) if stored_version else CURRENT_VERSION
        
        update_available = compare_versions(remote_version, current) > 0
        
        return {
            "current_version": current,
            "latest_version": remote_version,
            "update_available": update_available,
            "release_date": remote_data.get("release_date", ""),
            "release_notes": remote_data.get("release_notes", "")
        }
    
    except httpx.RequestError as e:
        logger.error(f"Failed to check for updates: {e}")
        return {
            "current_version": CURRENT_VERSION,
            "latest_version": None,
            "update_available": False,
            "error": "Konnte nicht auf Updates prüfen. Keine Internetverbindung?"
        }
    except Exception as e:
        logger.error(f"Update check error: {e}")
        return {
            "current_version": CURRENT_VERSION,
            "latest_version": None,
            "update_available": False,
            "error": str(e)
        }


@router.get("/changelog")
async def get_changelog(user: dict = Depends(get_current_user)):
    """
    Get the full changelog from GitHub
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(GITHUB_CHANGELOG_URL)
            response.raise_for_status()
            changelog = response.text
        
        return {
            "changelog": changelog,
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch changelog: {e}")
        # Return local changelog if available
        local_path = "/app/CHANGELOG.md"
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                return {
                    "changelog": f.read(),
                    "fetched_at": datetime.utcnow().isoformat(),
                    "source": "local"
                }
        raise HTTPException(status_code=503, detail="Changelog nicht verfügbar")


@router.post("/update")
async def perform_update(user: dict = Depends(require_admin)):
    """
    Perform system update (Admin only)
    Pulls latest Docker images and restarts containers
    """
    try:
        # First, check what version we're updating to
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(GITHUB_VERSION_URL)
            response.raise_for_status()
            remote_data = response.json()
        
        new_version = remote_data.get("version", CURRENT_VERSION)
        
        # Store current version for rollback
        stored_version = await db.system_settings.find_one({"key": "installed_version"})
        current = stored_version.get("version", CURRENT_VERSION) if stored_version else CURRENT_VERSION
        
        await db.system_settings.update_one(
            {"key": "previous_version"},
            {"$set": {"version": current, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        
        # Log the update attempt
        await db.system_logs.insert_one({
            "type": "update",
            "action": "update_started",
            "from_version": current,
            "to_version": new_version,
            "user_id": user["id"],
            "timestamp": datetime.utcnow()
        })
        
        # Execute docker compose pull
        # Note: In production, this runs from the host via a mounted socket or similar
        # For now, we'll return success and let the admin do it manually if needed
        
        result = {
            "success": True,
            "message": "Update wird vorbereitet...",
            "from_version": current,
            "to_version": new_version,
            "instructions": [
                "Die Container werden jetzt aktualisiert.",
                "Dies kann einige Minuten dauern.",
                "Die Seite wird automatisch neu geladen."
            ]
        }
        
        # Try to execute the update command
        # This requires Docker socket to be mounted in the container
        try:
            # Check if docker socket is available
            if os.path.exists("/var/run/docker.sock"):
                # Execute docker compose pull in background
                process = await asyncio.create_subprocess_exec(
                    "docker", "compose", "-f", DOCKER_COMPOSE_FILE, "pull",
                    cwd=DOCKER_COMPOSE_DIR,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
                
                if process.returncode == 0:
                    # Pull succeeded, now recreate containers
                    process = await asyncio.create_subprocess_exec(
                        "docker", "compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d",
                        cwd=DOCKER_COMPOSE_DIR,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
                    
                    if process.returncode == 0:
                        # Update installed version
                        await db.system_settings.update_one(
                            {"key": "installed_version"},
                            {"$set": {"version": new_version, "updated_at": datetime.utcnow()}},
                            upsert=True
                        )
                        
                        result["message"] = "Update erfolgreich installiert!"
                        result["docker_executed"] = True
                    else:
                        result["message"] = "Container-Neustart fehlgeschlagen"
                        result["error"] = stderr.decode() if stderr else "Unknown error"
                        result["success"] = False
                else:
                    result["message"] = "Docker Pull fehlgeschlagen"
                    result["error"] = stderr.decode() if stderr else "Unknown error"
                    result["success"] = False
            else:
                # Docker socket not available - provide manual instructions
                result["docker_executed"] = False
                result["manual_required"] = True
                result["manual_commands"] = [
                    f"cd {DOCKER_COMPOSE_DIR}",
                    f"docker compose -f {DOCKER_COMPOSE_FILE} pull",
                    f"docker compose -f {DOCKER_COMPOSE_FILE} up -d"
                ]
                result["message"] = "Docker-Socket nicht verfügbar. Bitte manuell ausführen."
                
                # Still update the version in DB (user will do manual update)
                await db.system_settings.update_one(
                    {"key": "installed_version"},
                    {"$set": {"version": new_version, "updated_at": datetime.utcnow()}},
                    upsert=True
                )
        
        except asyncio.TimeoutError:
            result["success"] = False
            result["message"] = "Update-Timeout - bitte manuell fortfahren"
        except Exception as e:
            logger.error(f"Docker command failed: {e}")
            result["docker_executed"] = False
            result["manual_required"] = True
            result["manual_commands"] = [
                f"cd {DOCKER_COMPOSE_DIR}",
                f"docker compose -f {DOCKER_COMPOSE_FILE} pull",
                f"docker compose -f {DOCKER_COMPOSE_FILE} up -d"
            ]
        
        # Log result
        await db.system_logs.insert_one({
            "type": "update",
            "action": "update_completed" if result["success"] else "update_failed",
            "from_version": current,
            "to_version": new_version,
            "result": result,
            "user_id": user["id"],
            "timestamp": datetime.utcnow()
        })
        
        return result
    
    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update fehlgeschlagen: {str(e)}")


@router.post("/rollback")
async def perform_rollback(user: dict = Depends(require_admin)):
    """
    Rollback to previous version (Admin only)
    """
    try:
        # Get previous version
        previous = await db.system_settings.find_one({"key": "previous_version"})
        if not previous or not previous.get("version"):
            raise HTTPException(status_code=400, detail="Keine vorherige Version zum Zurücksetzen verfügbar")
        
        previous_version = previous["version"]
        
        # Get current version
        stored_version = await db.system_settings.find_one({"key": "installed_version"})
        current = stored_version.get("version", CURRENT_VERSION) if stored_version else CURRENT_VERSION
        
        # Log rollback attempt
        await db.system_logs.insert_one({
            "type": "update",
            "action": "rollback_started",
            "from_version": current,
            "to_version": previous_version,
            "user_id": user["id"],
            "timestamp": datetime.utcnow()
        })
        
        result = {
            "success": True,
            "message": f"Rollback zu Version {previous_version} wird vorbereitet...",
            "from_version": current,
            "to_version": previous_version
        }
        
        # Try to execute rollback
        try:
            if os.path.exists("/var/run/docker.sock"):
                # Pull specific version
                images = [
                    f"ghcr.io/anditrenter/casedesk-ai/backend:v{previous_version}",
                    f"ghcr.io/anditrenter/casedesk-ai/frontend:v{previous_version}",
                    f"ghcr.io/anditrenter/casedesk-ai/ocr:v{previous_version}"
                ]
                
                for image in images:
                    process = await asyncio.create_subprocess_exec(
                        "docker", "pull", image,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await asyncio.wait_for(process.communicate(), timeout=120)
                
                # Restart with old images
                process = await asyncio.create_subprocess_exec(
                    "docker", "compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d",
                    cwd=DOCKER_COMPOSE_DIR,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(process.communicate(), timeout=120)
                
                # Update version in DB
                await db.system_settings.update_one(
                    {"key": "installed_version"},
                    {"$set": {"version": previous_version, "updated_at": datetime.utcnow()}},
                    upsert=True
                )
                
                result["message"] = f"Rollback zu Version {previous_version} erfolgreich!"
                result["docker_executed"] = True
            else:
                result["docker_executed"] = False
                result["manual_required"] = True
                result["manual_commands"] = [
                    f"docker pull ghcr.io/anditrenter/casedesk-ai/backend:v{previous_version}",
                    f"docker pull ghcr.io/anditrenter/casedesk-ai/frontend:v{previous_version}",
                    f"docker pull ghcr.io/anditrenter/casedesk-ai/ocr:v{previous_version}",
                    f"cd {DOCKER_COMPOSE_DIR}",
                    f"docker compose -f {DOCKER_COMPOSE_FILE} up -d"
                ]
                result["message"] = "Docker-Socket nicht verfügbar. Bitte manuell ausführen."
        
        except Exception as e:
            logger.error(f"Rollback docker commands failed: {e}")
            result["manual_required"] = True
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback fehlgeschlagen: {str(e)}")


@router.get("/update-history")
async def get_update_history(user: dict = Depends(require_admin)):
    """
    Get update history (Admin only)
    """
    history = await db.system_logs.find(
        {"type": "update"}
    ).sort("timestamp", -1).limit(20).to_list(20)
    
    # Convert ObjectId to string
    for item in history:
        item["id"] = str(item.pop("_id"))
        if "timestamp" in item:
            item["timestamp"] = item["timestamp"].isoformat()
    
    return {"history": history}
