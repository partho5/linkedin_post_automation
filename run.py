#!/usr/bin/env python3
"""
Script to run the LinkedIn content automation pipeline via API
"""

import os
import asyncio
import subprocess

import aiohttp
import json
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_server_running(host: str, port: str) -> bool:
    """Check if the server is running by making a health check request"""
    try:
        timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout for health check
        async with aiohttp.ClientSession(timeout=timeout) as session:
            health_url = f"http://{host}:{port}/api/v1/health-check"
            async with session.get(health_url) as response:
                return response.status == 200
    except:
        return False

def start_server(host: str, port: str):
    """Start the server using uvicorn with venv activation"""
    import subprocess
    import time
    import platform
    import threading
    
    print(f"🚀 Starting server on {host}:{port}...")
    
    # Determine the activation script based on OS
    if platform.system() == "Windows":
        activate_script = "linkedin_automation\\Scripts\\activate"
        # Use start /B for background execution on Windows
        shell_cmd = f"start /B cmd /c \"{activate_script} && uvicorn main:app --host {host} --port {port}\""
    else:
        activate_script = "linkedin_automation/Scripts/activate"
        # Use & for background execution on Unix/Linux
        shell_cmd = f"source {activate_script} && uvicorn main:app --host {host} --port {port} &"
    
    print(f"🔧 Activating venv and starting server: {shell_cmd}")
    
    # Start server in background with venv activation
    process = subprocess.Popen(
        shell_cmd,
        shell=True,
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Function to read and print server logs
    def print_server_logs(stream, prefix):
        try:
            for line in iter(stream.readline, ''):
                if line:
                    print(f"{prefix} {line.rstrip()}")
        except:
            pass
    
    # Start threads to capture server logs
    stdout_thread = threading.Thread(target=print_server_logs, args=(process.stdout, "📝 [SERVER]"))
    stderr_thread = threading.Thread(target=print_server_logs, args=(process.stderr, "⚠️  [SERVER ERROR]"))
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    # Wait a bit for server to start
    time.sleep(3)
    
    return process

async def run_automation():
    """Run the content automation pipeline via API"""
    
    # Get configuration from environment variables
    host = os.getenv('APP_HOST', '127.0.0.1')
    port = os.getenv('APP_PORT', '8001')
    auth_token = os.getenv('BASIC_AUTH_TOKEN')
    
    if not auth_token:
        print("❌ Error: BASIC_AUTH_TOKEN environment variable is required")
        sys.exit(1)
    
    # Check if server is running
    print(f"🔍 Checking if server is running on {host}:{port}...")
    server_running = await check_server_running(host, port)
    
    server_process = None
    if not server_running:
        print("⚠️  Server is not running. Starting it now...")
        server_process = start_server(host, port)
        
        # Wait for server to be ready
        for attempt in range(10):  # Try for 10 attempts
            await asyncio.sleep(2)
            if await check_server_running(host, port):
                print("✅ Server is now running!")
                break
        else:
            print("❌ Failed to start server or server not responding")
            if server_process:
                server_process.terminate()
            sys.exit(1)
    else:
        print("✅ Server is already running!")
    
    # Construct the API URL
    api_url = f"http://{host}:{port}/api/v1/automate-content"
    
    # Request payload
    payload = {
        "enable_idea_generation": True,
        "enable_content_generation": True,
        "enable_image_generation": False,
        "enable_posting": False,
        "style_params": "professional and engaging"
    }
    
    # Headers with authentication
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    timeout_seconds = 60*10  # seconds

    print(f"🚀 Starting LinkedIn content automation...")
    print(f"📡 API URL: {api_url}")
    print(f"⚙️  Configuration: {json.dumps(payload, indent=2)}")
    print(f"⏱️  Timeout: {timeout_seconds} seconds")
    print("-" * 50)
    
    try:
        # Create timeout context
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)  # timeout seconds
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print("📡 Making API request...")
            async with session.post(api_url, json=payload, headers=headers) as response:
                print(f"📊 Response Status: {response.status}")
                print(f"📊 Response Headers: {dict(response.headers)}")
                
                # Read response content
                response_text = await response.text()
                print(f"📊 Response Size: {len(response_text)} characters")
                
                try:
                    response_json = json.loads(response_text)
                    print(f"📋 Response JSON: {json.dumps(response_json, indent=2)}")
                    
                    # Print detailed pipeline information if available
                    if response_json.get("pipeline_id"):
                        print(f"🆔 Pipeline ID: {response_json['pipeline_id']}")
                    if response_json.get("stages"):
                        print(f"📋 Pipeline Stages: {response_json['stages']}")
                    if response_json.get("estimated_duration"):
                        print(f"⏱️  Estimated Duration: {response_json['estimated_duration']}")
                        
                except json.JSONDecodeError:
                    print(f"📋 Response (raw): {response_text}")
                
                if response.status == 200:
                    print("✅ Automation pipeline completed successfully!")
                    return True
                else:
                    print(f"❌ Automation pipeline failed with status {response.status}")
                    if response_json.get("error"):
                        print(f"❌ Error Details: {response_json['error']}")
                    return False
                    
    except asyncio.TimeoutError:
        print("⏰ Error: Request timed out after 180 seconds")
        return False
    except aiohttp.ClientConnectorError as e:
        print(f"🔌 Error: Could not connect to server at {api_url}")
        print(f"   Details: {str(e)}")
        return False
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return False
    finally:
        # Clean up server process if we started it
        if server_process:
            print("🛑 Stopping server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✅ Server stopped")

def main():
    """Main function"""
    print("LinkedIn Content Automation Runner")
    print("=" * 40)
    
    # Check if required environment variables are set
    required_vars = ['BASIC_AUTH_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        sys.exit(1)
    
    # Run the automation
    success = asyncio.run(run_automation())
    
    if success:
        print("\n🎉 Automation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Automation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 