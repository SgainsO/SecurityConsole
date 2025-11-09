import { EmployeeView } from "@/components/employee-view"

export default function EmployeePage() {
  // In production, you would get the employee ID from authentication/session
  const employeeId = "emp_demo_001"
  
  return <EmployeeView employeeId={employeeId} />
}

