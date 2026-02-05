from datetime import datetime
from fastapi import FastAPI, Request, Response, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import subprocess
import psycopg2
import csv
import json
import requests
from starlette.middleware.sessions import SessionMiddleware
from psycopg2.extras import RealDictCursor
import urllib3
import traceback
import time

from backups.backup import create_backup
from db_init import init_db


app = FastAPI()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
@app.on_event("startup")
def startup():
    init_db()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key",
    same_site="none",
    https_only=True
)
BACKUP_DIR = "backups"
NETBOX_URL = os.getenv(
    "NETBOX_URL",
    "https://whih7783.cloud.netboxapp.com/api/"
)

NETBOX_API_TOKEN = os.getenv(
    "NETBOX_API_TOKEN",
    "tmlfSr1ShEPgpLJlUPG2qgcJvBUVsN6rxkbf06vT"
)

HEADERS = {
    "Authorization": f"Token {NETBOX_API_TOKEN}",
    "Accept": "application/json",
}
DEVICE_TYPE_MAP = {
    "router": "Router",
    "switch": "Switch",
    "servidor": "Servidor",
    "ordenador": "Ordenador",
}
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://telares-morros.vercel.app", "https://telares.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# === Conexión a la base de datos PostgreSQL ===
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "dpg-d5sj20fpm1nc73cds5j0-a"),
        dbname=os.getenv("DB_NAME", "telares_db"),
        user=os.getenv("DB_USER", "telares_db_user"),
        password=os.getenv("DB_PASSWORD", "r2850sFLGCVPhlTf9LwecNsn2K6kPnl0")
    )
def get_site_id(site_name="Principal"):
    r = requests.get(
        f"{NETBOX_URL}dcim/sites/",
        headers=HEADERS,
        params={"name": site_name},
        timeout=10,
        verify=True
    )
    r.raise_for_status()

    results = r.json().get("results", [])
    if not results:
        raise Exception(f"Site '{site_name}' no existe en NetBox")

    return results[0]["id"]
def get_role_id(role_name):
    r = requests.get(
        f"{NETBOX_URL}dcim/device-roles/",
        headers=HEADERS,
        params={"name": role_name.capitalize()},
        timeout=10,
        verify=False
    )
    r.raise_for_status()

    results = r.json().get("results", [])
    if not results:
        raise Exception(f"Device Role '{role_name}' no existe en NetBox")

    return results[0]["id"]
def get_device_type_id(model_name):
    r = requests.get(
        f"{NETBOX_URL}dcim/device-types/",
        headers=HEADERS,
        params={"model": model_name},
        timeout=10,
        verify=False
    )
    r.raise_for_status()

    results = r.json().get("results", [])
    if not results:
        raise Exception(f"Device Type '{model_name}' no existe en NetBox")

    return results[0]["id"]
