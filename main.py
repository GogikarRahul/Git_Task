from fastapi import FastAPI,Depends,HTTPException,status,Request
import models,schemas
from database import Base,get_db,engine
from sqlalchemy.orm import Session
import math


Base.metadata.create_all(bind=engine)



app=FastAPI()


@app.get("/")
def home():
    return "Application Running Succssefully"

@app.post("/calculate/", response_model=schemas.CalcResponse, status_code=status.HTTP_201_CREATED)
def calculate(data:schemas.CalcRequest, db: Session = Depends(get_db)):
    # 400 Bad Request
    if data.operation.strip() == "":
        raise HTTPException(status_code=400, detail="Operation name cannot be empty")

    # 415 Unsupported Media Type
    if not isinstance(data.operand1, (int, float)):
        raise HTTPException(status_code=415, detail="Operand1 must be a number")

    # 422 Unprocessable Entity (custom trigger)
    if data.operation not in ["add", "subtract", "multiply", "divide", "sqrt"]:
        raise HTTPException(status_code=422, detail="Unsupported operation type")

    # Perform calculation
    try:
        if data.operation == "add":
            result = data.operand1 + (data.operand2 or 0)
        elif data.operation == "subtract":
            result = data.operand1 - (data.operand2 or 0)
        elif data.operation == "multiply":
            result = data.operand1 * (data.operand2 or 1)
        elif data.operation == "divide":
            if data.operand2 == 0:
                raise HTTPException(status_code=400, detail="Division by zero is not allowed")
            result = data.operand1 / data.operand2
        elif data.operation == "sqrt":
            if data.operand1 < 0:
                raise HTTPException(status_code=400, detail="Cannot take square root of negative number")
            result = math.sqrt(data.operand1)
    except Exception as e:
        # 500 Internal Server Error
        raise HTTPException(status_code=500, detail=f"Internal calculation error: {str(e)}")

    # Check for duplicate (409 Conflict)
    existing = db.query(models.Calculation).filter(
       models. Calculation.operation == data.operation,
        models.Calculation.operand1 == data.operand1,
       models. Calculation.operand2 == data.operand2,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Duplicate calculation exists")

    # Save result
    new_calc = models.Calculation(
        operation=data.operation,
        operand1=data.operand1,
        operand2=data.operand2,
        result=result
    )
    db.add(new_calc)
    db.commit()
    db.refresh(new_calc)
    return new_calc


@app.get("/calculations/", response_model=list[schemas.CalcResponse])
def get_all_calculations(db: Session = Depends(get_db)):
    data = db.query(models.Calculation).all()
    if not data:
        # 404 Not Found
        raise HTTPException(status_code=404, detail="No calculations found")
    return data


@app.get("/calculations/{calc_id}", response_model=schemas.CalcResponse)
def get_calculation(calc_id: int, db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail=f"Calculation with ID {calc_id} not found")
    return calc


@app.delete("/calculations/{calc_id}")
def delete_calculation(calc_id: int, db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    db.delete(calc)
    db.commit()
    return {"message": "Calculation deleted successfully"}


# =============================================
# Fake Authentication (401 & 403 Example)
# =============================================

@app.get("/admin/")
def get_admin_data(token: str = None):
    if not token:
        # 401 Unauthorized
        raise HTTPException(status_code=401, detail="Missing authentication token")

    if token != "supersecret":
        # 403 Forbidden
        raise HTTPException(status_code=403, detail="Access denied: invalid admin token")

    return {"message": "Welcome, admin!"}


# =============================================
# Global Exception Handler Example
# =============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return {
        "error": "Unexpected server error",
        "details": str(exc)
    }