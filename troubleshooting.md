# Troubleshooting Guide

This guide helps you diagnose and fix common issues you might encounter when using the Blog AI Generation Tool.

## Table of Contents

1. [API Key Issues](#api-key-issues)
2. [Backend Server Issues](#backend-server-issues)
3. [Frontend Issues](#frontend-issues)
4. [Content Generation Issues](#content-generation-issues)
5. [Dependency Issues](#dependency-issues)

## API Key Issues

### Problem: "OPENAI_API_KEY environment variable not set" error

**Solution:**
1. Make sure you've created a `.env` file in the root directory based on `.env.example`
2. Ensure your OpenAI API key is correctly set in the `.env` file:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```
3. Verify there are no spaces before or after the API key
4. Restart the backend server after making changes to the `.env` file

### Problem: "API key not valid" error

**Solution:**
1. Check that your API key is valid by testing it with a simple API call
2. Ensure your OpenAI account has billing set up and is in good standing
3. If using other API providers (Anthropic, etc.), verify those keys are also valid

## Backend Server Issues

### Problem: Backend server won't start

**Solution:**
1. Check for error messages in the terminal
2. Verify all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure you're using Python 3.12 or later
4. Check if another process is already using port 8000:
   ```bash
   # On Windows
   netstat -ano | findstr :8000
   
   # On macOS/Linux
   lsof -i :8000
   ```
5. If port 8000 is in use, you can specify a different port:
   ```bash
   python server.py --port 8001
   ```

### Problem: "Connection refused" errors when frontend tries to connect to backend

**Solution:**
1. Verify the backend server is running
2. Check that the server is running on the expected port (default: 8000)
3. Ensure your firewall isn't blocking the connection
4. If running the server on a different machine, make sure CORS is properly configured

## Frontend Issues

### Problem: Frontend won't start or build

**Solution:**
1. Ensure all dependencies are installed:
   ```bash
   cd frontend
   npm install
   ```
2. Check for errors in the terminal
3. Verify you're using a compatible Node.js version (14.x or later recommended)
4. Clear the Next.js cache:
   ```bash
   cd frontend
   rm -rf .next
   ```

### Problem: WebSocket connection errors

**Solution:**
1. Verify the backend server is running
2. Check that the WebSocket URL in the frontend code matches the backend server address
3. Ensure your browser supports WebSockets
4. Check if any browser extensions might be blocking WebSocket connections

## Content Generation Issues

### Problem: Content generation is very slow

**Solution:**
1. Check your internet connection
2. Verify that your OpenAI account has access to the models being used
3. Consider using a less powerful but faster model by modifying the `model` parameter in the code
4. If using research features, these can significantly increase generation time

### Problem: Generated content has errors or is low quality

**Solution:**
1. Enable the "proofread" option when generating content
2. Try a different tone or style
3. Provide more specific keywords or a more detailed topic
4. Adjust the temperature parameter in the code (lower for more conservative outputs, higher for more creative)

## Dependency Issues

### Problem: ImportError or ModuleNotFoundError

**Solution:**
1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
2. Check that you're using the correct Python environment
3. If using Poetry, make sure the environment is activated:
   ```bash
   poetry shell
   ```
4. For specific package errors, try reinstalling the package:
   ```bash
   pip uninstall package_name
   pip install package_name
   ```

### Problem: Version conflicts between packages

**Solution:**
1. Consider using a virtual environment to isolate dependencies
2. Use Poetry to manage dependencies (recommended):
   ```bash
   poetry install
   ```
3. If specific packages are causing conflicts, try installing compatible versions:
   ```bash
   pip install package_name==specific_version
   ```

## Still Having Issues?

If you're still experiencing problems after trying these solutions:

1. Check the project's GitHub issues to see if others have encountered the same problem
2. Search for error messages online
3. Try running the tests to see if they pass:
   ```bash
   python -m unittest discover tests
   ```
4. Consider opening an issue on the GitHub repository with details about your problem, including:
   - Error messages
   - Steps to reproduce
   - Your environment (OS, Python version, etc.)
   - Any modifications you've made to the code