def resolve_netbox_ids(rol):
    site_id = get_site_id("Principal")
    role_id = get_role_id(rol)

    model_name = DEVICE_TYPE_MAP.get(rol)
    if not model_name:
        raise Exception(f"Rol '{rol}' no soportado")

    device_type_id = get_device_type_id(model_name)

    return {
        "site_id": site_id,
        "role_id": role_id,
        "device_type_id": device_type_id
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal"""

    print("🧠 SESSION:", dict(request.session))

    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=302)

    backups = []
    if os.path.exists(BACKUP_DIR):
        for file in sorted(os.listdir(BACKUP_DIR)):
            if file.endswith(".sql"):
                path = os.path.join(BACKUP_DIR, file)
                size = round(os.path.getsize(path) / 1024, 2)
                date_str = file.replace("backup_", "").replace(".sql", "")
                backups.append({
                    "name": file,
                    "size": f"{size} KB",
                    "date": date_str
                })

    chart_data = {
        "labels": [b["date"] for b in backups],
        "sizes": [float(b["size"].replace(" KB", "")) for b in backups],
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "backups": backups,
            "chart_data": chart_data,
            "user": user,  # 👈 IMPORTANTE
        },
    )
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )
@app.get("/backup")
async def manual_backup():
    msg = create_backup()
    return JSONResponse({"status": "success" if "exitoso" in msg else "error", "message": msg})

@app.delete("/delete_backup/{filename}")
async def delete_backup(filename: str):
    filepath = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return JSONResponse({
                "status": "success",
                "message": f"Respaldo '{filename}' eliminado."
            })
        except Exception as e:
            return JSONResponse({
                "status": "error",
                "message": f"Error al eliminar: {e}"
            })
    else:
        return JSONResponse({
            "status": "error",
            "message": "Archivo no encontrado."
        })

@app.get("/download_backup/{filename}")
async def download_backup(filename: str):
    path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse(content={"status": "error", "message": "Archivo no encontrado"})
    return FileResponse(path, filename=filename)

def create_netbox_device(nombre, rol):
    site_id = get_site_id("Principal")
    role_id = get_role_id(rol)

    model_name = DEVICE_TYPE_MAP.get(rol)
    if not model_name:
        raise Exception(f"Rol no soportado: {rol}")

    device_type_id = get_device_type_id(model_name)

    payload = {
        "name": nombre,
        "site": site_id,
        "role": role_id,
        "device_type": device_type_id,
        "status": "active",
    }

    res = requests.post(
        f"{NETBOX_URL}dcim/devices/",
        headers=HEADERS,
        json=payload,
        timeout=10
    )

    if not res.ok:
        raise Exception(f"NetBox error: {res.text}")

    return res.json()["id"]


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

@app.post("/login")
async def login(request: Request):
    try:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        print("🔐 LOGIN ATTEMPT")
        print("   user:", username)
        print("   pass:", password)

        if username != "admin" or password != "admin2025":
            return JSONResponse(
                {"status": "error", "message": "Credenciales inválidas"},
                status_code=401
            )

        # ✅ guardar sesión
        request.session["user"] = username
        print("✅ SESIÓN GUARDADA:", dict(request.session))

        # 🔥 RESPUESTA EXPLÍCITA
        response = JSONResponse({"status": "success"})
        return response

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )
@app.get("/session")
def get_session(request: Request):
    user = request.session.get("user")

    if not user:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "username": user
    }
@app.post("/add_node")
async def add_node(request: Request):
    try:
        data = await request.json()

        nombre = data["nombre"]
        ip = data["ip"]
        ubicacion = data["ubicacion"]
        rol = data["rol"]

        netbox_id = create_netbox_device(nombre, rol)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO nodos (nombre, ip, ubicacion, rol, netbox_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (nombre, ip, ubicacion, rol, netbox_id))

        node_id = cur.fetchone()[0]
        crear_enlaces_por_ubicacion(conn, netbox_id, ubicacion)
        conn.commit()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "id": node_id,
            "netbox_id": netbox_id
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/network/traffic")
async def network_traffic():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM enlaces")
    enlaces = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM nodos")
    nodos = cur.fetchone()[0]

    cur.close()
    conn.close()

    traffic_mbps = round((enlaces * 35 + nodos * 12) * 0.8, 2)

    return {
        "traffic_mbps": traffic_mbps
    }
 
def link_exists(cur, a, b):
    cur.execute("""
        SELECT 1 FROM enlaces
        WHERE (origen=%s AND destino=%s)
           OR (origen=%s AND destino=%s)
    """, (a, b, b, a))
    return cur.fetchone() is not None


def create_link(cur, origen, destino):
    cur.execute("""
        INSERT INTO enlaces (origen, destino, tipo, ancho_banda)
        VALUES (%s, %s, %s, %s)
    """, (origen, destino, "LAN", "1 Gbps")) 
    
@app.post("/auto_create_links")
async def auto_create_links():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, ubicacion, rol
        FROM nodos
        WHERE ubicacion IS NOT NULL
    """)
    nodes = cur.fetchall()

    created = 0

    # Agrupar nodos por ubicación
    locations = {}
    for n in nodes:
        locations.setdefault(n["ubicacion"], []).append(n)

    for ubicacion, group in locations.items():
        routers = [n for n in group if n["rol"] == "router"]
        switches = [n for n in group if n["rol"] == "switch"]
        endpoints = [n for n in group if n["rol"] in ("pc", "ordenador", "servidor")]

        # 1️⃣ Router → Switch
        for router in routers:
            for switch in switches:
                if not link_exists(cur, router["id"], switch["id"]):
                    create_link(cur, router["id"], switch["id"])
                    created += 1

        # 2️⃣ Switch → Dispositivos finales
        for switch in switches:
            for end in endpoints:
                if not link_exists(cur, switch["id"], end["id"]):
                    create_link(cur, switch["id"], end["id"])
                    created += 1

    conn.commit()
    cur.close()
    conn.close()

    return {
        "status": "success",
        "created_links": created
    }
