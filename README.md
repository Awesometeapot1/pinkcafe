# Bristol Pink Café Dashboard 

A Streamlit dashboard for the Bristol Pink Café case study:
- Upload café CSV sales files (coffee + croissant)
- View sales trends and best sellers
- Predict the next 4 weeks (AI heuristic or ML Linear Regression or ML random forest) and can be toggled to 8 weeks
- Role-based access:
  - **Admin**: allows you to create more staff and manager accounts if needed and does everything a manager can
  - **Staff**: record sales entries, can also see and esport csv files
  - **Manager**: view sales totals, charts, records, and export CSV and edit sales entries

---

## 1) Requirements
- Python 3.11+ (3.13 works too)
- Packages:
  - streamlit
  - pandas
  - numpy
  - scikit-learn (optional, only needed for ML mode)

---

## 2) Setup (Windows PowerShell)

### Create + activate virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Install dependencies
python -m pip install --upgrade pip
python -m pip install streamlit pandas numpy scikit-learn
If you want to capture dependencies for teammates:

python -m pip freeze > requirements.txt
3) Run the app
From the project folder:

python -m streamlit run dashboardfoodwastage.py
4) Login (Demo Accounts)
This project uses simple demo accounts (change later if needed):

Manager

Username: manager

Password: manager123

Staff

Username: staff

Password: staff123

5) Price list (teacher-provided)
The Staff sales entry page uses fixed unit prices from:

product_prices.csv (in the same folder as the app)

Example format:

product,unit_price
Cappuccino,3.50
Americano,3.00
Croissant,2.20
✅ Unit price is displayed as £x.xx and staff cannot edit it in the form.

If product_prices.csv is missing, the app creates a template—edit it with the correct teacher prices.

6) Staff sales logging
Staff entries are saved to:

sales_entries.csv

Columns:

date

product

qty

unit_price

staff_user

created_at

Manager pages read this file to show totals, charts, filters, and export.

7) Prediction dashboard CSV inputs
Prediction page expects two CSV files:

Coffee CSV (weird layout)
Has a Date column

First row contains product names in the other columns (e.g., Cappuccino, Americano)

Following rows contain daily sales counts

Croissant CSV (normal layout)
Columns like:

Date

Number Sold (or similar)

8) Project structure (recommended)
pinkcafe/
  dashboardfoodwastage.py
  product_prices.csv
  sales_entries.csv          (created by app after staff saves sales)
  requirements.txt           (optional)
  README.md
  .venv/                     (local only, do not commit)
9) Troubleshooting
“No module named streamlit”
You installed packages outside the venv. Activate the venv and reinstall:

.\.venv\Scripts\Activate.ps1
python -m pip install streamlit pandas numpy scikit-learn
“streamlit is not recognized…”
Use:

python -m streamlit run dashboardfoodwastage.py
10) Notes
ML mode uses Linear Regression (simple baseline) and shows training R².

AI mode uses a rolling mean + light trend heuristic.

Demo login is for coursework / prototype purposes; upgrade to hashed passwords + secrets for production-style security.



