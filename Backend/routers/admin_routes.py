from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database.connection import get_database


router = APIRouter(prefix="/api/admin", tags=["admin"])


class UpdateEmployeeNameRequest(BaseModel):
    old_employee_id: str
    new_employee_id: str


@router.post("/update-employee-name")
async def update_employee_name(request: UpdateEmployeeNameRequest):
    """
    Update employee_id across all messages in the database.
    
    This is an admin operation to rename an employee.
    """
    db = await get_database()
    
    # Check if old employee exists
    old_count = await db.messages.count_documents({"employee_id": request.old_employee_id})
    if old_count == 0:
        raise HTTPException(
            status_code=404, 
            detail=f"No messages found for employee_id: {request.old_employee_id}"
        )
    
    # Check if new employee_id already exists
    new_count = await db.messages.count_documents({"employee_id": request.new_employee_id})
    if new_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Employee_id '{request.new_employee_id}' already exists with {new_count} messages"
        )
    
    # Update all messages
    result = await db.messages.update_many(
        {"employee_id": request.old_employee_id},
        {"$set": {"employee_id": request.new_employee_id}}
    )
    
    return {
        "success": True,
        "old_employee_id": request.old_employee_id,
        "new_employee_id": request.new_employee_id,
        "messages_updated": result.modified_count,
        "message": f"Successfully updated {result.modified_count} messages"
    }


@router.get("/employees/list")
async def list_all_employees():
    """
    Get a list of all unique employee_ids in the database.
    """
    db = await get_database()
    
    # Get distinct employee IDs
    employee_ids = await db.messages.distinct("employee_id")
    
    # Get count for each employee
    employees = []
    for emp_id in employee_ids:
        count = await db.messages.count_documents({"employee_id": emp_id})
        employees.append({
            "employee_id": emp_id,
            "message_count": count
        })
    
    return {
        "total_employees": len(employees),
        "employees": sorted(employees, key=lambda x: x["message_count"], reverse=True)
    }

