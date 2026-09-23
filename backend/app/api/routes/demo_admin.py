import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import DemoSeedManifest
from app.services.demo_seed import CREATED_COUNTS, DATASET_ID, VERSION, current_counts, seed_dataset

DATASET_KEY = DATASET_ID
router = APIRouter(prefix="/admin/demo", tags=["private-demo-admin"], include_in_schema=False)


def _secured(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"


def _check_token(request: Request, x_demo_admin_token: str | None = Header(default=None, alias="X-Demo-Admin-Token")):
    token = request.app.state.demo_admin_token
    if not x_demo_admin_token or not token or not hmac.compare_digest(
        x_demo_admin_token.encode("utf-8"), token.encode("utf-8")
    ):
        raise HTTPException(status_code=403, detail="Invalid demo admin token")


_PAGE = r'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Локальная демо-панель</title><style>body{font:16px system-ui;max-width:720px;margin:3rem auto;padding:0 1rem;color:#18212b}label,input,button{display:block;margin:.7rem 0}input{padding:.6rem;width:min(100%,30rem)}button{padding:.65rem 1rem;cursor:pointer}pre{white-space:pre-wrap;background:#f2f4f7;padding:1rem}.warning{border-left:4px solid #c60;padding:.7rem}</style><h1>Локальная демо-панель</h1><p class="warning">Local demo tool: только для локального доверенного демо. Это не production-аутентификация.</p><label>Demo admin token <input id="token" type="password" autocomplete="off"></label><button id="status">Проверить состояние</button><button id="seed">Создать демо-данные</button><pre id="output" aria-live="polite"></pre><script>(()=>{const input=document.querySelector('#token'),out=document.querySelector('#output'),buttons=[...document.querySelectorAll('button')];const base=location.pathname.replace(/\/+$/,'');async function call(path,method='GET'){buttons.forEach(b=>b.disabled=true);out.textContent='Запрос выполняется…';try{const r=await fetch(base+path,{method,headers:{'X-Demo-Admin-Token':input.value}});const t=await r.text();out.textContent=`HTTP ${r.status}\n`+t;}catch(e){out.textContent='Ошибка запроса: '+String(e)}finally{buttons.forEach(b=>b.disabled=false)}}document.querySelector('#status').onclick=()=>call('/status');document.querySelector('#seed').onclick=()=>call('/seed','POST')})()</script></html>'''
