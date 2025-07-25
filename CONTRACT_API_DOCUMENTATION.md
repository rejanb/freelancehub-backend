# Contract Management API Documentation

## Overview

Complete contract management system with PDF generation, milestone tracking, digital signing, and comprehensive analytics.

## Base URL

```
/api/contracts/
```

## Authentication

All endpoints require JWT authentication via Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Contract Model Structure

```python
{
    "id": 1,
    "project_proposal": {
        "id": 1,
        "project": {
            "id": 1,
            "title": "Website Development",
            "client": {...}
        },
        "freelancer": {...}
    },
    "client": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
    },
    "freelancer": {
        "id": 2,
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@example.com"
    },
    "total_payment": "5000.00",
    "start_date": "2024-01-15",
    "end_date": "2024-03-15",
    "status": "active",
    "deliverables": "Complete website with responsive design",
    "milestones": "[{...}]",
    "signed_by_client": true,
    "signed_by_freelancer": true,
    "client_signed_at": "2024-01-15T10:30:00Z",
    "freelancer_signed_at": "2024-01-15T11:00:00Z",
    "created_at": "2024-01-15T09:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
}
```

## Core CRUD Operations

### 1. List Contracts

```http
GET /api/contracts/
```

**Response:**

```json
{
    "count": 25,
    "next": "http://localhost:8000/api/contracts/?page=2",
    "previous": null,
    "results": [...]
}
```

**Query Parameters:**

- `status`: Filter by status (draft, active, completed, cancelled, terminated)
- `search`: Search in project title, client name, freelancer name
- `ordering`: Sort by fields (-created_at, total_payment, etc.)
- `page`: Pagination

### 2. Retrieve Contract Details

```http
GET /api/contracts/{id}/
```

**Response:** Full contract details with calculated fields:

```json
{
    "id": 1,
    "project_info": {
        "id": 1,
        "title": "Website Development",
        "description": "...",
        "budget": "5000.00"
    },
    "payment_info": {
        "total_payment": "5000.00",
        "paid_amount": "2500.00",
        "remaining_amount": "2500.00",
        "payment_percentage": 50.0
    },
    "timeline_info": {
        "duration_days": 60,
        "days_remaining": 30,
        "progress_percentage": 50.0,
        "is_overdue": false
    },
    "milestones": [...],
    "documents": [...],
    ...
}
```

### 3. Create Contract

```http
POST /api/contracts/
```

**Request Body:**

```json
{
  "project_proposal": 1,
  "total_payment": "5000.00",
  "start_date": "2024-01-15",
  "end_date": "2024-03-15",
  "deliverables": "Complete website with responsive design",
  "milestones": "[{\"title\": \"Design Phase\", \"amount\": 1500, \"due_date\": \"2024-02-01\"}]"
}
```

### 4. Update Contract

```http
PUT /api/contracts/{id}/
PATCH /api/contracts/{id}/
```

### 5. Delete Contract

```http
DELETE /api/contracts/{id}/
```

## Contract Actions

### 1. Sign Contract

```http
POST /api/contracts/{id}/sign_contract/
```

**Description:** Digitally sign contract (client or freelancer)

**Response:**

```json
{
    "message": "Contract signed successfully by John Doe",
    "contract": {...},
    "fully_signed": true
}
```

**Behavior:**

- Automatically activates contract when both parties sign
- Sends notifications to both parties
- Updates signing timestamps

### 2. Download PDF

```http
GET /api/contracts/{id}/download_pdf/
```

**Description:** Generate and download contract as PDF

**Response:** PDF file download

**Features:**

- Professional PDF layout with company branding
- Contract details, parties, financial terms
- Milestones and deliverables
- Signature status and dates
- Fallback to text format if reportlab unavailable

### 3. Add Milestone

```http
POST /api/contracts/{id}/add_milestone/
```

**Request Body:**

```json
{
  "milestone": {
    "title": "Design Phase Complete",
    "description": "All design mockups approved",
    "amount": 1500.0,
    "due_date": "2024-02-01"
  }
}
```

**Response:**

```json
{
  "message": "Milestone added successfully",
  "milestone": {
    "id": 1,
    "title": "Design Phase Complete",
    "status": "pending",
    "created_by": 1,
    "created_at": "2024-01-15T10:00:00Z"
  },
  "total_milestones": 3
}
```

### 4. Complete Milestone

```http
POST /api/contracts/{id}/complete_milestone/
```

**Request Body:**

```json
{
  "milestone_id": 1
}
```

**Authorization:** Only freelancer can complete milestones

**Response:**

```json
{
  "message": "Milestone marked as completed"
}
```

**Behavior:**