@app.delete("/delete_node/{node_id}")
async def delete_node(node_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT netbox_id FROM nodos WHERE id=%s", (node_id,))
    row = cur.fetchone()

    if row and row[0]:
        netbox_id = row[0]

        # 🔥 Eliminar en NetBox
        nb_res = requests.delete(
            f"{NETBOX_URL}dcim/devices/{netbox_id}/",
            headers=HEADERS,
            timeout=10
        )

        if not nb_res.ok:
            return {"status": "error", "message": f"NetBox error: {nb_res.text}"}

    # 🔹 Eliminar enlaces y nodo local
    cur.execute("DELETE FROM enlaces WHERE origen=%s OR destino=%s", (node_id, node_id))
    cur.execute("DELETE FROM nodos WHERE id=%s", (node_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "success"}


@app.get("/get_nodes")
async def get_nodes():
    """Devuelve todos los nodos"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, ip, ubicacion, rol FROM nodos;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        nodes = [
            {"id": r[0], "nombre": r[1], "ip": r[2], "ubicacion": r[3], "rol": r[4]}
            for r in rows
        ]
        return {"status": "success", "nodes": nodes}
    except Exception as e:
        return {"status": "error", "message": f"Error al obtener nodos: {str(e)}"}
def crear_enlaces_por_ubicacion(conn, netbox_id, ubicacion):
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM nodos
        WHERE ubicacion = %s AND netbox_id != %s
    """, (ubicacion, netbox_id))
    otros_nodos = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT id FROM nodos WHERE netbox_id = %s", (netbox_id,))
    nodo_actual = cur.fetchone()[0]

    # Crear enlaces con cada nodo existente
    for nodo_destino in otros_nodos:
        cur.execute("""
            INSERT INTO enlaces (origen, destino, tipo, ancho_banda)
            VALUES (%s, %s, %s, %s)
        """, (nodo_actual, nodo_destino, "Ethernet", "100Mb/s"))

    cur.close()
# === Agregar enlace ===
@app.post("/add_link")
async def add_link(
    origen: int = Form(...),
    destino: int = Form(...),
    tipo: str = Form(...),
    ancho_banda: str = Form(None)
):
    """Agrega un nuevo enlace entre nodos existentes."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """
        INSERT INTO enlaces (origen, destino, tipo, ancho_banda)
        VALUES (%s, %s, %s, %s)
        """
        cur.execute(query, (origen, destino, tipo, ancho_banda))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "message": "Enlace agregado correctamente."}
    except Exception as e:
        return {"status": "error", "message": f"Error al agregar enlace: {str(e)}"}
@app.get("/netbox_api/get_netvis_data")
async def get_netvis_data():
    conn = get_connection()
    cur = conn.cursor()

    # Nodos
    cur.execute("""
        SELECT id, nombre, rol
        FROM nodos
    """)
    nodes_db = cur.fetchall()

    nodes = [{
        "id": n[0],
        "label": n[1],
        "nombre": n[1],
        "rol": n[2]
    } for n in nodes_db]

    # 🔗 Enlaces
    cur.execute("""
        SELECT id, origen, destino, tipo, ancho_banda
        FROM enlaces
    """)
    edges_db = cur.fetchall()

    edges = [{
        "id": e[0],
        "from": e[1],
        "to": e[2],
        "label": e[3] or "",
        "title": f"{e[3]} {e[4] or ''}".strip()
    } for e in edges_db]

    cur.close()
    conn.close()

    return {
        "status": "success",
        "nodes": nodes,
        "edges": edges
    }
# === Obtener red completa (nodos + posiciones) ===
@app.get("/get_network")
async def get_network():
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 🔹 NODOS
        cur.execute("""
            SELECT id, nombre, ip, ubicacion, rol, pos_x, pos_y
            FROM nodos
        """)
        nodos = cur.fetchall()

        # 🔹 ENLACES
        cur.execute("""
            SELECT id, origen, destino, tipo, ancho_banda
            FROM enlaces
        """)
        enlaces = cur.fetchall()

        cur.close()
        conn.close()

        nodes = []
        for n in nodos:
            node = {
                "id": n[0],
                "label": n[1],
                "title": f"{n[1]}<br>IP: {n[2]}<br>Ubicación: {n[3]}",
                "rol": n[4],
                "shape": "icon",
                "icon": {
                    "face": "FontAwesome",
                    "code": (
                        "\uf233" if n[4] == "router" else
                        "\uf6ff" if n[4] == "switch" else
                        "\uf0c2" if n[4] == "firewall" else
                        "\uf1eb" if n[4] == "ap" else
                        "\uf233"
                    ),
                    "size": 40
                }
            }

            # 📍 SOLO fijar si tiene coordenadas reales
            if n[5] not in (None, 0) and n[6] not in (None, 0):
                node.update({
                    "x": float(n[5]),
                    "y": float(n[6]),
                    "fixed": True
                })

            nodes.append(node)

        edges = []
        for e in enlaces:
            edges.append({
                "id": e[0],
                "from": e[1],
                "to": e[2],
                "label": e[4] or e[3],
                "arrows": "to",
                "smooth": True,
                "width": 2
            })

        return {
            "status": "success",
            "nodes": nodes,
            "edges": edges
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al obtener red: {str(e)}",
            "nodes": [],
            "edges": []
        }

# === Actualizar posición del nodo ===
@app.post("/update_position/{node_id}")
async def update_position(node_id: int, request: Request):
    """Actualiza la posición X,Y de un nodo cuando se mueve en el mapa."""
    try:
        body = await request.json()
        pos_x = body.get("pos_x")
        pos_y = body.get("pos_y")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE nodos SET pos_x = %s, pos_y = %s WHERE id = %s", (pos_x, pos_y, node_id))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "message": "Posición actualizada"}
    except Exception as e:
        return {"status": "error", "message": f"Error al actualizar posición: {str(e)}"}

# === Estadísticas de nodos ===
@app.get("/get_device_stats")
async def get_device_stats():
    """Devuelve la cantidad de nodos agrupados por tipo (rol)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT rol, COUNT(*) FROM nodos GROUP BY rol;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        data = [{"rol": r[0], "cantidad": r[1]} for r in rows]
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": f"Error al obtener estadísticas: {str(e)}"}

# === Actualizar nodos desde la tabla ===
@app.put("/update_node/{node_id}")
async def update_node(node_id: int, request: Request):
    data = await request.json()
    nombre = data.get("nombre")
    rol = data.get("rol")

    conn = get_connection()
    cur = conn.cursor()

    # 🔹 Obtener netbox_id
    cur.execute("SELECT netbox_id FROM nodos WHERE id=%s", (node_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        return {"status": "error", "message": "Nodo no sincronizado con NetBox"}

    netbox_id = row[0]

    # 🔹 Resolver role_id REAL desde NetBox
    try:
        role_id = get_role_id(rol)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # 🔹 Actualizar en NetBox
    payload = {
        "name": nombre,
        "role": role_id,
    }

    nb_res = requests.patch(
        f"{NETBOX_URL}dcim/devices/{netbox_id}/",
        headers=HEADERS,
        json=payload,
        timeout=10
    )

    if not nb_res.ok:
        return {
            "status": "error",
            "message": f"NetBox error: {nb_res.text}"
        }

    # 🔹 Actualizar en DB local
    cur.execute(
        "UPDATE nodos SET nombre=%s, rol=%s WHERE id=%s",
        (nombre, rol, node_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "success"}
@app.get("/list_backups")
async def list_backups():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    files = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):  # los más recientes primero
        if f.endswith(".sql"):
            path = os.path.join(BACKUP_DIR, f)
            size = round(os.path.getsize(path) / 1024, 2)  # KB
            date = os.path.getmtime(path)
            files.append({
                "name": f,
                "size": f"{size} KB",
                "date": datetime.fromtimestamp(date).strftime("%Y-%m-%d %H:%M:%S")
            })

    return JSONResponse(content={"status": "success", "files": files})
@app.get("/netbox_api/get_netvis_data")
async def get_netvis_data():
    """
    Devuelve nodos y enlaces desde NetBox en formato compatible con NetVis.
    """
    try:
        # 🔹 Obtener dispositivos (devices)
        devices_res = requests.get(
            f"{NETBOX_URL}dcim/devices/?limit=1000",
            headers=HEADERS
        )
        devices_res.raise_for_status()
        devices = devices_res.json().get("results", [])

        nodes = []
        for d in devices:
            # Obtener modelo o asignar 'desconocido'
            rol = (d.get("device_type", {}).get("model") or "desconocido").lower()
            device_name = d.get("name") or f"Dispositivo {d.get('id')}"
            
            nodes.append({
                "id": d.get("id"),
                "label": device_name,
                "rol": rol,  # ⚡ Importante: frontend espera 'rol', no 'role'
                "title": f"{device_name} ({rol})",
                "x": 0,  # posición inicial
                "y": 0,
                "fixed": False  # vis.js ajustará automáticamente si no se mueve
            })

        # 🔹 Obtener cables (links)
        cables_res = requests.get(
            f"{NETBOX_URL}dcim/cables/?limit=1000",
            headers=HEADERS
        )
        cables_res.raise_for_status()
        cables = cables_res.json().get("results", [])

        edges = []
        for c in cables:
            device_a = c.get("termination_a_device")
            device_b = c.get("termination_b_device")
            if device_a and device_b and device_a.get("id") and device_b.get("id"):
                edges.append({
                    "from": device_a["id"],
                    "to": device_b["id"],
                    "arrows": "to",
                    "smooth": True,
                    "label": c.get("label") or str(c.get("id"))  # opcional: mostrar id o label
                })

        return JSONResponse({"status": "success", "nodes": nodes, "edges": edges})

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e),
            "nodes": [],
            "edges": []
        })
@app.get("/netbox_test")
def netbox_test():
    r = requests.get(
        f"{NETBOX_URL}dcim/devices/",
        headers=HEADERS,
        timeout=10
    )
    return {
        "status_code": r.status_code,
        "ok": r.ok,
        "data": r.json() if r.ok else r.text
    }        