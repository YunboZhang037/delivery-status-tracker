"""FastAPI application — shipment tracking endpoints."""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.database import get_db, engine, Base
from app.models import Shipment, StatusHistory
from app.schemas import ShipmentOut, StatusUpdateIn, ShipmentDetailOut, StatusHistoryOut
from app.state_machine import validate_transition, InvalidTransitionError

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Delivery Status Tracker", version="1.0.0")

# CORS — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/shipments", response_model=list[ShipmentOut])
def list_shipments(
    status: str | None = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """List all shipments, optionally filtered by status."""
    stmt = select(Shipment).order_by(Shipment.id)
    if status:
        stmt = stmt.where(Shipment.status == status)
    return db.execute(stmt).scalars().all()


@app.get("/api/shipments/{reference}", response_model=ShipmentDetailOut)
def get_shipment(reference: str, db: Session = Depends(get_db)):
    """Get a single shipment with its status history."""
    shipment = db.execute(
        select(Shipment).where(Shipment.reference == reference)
    ).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{reference}' not found")
    return shipment


@app.patch("/api/shipments/{reference}/status", response_model=ShipmentOut)
def update_status(
    reference: str,
    payload: StatusUpdateIn,
    db: Session = Depends(get_db),
):
    """Update a shipment's status.

    Validates the transition against the state machine:
    created -> picked_up -> in_transit -> delivered
    `failed` is allowed from any non-delivered status.
    """
    shipment = db.execute(
        select(Shipment).where(Shipment.reference == reference)
    ).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{reference}' not found")

    try:
        validate_transition(shipment.status, payload.status)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Record history
    history_entry = StatusHistory(
        shipment_id=shipment.id,
        previous_status=shipment.status,
        new_status=payload.status,
        note=payload.note,
    )
    shipment.status = payload.status
    db.add(history_entry)
    db.commit()
    db.refresh(shipment)
    return shipment


@app.get("/api/shipments/{reference}/history", response_model=list[StatusHistoryOut])
def get_status_history(reference: str, db: Session = Depends(get_db)):
    """Get the full status-change history for a shipment."""
    shipment = db.execute(
        select(Shipment).where(Shipment.reference == reference)
    ).scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{reference}' not found")
    return shipment.history


# ── Database Viewer ──────────────────────────────────────────────
@app.get("/db", response_class=HTMLResponse)
def db_viewer():
    """Visual database browser — view tables, structure, and data."""
    return _DB_VIEWER_HTML


@app.get("/api/db/tables")
def list_tables(db: Session = Depends(get_db)):
    """List all tables with row counts."""
    result = db.execute(text("""
        SELECT t.table_name,
               (SELECT count(*) FROM information_schema.columns c
                WHERE c.table_name = t.table_name AND c.table_schema = 'public') as col_count
        FROM information_schema.tables t
        WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name
    """))
    tables = []
    for row in result:
        tbl = row[0]
        count = db.execute(text(f'SELECT count(*) FROM "{tbl}"')).scalar()
        tables.append({"name": tbl, "columns": row[1], "rows": count})
    return tables


@app.get("/api/db/tables/{table}/structure")
def table_structure(table: str, db: Session = Depends(get_db)):
    """Get column definitions for a table."""
    result = db.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = :tbl AND table_schema = 'public'
        ORDER BY ordinal_position
    """), {"tbl": table})
    return [
        {"column": r[0], "type": r[1], "nullable": r[2], "default": r[3]}
        for r in result
    ]


@app.get("/api/db/tables/{table}/data")
def table_data(table: str, limit: int = 100, db: Session = Depends(get_db)):
    """Get all rows from a table."""
    allowed = {"shipments", "status_history"}
    if table not in allowed:
        raise HTTPException(status_code=400, detail="Invalid table name")
    result = db.execute(text(f'SELECT * FROM "{table}" ORDER BY 1 LIMIT :limit'), {"limit": limit})
    columns = list(result.keys())
    rows = [dict(zip(columns, row)) for row in result]
    return {"columns": columns, "rows": rows}


@app.post("/api/db/query")
def run_query(query: str, db: Session = Depends(get_db)):
    """Run a read-only SQL query (SELECT only)."""
    q = query.strip().lower()
    if not q.startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    # Prevent SQL injection via multi-statement attacks (e.g., "SELECT 1; DROP TABLE ...")
    if ";" in query.strip().rstrip(";"):
        raise HTTPException(status_code=400, detail="Multiple statements are not allowed")
    result = db.execute(text(query))
    columns = list(result.keys())
    rows = [dict(zip(columns, row)) for row in result]
    return {"columns": columns, "rows": rows}


_DB_VIEWER_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Delivery Tracker — Database Viewer</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; color: #1a1a2e; }
  .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
  .header h1 { font-size: 22px; font-weight: 700; }
  .header p { font-size: 13px; opacity: 0.85; margin-top: 4px; }
  .container { max-width: 1400px; margin: 20px auto; padding: 0 20px; }
  .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
  .tab { padding: 10px 20px; background: white; border: 1px solid #e0e0e0; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
  .tab:hover { background: #f5f5ff; }
  .tab.active { background: #667eea; color: white; border-color: #667eea; }
  .tab .badge { background: rgba(0,0,0,0.1); padding: 2px 8px; border-radius: 10px; font-size: 12px; }
  .tab.active .badge { background: rgba(255,255,255,0.3); }
  .panel { background: white; border-radius: 0 8px 8px 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden; }
  .section-title { font-size: 13px; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 20px; border-bottom: 1px solid #f0f0f0; }
  .structure-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .structure-table th { background: #fafafa; padding: 10px 16px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #eee; white-space: nowrap; }
  .structure-table td { padding: 10px 16px; border-bottom: 1px solid #f5f5f5; }
  .structure-table td:first-child { font-weight: 600; color: #333; }
  .type-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-family: 'SF Mono', Monaco, monospace; background: #e3f2fd; color: #1565c0; }
  .nullable-yes { color: #999; font-size: 12px; }
  .nullable-no { color: #e53935; font-size: 12px; font-weight: 600; }
  .default-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #e8f5e9; color: #2e7d32; font-weight: 600; }
  .default-val { font-family: 'SF Mono', Monaco, monospace; font-size: 12px; color: #666; background: #f5f5f5; padding: 1px 6px; border-radius: 3px; }
  .data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .data-table th { background: #667eea; color: white; padding: 10px 16px; text-align: left; font-weight: 600; white-space: nowrap; position: sticky; top: 0; }
  .data-table td { padding: 8px 16px; border-bottom: 1px solid #f0f0f0; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .data-table tr:hover { background: #f5f5ff; }
  .status-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
  .s-created { background: #e3f2fd; color: #1565c0; }
  .s-picked_up { background: #fff3e0; color: #e65100; }
  .s-in_transit { background: #f3e5f5; color: #7b1fa2; }
  .s-delivered { background: #e8f5e9; color: #2e7d32; }
  .s-failed { background: #ffebee; color: #c62828; }
  .query-box { padding: 20px; border-bottom: 1px solid #f0f0f0; background: #fafafa; }
  .query-box textarea { width: 100%; height: 60px; border: 1px solid #ddd; border-radius: 6px; padding: 10px; font-family: 'SF Mono', Monaco, monospace; font-size: 13px; resize: vertical; }
  .query-box button { margin-top: 8px; padding: 8px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; }
  .query-box button:hover { background: #5568d3; }
  .query-result { margin: 0 20px 20px; }
  .info-bar { display: flex; gap: 20px; padding: 10px 20px; background: #fafafa; border-bottom: 1px solid #f0f0f0; font-size: 13px; color: #666; }
  .info-bar span { font-weight: 600; color: #333; }
  .empty { text-align: center; padding: 40px; color: #999; font-size: 14px; }
  .loading { text-align: center; padding: 30px; color: #667eea; font-size: 14px; }
</style>
</head>
<body>
<div class="header">
  <h1>Delivery Tracker — Database Viewer</h1>
  <p>PostgreSQL 16.14 | delivery_tracker | localhost:5432</p>
</div>
<div class="container">
  <div class="tabs" id="tabs"></div>
  <div class="panel">
    <div class="info-bar" id="info-bar"></div>
    <div class="section-title">Table Structure</div>
    <div id="structure"><div class="loading">Loading...</div></div>
    <div class="section-title" style="border-top: 1px solid #f0f0f0; margin-top: 4px;">Data</div>
    <div id="data"><div class="loading">Loading...</div></div>
    <div class="section-title" style="border-top: 1px solid #f0f0f0;">SQL Query</div>
    <div class="query-box">
      <textarea id="sql-input" placeholder="SELECT * FROM shipments WHERE status = 'created';"></textarea>
      <button onclick="runQuery()">Run Query</button>
    </div>
    <div class="query-result" id="query-result"></div>
  </div>
</div>
<script>
const API = '';
let currentTable = null;

async function loadTables() {
  const res = await fetch(API + '/api/db/tables');
  const tables = await res.json();
  const tabsEl = document.getElementById('tabs');
  tabsEl.innerHTML = '';
  tables.forEach(t => {
    const tab = document.createElement('div');
    tab.className = 'tab';
    tab.innerHTML = t.name + ' <span class="badge">' + t.rows + ' rows</span>';
    tab.onclick = () => selectTable(t.name, tab);
    tabsEl.appendChild(tab);
  });
  if (tables.length > 0) {
    selectTable(tables[0].name, tabsEl.children[0]);
  }
}

async function selectTable(name, tabEl) {
  currentTable = name;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  tabEl.classList.add('active');
  document.getElementById('structure').innerHTML = '<div class="loading">Loading...</div>';
  document.getElementById('data').innerHTML = '<div class="loading">Loading...</div>';
  const [structRes, dataRes] = await Promise.all([
    fetch(API + '/api/db/tables/' + name + '/structure'),
    fetch(API + '/api/db/tables/' + name + '/data')
  ]);
  const struct = await structRes.json();
  const data = await dataRes.json();
  document.getElementById('info-bar').innerHTML =
    'Table: <span>' + name + '</span> | Columns: <span>' + struct.length + '</span> | Rows: <span>' + data.rows.length + '</span>';
  let structHTML = '<table class="structure-table"><tr><th>Column</th><th>Type</th><th>Nullable</th><th>Default</th></tr>';
  struct.forEach(c => {
    let def = c.default;
    let defHTML;
    if (!def) {
      defHTML = '—';
    } else if (def.indexOf('nextval') !== -1) {
      defHTML = '<span class="default-badge">auto-increment</span>';
    } else {
      defHTML = '<code class="default-val">' + def + '</code>';
    }
    structHTML += '<tr><td>' + c.column + '</td><td><span class="type-badge">' + c.type + '</span></td><td class="' + (c.nullable === 'YES' ? 'nullable-yes' : 'nullable-no') + '">' + (c.nullable === 'YES' ? 'NULL' : 'NOT NULL') + '</td><td>' + defHTML + '</td></tr>';
  });
  structHTML += '</table>';
  document.getElementById('structure').innerHTML = structHTML;
  if (data.rows.length === 0) {
    document.getElementById('data').innerHTML = '<div class="empty">No data in this table</div>';
    return;
  }
  let dataHTML = '<table class="data-table"><tr>';
  data.columns.forEach(c => dataHTML += '<th>' + c + '</th>');
  dataHTML += '</tr>';
  data.rows.forEach(row => {
    dataHTML += '<tr>';
    data.columns.forEach(c => {
      let val = row[c];
      if (val === null || val === undefined) { val = '<span style="color:#ccc">NULL</span>'; }
      else if (typeof val === 'object') { val = JSON.stringify(val); }
      else { val = String(val); }
      if (c === 'status' && typeof row[c] === 'string') {
        val = '<span class="status-badge s-' + row[c] + '">' + row[c] + '</span>';
      }
      dataHTML += '<td title="' + String(row[c] ?? '') + '">' + val + '</td>';
    });
    dataHTML += '</tr>';
  });
  dataHTML += '</table>';
  document.getElementById('data').innerHTML = dataHTML;
}

async function runQuery() {
  const sql = document.getElementById('sql-input').value.trim();
  if (!sql) return;
  const resultEl = document.getElementById('query-result');
  resultEl.innerHTML = '<div class="loading">Running query...</div>';
  try {
    const res = await fetch(API + '/api/db/query?query=' + encodeURIComponent(sql), { method: 'POST' });
    const data = await res.json();
    if (data.detail) { resultEl.innerHTML = '<div class="empty">' + data.detail + '</div>'; return; }
    if (data.rows.length === 0) { resultEl.innerHTML = '<div class="empty">No results</div>'; return; }
    let html = '<table class="data-table"><tr>';
    data.columns.forEach(c => html += '<th>' + c + '</th>');
    html += '</tr>';
    data.rows.forEach(row => {
      html += '<tr>';
      data.columns.forEach(c => {
        let val = row[c];
        if (val === null || val === undefined) val = '<span style="color:#ccc">NULL</span>';
        else if (typeof val === 'object') val = JSON.stringify(val);
        else val = String(val);
        html += '<td>' + val + '</td>';
      });
      html += '</tr>';
    });
    html += '</table>';
    resultEl.innerHTML = html;
  } catch (e) {
    resultEl.innerHTML = '<div class="empty">Error: ' + e.message + '</div>';
  }
}

loadTables();
</script>
</body>
</html>"""
