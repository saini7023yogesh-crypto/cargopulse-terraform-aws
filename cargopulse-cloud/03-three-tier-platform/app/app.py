"""CargoPulse API: a small Flask service backed by PostgreSQL (RDS)."""
import os
import uuid

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)
VERSION = os.environ.get("APP_VERSION", "dev")


def get_conn():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def ensure_schema():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS shipments (
                   id TEXT PRIMARY KEY,
                   origin TEXT NOT NULL,
                   destination TEXT NOT NULL,
                   status TEXT NOT NULL DEFAULT 'CREATED',
                   created_at TIMESTAMPTZ NOT NULL DEFAULT now()
               )"""
        )


@app.get("/")
def index():
    return jsonify(service="CargoPulse API", version=VERSION)


@app.get("/health")
def health():
    # Liveness only: must NOT touch the database, otherwise a DB blip
    # makes the ALB kill every healthy container.
    return jsonify(status="ok")


@app.get("/ready")
def ready():
    # Readiness: verifies the DB connection too.
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify(status="ready")
    except Exception as exc:  # noqa: BLE001
        return jsonify(status="db_unavailable", error=str(exc)), 503


@app.get("/shipments")
def list_shipments():
    ensure_schema()
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM shipments ORDER BY created_at DESC LIMIT 50")
        return jsonify(cur.fetchall())


@app.post("/shipments")
def create_shipment():
    data = request.get_json(silent=True) or {}
    if not data.get("origin") or not data.get("destination"):
        return jsonify(error="origin and destination are required"), 400
    ensure_schema()
    shipment_id = "CP-" + uuid.uuid4().hex[:8].upper()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO shipments (id, origin, destination) VALUES (%s, %s, %s)",
            (shipment_id, data["origin"], data["destination"]),
        )
    return jsonify(id=shipment_id, status="CREATED"), 201
