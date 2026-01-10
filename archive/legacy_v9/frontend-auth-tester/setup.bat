@echo off
REM GremlinsAI OAuth2 & JWT Authentication Tester Setup Script for Windows
REM This script sets up the comprehensive frontend testing application

echo 🚀 Setting up GremlinsAI Authentication Tester...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ and try again.
    pause
    exit /b 1
)

echo ✅ Node.js detected
node --version

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not installed. Please install npm and try again.
    pause
    exit /b 1
)

echo ✅ npm detected
npm --version

REM Install dependencies
echo 📦 Installing dependencies...
npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✅ .env file created
    echo.
    echo ⚠️  IMPORTANT: Please edit the .env file and set your configuration:
    echo    - REACT_APP_GOOGLE_CLIENT_ID: Your Google OAuth2 client ID
    echo    - REACT_APP_API_BASE_URL: GremlinsAI backend URL (default: http://localhost:8000)
    echo    - REACT_APP_WS_BASE_URL: WebSocket server URL (default: ws://localhost:8000)
    echo.
) else (
    echo ✅ .env file already exists
)

REM Create public directory if it doesn't exist
if not exist "public" (
    mkdir public
)

REM Create a simple favicon if it doesn't exist
if not exist "public\favicon.ico" (
    echo 🎨 Creating favicon...
    echo. > public\favicon.ico
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Edit the .env file with your configuration
echo 2. Ensure GremlinsAI backend is running at http://localhost:8000
echo 3. Start the application with: npm start
echo.
echo 🔧 Available commands:
echo    npm start          - Start the development server
echo    npm run build      - Build for production
echo    npm test           - Run tests
echo.
echo 📖 For detailed instructions, see README.md
echo.
echo 🌐 The application will be available at: http://localhost:3000
echo.
echo Happy testing! 🧪
pause
