from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from database.connection import get_database
from models.message import MessageStatus


router = APIRouter(prefix="/api/employees", tags=["employees"])


class EmployeeStatistics(BaseModel):
    employee_id: str
    total_messages: int
    safe_messages: int
    flagged_messages: int
    blocked_messages: int
    conversations_count: int
    risk_score: float
    last_activity: str


@router.get("/", response_model=List[EmployeeStatistics])
async def get_all_employees(
    min_risk: Optional[int] = Query(None, ge=0, le=100),
    sort_by: Optional[str] = Query("risk", regex="^(risk|flags|blocks|total)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all employees with their aggregated statistics.
    
    Query Parameters:
    - min_risk: Filter employees by minimum risk score (0-100)
    - sort_by: Sort by 'risk', 'flags', 'blocks', or 'total' (default: 'risk')
    - skip: Pagination offset
    - limit: Max results to return
    """
    db = await get_database()
    
    # Aggregation pipeline to get employee statistics
    pipeline = [
        {
            "$group": {
                "_id": "$employee_id",
                "total_messages": {"$sum": 1},
                "safe_messages": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.SAFE.value]}, 1, 0]}
                },
                "flagged_messages": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.FLAG.value]}, 1, 0]}
                },
                "blocked_messages": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.BLOCKED.value]}, 1, 0]}
                },
                "unique_sessions": {"$addToSet": "$session_id"},
                "last_activity": {"$max": "$created_at"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "employee_id": "$_id",
                "total_messages": 1,
                "safe_messages": 1,
                "flagged_messages": 1,
                "blocked_messages": 1,
                "conversations_count": {"$size": "$unique_sessions"},
                "last_activity": 1,
                # Calculate risk score: (flagged * 2 + blocked * 5)
                "risk_score": {
                    "$min": [
                        100,
                        {
                            "$add": [
                                {"$multiply": ["$flagged_messages", 2]},
                                {"$multiply": ["$blocked_messages", 5]}
                            ]
                        }
                    ]
                }
            }
        }
    ]
    
    # Determine sort field
    sort_field_map = {
        "risk": "risk_score",
        "flags": "flagged_messages",
        "blocks": "blocked_messages",
        "total": "total_messages"
    }
    sort_field = sort_field_map.get(sort_by or "risk", "risk_score")
    
    pipeline.append({"$sort": {sort_field: -1, "employee_id": 1}})
    
    cursor = db.messages.aggregate(pipeline)
    employees = []
    
    async for emp in cursor:
        # Apply risk filter if specified
        if min_risk is not None and emp["risk_score"] < min_risk:
            continue
            
        employees.append(EmployeeStatistics(
            employee_id=emp["employee_id"],
            total_messages=emp["total_messages"],
            safe_messages=emp["safe_messages"],
            flagged_messages=emp["flagged_messages"],
            blocked_messages=emp["blocked_messages"],
            conversations_count=emp["conversations_count"],
            risk_score=float(emp["risk_score"]),
            last_activity=emp["last_activity"].isoformat()
        ))
    
    # Apply pagination after filtering
    start = skip
    end = skip + limit
    return employees[start:end]


@router.get("/summary/risk-levels")
async def get_employee_risk_summary():
    """
    Get summary of employees by risk level.
    
    Returns:
        Dictionary with total employees and counts by risk level (high/medium/low)
    """
    db = await get_database()
    
    pipeline = [
        {
            "$group": {
                "_id": "$employee_id",
                "flagged_messages": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.FLAG.value]}, 1, 0]}
                },
                "blocked_messages": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.BLOCKED.value]}, 1, 0]}
                }
            }
        },
        {
            "$project": {
                "risk_score": {
                    "$min": [
                        100,
                        {
                            "$add": [
                                {"$multiply": ["$flagged_messages", 2]},
                                {"$multiply": ["$blocked_messages", 5]}
                            ]
                        }
                    ]
                }
            }
        }
    ]
    
    cursor = db.messages.aggregate(pipeline)
    
    risk_levels = {
        "high": 0,  # >= 20
        "medium": 0,  # >= 10 and < 20
        "low": 0  # < 10
    }
    
    async for emp in cursor:
        risk_score = emp["risk_score"]
        if risk_score >= 20:
            risk_levels["high"] += 1
        elif risk_score >= 10:
            risk_levels["medium"] += 1
        else:
            risk_levels["low"] += 1
    
    return {
        "total_employees": sum(risk_levels.values()),
        "high_risk": risk_levels["high"],
        "medium_risk": risk_levels["medium"],
        "low_risk": risk_levels["low"]
    }


@router.get("/{employee_id}", response_model=EmployeeStatistics)
async def get_employee_detail(employee_id: str):
    """
    Get detailed statistics for a specific employee.
    
    Args:
        employee_id: The employee ID to retrieve
        
    Returns:
        EmployeeStatistics object with all aggregated data
    """
    db = await get_database()
    
    pipeline = [
        {"$match": {"employee_id": employee_id}},
        {
            "$group": {
                "_id": "$employee_id",
                "total_messages": {"$sum": 1},
                "safe_messages": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.SAFE.value]}, 1, 0]}
                },
                "flagged_messages": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.FLAG.value]}, 1, 0]}
                },
                "blocked_messages": {
                    "$sum": {"$cond": [{"$eq": ["$status", MessageStatus.BLOCKED.value]}, 1, 0]}
                },
                "unique_sessions": {"$addToSet": "$session_id"},
                "last_activity": {"$max": "$created_at"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "employee_id": "$_id",
                "total_messages": 1,
                "safe_messages": 1,
                "flagged_messages": 1,
                "blocked_messages": 1,
                "conversations_count": {"$size": "$unique_sessions"},
                "last_activity": 1,
                "risk_score": {
                    "$min": [
                        100,
                        {
                            "$add": [
                                {"$multiply": ["$flagged_messages", 2]},
                                {"$multiply": ["$blocked_messages", 5]}
                            ]
                        }
                    ]
                }
            }
        }
    ]
    
    cursor = db.messages.aggregate(pipeline)
    employee = await cursor.to_list(length=1)
    
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    
    emp = employee[0]
    return EmployeeStatistics(
        employee_id=emp["employee_id"],
        total_messages=emp["total_messages"],
        safe_messages=emp["safe_messages"],
        flagged_messages=emp["flagged_messages"],
        blocked_messages=emp["blocked_messages"],
        conversations_count=emp["conversations_count"],
        risk_score=float(emp["risk_score"]),
        last_activity=emp["last_activity"].isoformat()
    )

