# Subscription Hub

Subscription Hub is a subscription management platform built for the Odoo x FLUX Lucknow Hackathon 2026.

The platform manages the main lifecycle of a subscription-based business, including products, subscription plans, customers, subscriptions, invoices, payments, staff access, and financial reporting.

## Features

### Authentication and Roles

- Customer signup and login
- Unique email validation
- Secure password hashing
- Password validation with:
  - More than 8 characters
  - Uppercase character
  - Lowercase character
  - Special character
- Role-based access for:
  - Admin
  - Staff
  - Customer
- Only admins can create staff accounts

### Products

- View active subscription products
- Admin can create new products
- Product information includes:
  - Name
  - Type
  - Sales price
  - Cost price
  - Notes

### Subscription Plans

- View available subscription plans
- Admin can create new plans
- Supported billing frequencies:
  - Daily
  - Weekly
  - Monthly
  - Yearly
- Minimum quantity configuration

### Subscription Management

- Customers can subscribe to plans
- Only one active subscription is maintained per customer
- Customers can change plans
- Customers can cancel active subscriptions
- Subscription history is maintained

### Invoice Management

- Generate invoices from active subscriptions
- Duplicate open invoices are prevented
- Invoice workflow:

```text
Draft -> Confirmed -> Paid
```

- Customers can view their own invoices
- Admin can view invoices across customers
- Invoice due-date support
- Outstanding and overdue invoice tracking

### Payment Management

- Record payments against invoices
- Supported payment methods include:
  - UPI
  - Credit Card
  - Debit Card
  - Bank Transfer
- Payment information includes:
  - Payment method
  - Amount
  - Date
  - Notes
- Successful payment automatically marks the invoice as Paid

### Admin Dashboard

The admin dashboard provides a central overview of the subscription business.

It includes:

- Total customers
- Active subscriptions
- Available plans
- Revenue received
- Amount owed
- Outstanding invoices
- Overdue invoices
- Registered customers
- Staff members
- All invoices
- All subscriptions

Admins can also:

- Add products
- Add subscription plans
- Create staff accounts

## User Roles

### Customer

Customers can:

- Register and log in
- Browse products
- Browse subscription plans
- Subscribe to a plan
- Cancel a subscription
- View subscription history
- Generate invoices
- Confirm invoices
- Record payments
- View their invoices

### Staff

Staff accounts are created only by an administrator.

Staff can:

- Log in to the platform
- Access normal platform functionality
- Browse products and plans

Staff cannot access the administrator dashboard.

### Admin

Admins have complete management access and can:

- Monitor customers
- Monitor subscriptions
- Monitor invoices
- Monitor financial metrics
- Create products
- Create subscription plans
- Create staff members

## Technology Stack

### Backend

- Python
- Flask

### Database

- MongoDB
- PyMongo

### Frontend

- HTML
- CSS
- Bootstrap 5
- Bootstrap Icons
- Jinja2 Templates

### Security

- Werkzeug password hashing
- Flask session-based authentication

## Project Structure

```text
odoo-subscription-hub/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── static/
│   └── css/
│       └── style.css
│
└── templates/
    ├── base.html
    ├── home.html
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    ├── products.html
    ├── plans.html
    ├── invoices.html
    ├── payment.html
    └── admin.html
```

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/aaryanpathak22/odoo-subscription-hub.git
cd odoo-subscription-hub
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start MongoDB

Make sure MongoDB is running locally.

The default application configuration expects MongoDB on:

```text
mongodb://127.0.0.1:27017/
```

### 5. Create a .env file

Create .env in the project root:

```env
MONGO_URI=mongodb://127.0.0.1:27017/
DATABASE_NAME=odoo_subscription_hub
SECRET_KEY=your-secret-key
```

### 6. Run the application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Demo Flow

A recommended demonstration flow is:

```text
Customer Signup
      ↓
Login
      ↓
Browse Products
      ↓
Choose Subscription Plan
      ↓
Active Subscription
      ↓
Generate Invoice
      ↓
Confirm Invoice
      ↓
Record Payment
      ↓
Invoice Paid
      ↓
Admin Financial Dashboard
```

For the administrator flow:

```text
Admin Login
    ↓
Create Product / Plan
    ↓
Create Staff Account
    ↓
Monitor Customers
    ↓
Monitor Subscriptions
    ↓
Monitor Invoices
    ↓
Track Revenue / Outstanding / Overdue
```

## Database Collections

The application uses MongoDB collections such as:

```text
users
products
plans
subscriptions
invoices
payments
```

## Hackathon Scope

The project focuses on delivering a working end-to-end subscription management MVP.

Implemented core lifecycle:

```text
Products
   ↓
Plans
   ↓
Subscriptions
   ↓
Invoices
   ↓
Payments
   ↓
Revenue Reporting
```

Additional enterprise features such as advanced discount engines, automated tax rules, quotation workflows, password reset email delivery, product variants, and automated subscription renewals can be added in future iterations.

## Team

Built for the Odoo x FLUX Lucknow Hackathon 2026.

Contributors:

- Aaryan Pathak
- Bhoomi Saini
- Shashwat Tiwari

## Repository

GitHub:

```text
https://github.com/aaryanpathak22/odoo-subscription-hub
```
