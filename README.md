# NursingCNE - Professional Nursing Education Platform

NursingCNE is a professional web platform designed for Nursing Continuing Education (CNE). It provides a streamlined interface for nurses to register for courses, manage their certifications, and for administrators to manage offers, registrations, and site content.

## 🚀 Features

- **Dynamic Offer Management**: Administrators can create and update CNE packages and workshops.
- **User Registration**: Seamless registration process for nursing professionals.
- **Admin Dashboard**: Secure management interface for handling site settings, gallery, and registrations.
- **Automated Database Setup**: Automatic initialization of SQLite database with sample data.
- **FastAPI Backend**: High-performance asynchronous API handling.
- **Static Frontend**: Pre-built static pages served directly by the backend for maximum speed.

## 🛠️ Tech Stack

- **Backend**: Python 3.x, FastAPI
- **Database**: SQLite (Serverless)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Server**: Uvicorn (ASGI)
- **Security**: Bcrypt for password hashing, JWT-ready architecture.

## 📂 Project Structure

```text
├── data/               # SQLite database storage
├── public/             # Frontend static files (HTML, CSS, JS)
│   ├── admin/          # Admin dashboard interface
│   └── images/         # Static assets
├── routes/             # API route handlers (Admin, Offers, Payments, etc.)
├── uploads/            # User-uploaded content
├── utils/              # Helper functions (Mailers, etc.)
├── database.py         # Database connection and schema
├── main.py             # Application entry point
├── package.json        # Start scripts
└── requirements.txt    # Python dependencies
```

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.8 or higher
- Node.js & Yarn (for running via package scripts)

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key
```

### 3. Install Dependencies
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 4. Running the Application
Using Yarn:
```bash
yarn start
```
Or manually via Uvicorn:
```bash
venv/bin/uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

The application will be available at `http://localhost:3000`.

## 🔒 Security Note
- The default admin credentials are created upon first run. Change them immediately in the `.env` file or via the admin settings.
- Ensure the `data/` folder is backed up regularly as it contains the SQLite database.

## 📄 License
This project is proprietary and built for NursingCNE.
