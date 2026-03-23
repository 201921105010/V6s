from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from crud.inventory import (
    INVENTORY_COLS,
    get_data,
    get_warehouse_layout,
    inbound_to_slot,
    reset_warehouse_layout,
    save_data,
    save_warehouse_layout,
)

router = APIRouter()


class LayoutPayload(BaseModel):
    layout_id: str = "default"
    layout_json: Dict[str, Any]


class LayoutResetPayload(BaseModel):
    layout_id: str = "default"


class InboundSlotPayload(BaseModel):
    serial_no: str
    slot_code: str

@router.get("/")
def get_inventory():
    """Get all inventory data."""
    try:
        df = get_data()
        # Convert NaN/NaT to None for JSON serialization
        df = df.where(df.notnull(), None)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
def update_inventory(data: List[Dict[str, Any]]):
    """
    Replace all inventory data with the provided list of dicts.
    Note: In actual production, you might want to use specific update/add endpoints instead of full replace.
    """
    import pandas as pd
    try:
        if data:
            missing_sn = [idx for idx, item in enumerate(data) if not str(item.get("流水号", "")).strip()]
            if missing_sn:
                raise HTTPException(status_code=422, detail=f"第 {missing_sn[:10]} 条记录缺少必填字段: 流水号")
        df = pd.DataFrame(data)
        unknown_cols = [c for c in df.columns if c not in INVENTORY_COLS]
        if unknown_cols:
            raise HTTPException(status_code=422, detail=f"存在不支持字段: {unknown_cols}")
        save_data(df)
        return {"message": "Inventory updated successfully"}
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layout/{layout_id}")
def get_layout(layout_id: str):
    try:
        return get_warehouse_layout(layout_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/layout/save")
def save_layout(payload: LayoutPayload):
    try:
        return save_warehouse_layout(payload.layout_id, payload.layout_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/layout/reset")
def reset_layout(payload: LayoutResetPayload):
    try:
        return reset_warehouse_layout(payload.layout_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inbound-to-slot")
def inbound_machine_to_slot(payload: InboundSlotPayload):
    try:
        result = inbound_to_slot(payload.serial_no, payload.slot_code)
        if not result.get("ok"):
            raise HTTPException(status_code=422, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