- Updates milestone status to 'completed'
- Adds completion timestamp
- Sends notification to client

### 5. Extend Deadline

```http
POST /api/contracts/{id}/extend_deadline/
```

**Request Body:**

```json
{
  "end_date": "2024-04-15",
  "reason": "Additional features requested by client"
}
```

**Response:**

```json
{
  "message": "Contract deadline extended successfully",
  "old_end_date": "2024-03-15",
  "new_end_date": "2024-04-15",
  "reason": "Additional features requested by client"
}
```

### 6. Terminate Contract

```http
POST /api/contracts/{id}/terminate_contract/
```

**Request Body:**

```json
{
  "reason": "Project requirements changed significantly"
}
```

**Authorization:** Only contract parties can terminate

**Response:**

```json
{
  "message": "Contract terminated successfully",
  "termination_reason": "Project requirements changed significantly",
  "terminated_by": "John Doe",
  "terminated_at": "2024-01-15T15:30:00Z"
}
```

### 7. Upload Document

```http
POST /api/contracts/{id}/upload_document/
```

**Request:** Multipart form data

```
document: <file>
document_type: "contract" | "amendment" | "other"
```

**Response:**

```json
{
  "id": 1,
  "filename": "contract_amendment.pdf",
  "document_type": "amendment",
  "uploaded_by": {
    "id": 1,
    "name": "John Doe"
  },
  "uploaded_at": "2024-01-15T14:00:00Z",
  "file_size": 245760
}
```

## Analytics and Reports

### 1. Contract Analytics

```http
GET /api/contracts/analytics/
```

**Response:**

```json
{
    "summary": {
        "total_contracts": 25,
        "active_contracts": 8,
        "completed_contracts": 15,
        "cancelled_contracts": 2,
        "total_value": 125000.00,
        "active_value": 40000.00,
        "completed_value": 75000.00,
        "average_contract_value": 5000.00,
        "contracts_this_month": 5,
        "overdue_contracts": 2
    },
    "status_distribution": [
        {"status": "active", "count": 8},
        {"status": "completed", "count": 15},
        {"status": "cancelled", "count": 2}
    ],
    "recent_contracts": [...]
}
```

**Filtering by User Type:**

- **Superuser:** All contracts
- **Client:** Only contracts where user is client
- **Freelancer:** Only contracts where user is freelancer

## Status Workflow

```
draft → active → completed
       ↓
     terminated/cancelled
```

### Status Descriptions:

- **draft:** Contract created but not signed by both parties
- **active:** Both parties signed, work in progress
- **completed:** All deliverables completed and accepted
- **cancelled:** Contract cancelled before activation
- **terminated:** Contract terminated after activation

## Error Handling

### Common Error Responses:

**400 Bad Request:**

```json
{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

**403 Forbidden:**

```json
{
  "error": "Not authorized to sign this contract"
}
```

**404 Not Found:**

```json
{
  "detail": "Not found."
}
```

## Integration Examples

### JavaScript/Angular Example:

```typescript
// Sign contract
async signContract(contractId: number) {
    const response = await this.http.post(
        `/api/contracts/${contractId}/sign_contract/`,
        {},
        { headers: { Authorization: `Bearer ${this.token}` }}
    ).toPromise();

    if (response.fully_signed) {
        this.showSuccessMessage('Contract fully executed!');
    }
}

// Add milestone
async addMilestone(contractId: number, milestone: any) {
    return this.http.post(
        `/api/contracts/${contractId}/add_milestone/`,
        { milestone },
        { headers: { Authorization: `Bearer ${this.token}` }}
    ).toPromise();
}

// Download PDF
downloadPDF(contractId: number) {
    window.open(`/api/contracts/${contractId}/download_pdf/`, '_blank');
}
```

### Python Example:

```python
import requests

# Get contract analytics
def get_contract_analytics(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('/api/contracts/analytics/', headers=headers)
    return response.json()

# Create contract
def create_contract(token, contract_data):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post('/api/contracts/',
                           json=contract_data,
                           headers=headers)
    return response.json()
```

## Features Summary

✅ **Contract CRUD Operations**
✅ **Digital Signing with Timestamps**
✅ **PDF Generation (Advanced & Fallback)**
✅ **Milestone Management**
✅ **Document Upload/Management**
✅ **Deadline Extensions**
✅ **Contract Termination**
✅ **Comprehensive Analytics**
✅ **Real-time Notifications**
✅ **Role-based Permissions**
✅ **Status Workflow Management**
✅ **Search and Filtering**
✅ **Pagination Support**

This contract management system provides a complete solution for freelance project contracts with professional PDF generation, milestone tracking, and comprehensive analytics.
