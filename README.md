# Medical Store Management System

## Overview

The Medical Store Management System is a web-based application developed using Python Flask and MySQL to automate and simplify the management of a medical store. The system helps manage medicines, inventory, sales, purchases, suppliers, and customer interactions through an easy-to-use interface.

The application also includes AI-assisted medicine search functionality, autocomplete suggestions, and inventory tracking features to improve efficiency and user experience.

---

## Features

### Medicine Management

* Add new medicines
* Update medicine details
* Delete medicines
* View medicine inventory
* Search medicines by name

### Inventory Management

* Track medicine stock levels
* Batch-wise inventory management
* Expiry date monitoring
* Quantity tracking

### Sales Management

* Generate sales records
* Manage customer purchases
* Calculate billing amounts
* Maintain sales history

### Purchase Management

* Record medicine purchases
* Supplier-wise purchase tracking
* Update stock automatically after purchases

### Supplier Management

* Add supplier details
* Edit supplier information
* Maintain supplier database

### Smart Search Features

* Medicine name autocomplete
* AI-assisted symptom-based medicine search
* Instant medicine suggestions
* Search medicines using descriptions and categories

### Reporting

* View inventory reports
* Monitor stock availability
* Analyze sales and purchase records

---

## Technologies Used

### Backend

* Python
* Flask

### Database

* MySQL

### Frontend

* HTML
* CSS
* JavaScript
* Bootstrap
* jQuery

### APIs

* Flask JSON API
* AJAX-based autocomplete

---

## Database Configuration

Database Name:

```sql
medcl
```

Update the database credentials inside the application:

```python
def get_db_connection():
    conn = mc.connect(
        host="localhost",
        user="root",
        passwd="YOUR_PASSWORD",
        database="medcl"
    )
    return conn
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/MedicalStoreManagementSystem.git
cd MedicalStoreManagementSystem
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

Open browser:

```text
http://127.0.0.1:5000
```

---

## Project Structure

```text
MedicalStoreManagementSystem/
│
├── app.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── home.html
│   ├── search_results.html
│   └── other_pages.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── database/
    └── medcl.sql
```

---

## AI-Based Medicine Search

The system includes an AI-assisted search feature where users can enter symptoms and receive medicine recommendations based on medicine descriptions and categories stored in the database.

Example:

```text
Input:
fever

Output:
Paracetamol
Crocin
Dolo 650
```

---

## Autocomplete Functionality

The application provides real-time medicine name suggestions while typing.

Example:

```text
User types:
Par

Suggestions:
Paracetamol
Paracip
Parafast
```

---

## Future Enhancements

* Barcode Scanning
* Online Medicine Ordering
* SMS Notifications
* Email Alerts
* Prescription Upload
* Sales Analytics Dashboard
* AI Chat Assistant
* Mobile Application Support

---

## Author

Developed by:

Vaishnav R Nair

Integrated Bachelor of Computer Applications (IMCA)

---

## License

This project is developed for educational and learning purposes.
