@echo off
REM Dryad.AI React Chat App Setup Script for Windows
REM This script sets up the React chat interface to connect to Dryad backend

echo 🤖 Setting up Dryad.AI React Chat Interface...

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed. Please install npm first.
    exit /b 1
)

echo ✅ Node.js and npm are installed

REM Install dependencies
echo 📦 Installing dependencies...
npm install

REM Create environment file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file to configure your Dryad.AI backend URL
)

REM Build the project
echo 🔨 Building the project...
npm run build

echo.
echo 🎉 Setup complete!
echo.
echo To start the chat interface:
echo   npm start
echo.
echo Configuration:
echo   - Backend URL: http://localhost:8000 (default)
echo   - Edit .env file to change configuration
echo.
echo Make sure your Dryad.AI backend is running before starting the chat interface!
pause