from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.core import DBConfig

router = APIRouter()

@router.get("/servers")
def get_server_details():
    try:
        engine = DBConfig.get_engine()

        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM server_details"))
            rows = result.fetchall()

            # Convert result to list of dicts
            server_data = [dict(row._mapping) for row in rows]

        return server_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching server details: {str(e)}")
