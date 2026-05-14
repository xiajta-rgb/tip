import requests
import time
from io import BytesIO

# ===================== Configuration (No modification needed) =====================
USERNAME = 'tip'
API_TOKEN = '62a3a6f8f5bb36ef29ab10bd610ec254e0041649'
HOST = 'www.pythonanywhere.com'
WEBAPP_DOMAIN = 'tip.pythonanywhere.com'
WSGI_FILE_PATH = '/var/www/tip_pythonanywhere_com_wsgi.py'
BACKUP_FILE_PATH = '/home/tip/original_wsgi_backup.txt'
HEADERS = {'Authorization': f'Token {API_TOKEN}'}

# ===================== Core Functions (100% English, No Chinese) =====================
def backup_original_wsgi_to_file():
    """Backup original WSGI to file (avoid string nesting issues)"""
    # 1. Get original WSGI content via API
    url = f'https://{HOST}/api/v0/user/{USERNAME}/files/path{WSGI_FILE_PATH}'
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        original_content = resp.text
    except Exception as e:
        print(f"Failed to get original WSGI content: {e}")
        return False
    
    # 2. Upload backup file to PythonAnywhere
    backup_url = f'https://{HOST}/api/v0/user/{USERNAME}/files/path{BACKUP_FILE_PATH}'
    try:
        resp = requests.post(
            backup_url,
            headers=HEADERS,
            files={'content': ('original_wsgi_backup.txt', BytesIO(original_content.encode('utf-8')), 'text/plain')},
            timeout=15
        )
        if resp.status_code in [200, 201]:
            print(f"Original WSGI successfully backed up to {BACKUP_FILE_PATH}")
            return True
        else:
            print(f"Failed to upload backup file: Status code {resp.status_code}")
            return False
    except Exception as e:
        print(f"Backup WSGI to file failed: {e}")
        return False

def upload_deployment_wsgi():
    """Upload pure English temporary WSGI (no encoding issues)"""
    # Temporary WSGI script (100% English, no nested string issues)
    temp_wsgi = '''
import subprocess
import os
import time

# Step 1: Execute deployment command
deploy_success = False
try:
    # Deployment command: clone tip repository
    deploy_cmd = 'cd /home/tip/ && rm -rf tip && git clone git@github.com:xiajta-rgb/tip.git'
    result = subprocess.run(
        deploy_cmd,
        shell=True,
        cwd='/home/tip/',
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=120
    )
    # Write deployment log (English only)
    with open('/home/tip/deploy_log.txt', 'w', encoding='utf-8') as f:
        f.write(f"Deploy time: {time.ctime()}\\n")
        f.write(f"Return code: {result.returncode}\\n")
        f.write(f"STDOUT: {result.stdout}\\n")
        f.write(f"STDERR: {result.stderr}\\n")
    deploy_success = True
except Exception as e:
    with open('/home/tip/deploy_error.txt', 'w', encoding='utf-8') as f:
        f.write(f"Deployment failed: {str(e)}\\n")

# Step 1.5: Install Python dependencies
try:
    if os.path.exists('/home/tip/tip/requirements.txt'):
        pip_cmd = 'cd /home/tip/tip && python3.11 -m pip install -r requirements.txt --user'
        pip_result = subprocess.run(
            pip_cmd,
            shell=True,
            cwd='/home/tip/tip',
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300
        )
        with open('/home/tip/deploy_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"\\nPip install return code: {pip_result.returncode}\\n")
            f.write(f"Pip STDOUT: {pip_result.stdout}\\n")
            f.write(f"Pip STDERR: {pip_result.stderr}\\n")
except Exception as e:
    with open('/home/tip/deploy_error.txt', 'a', encoding='utf-8') as f:
        f.write(f"\\nPip install failed: {str(e)}\\n")

# Step 2: Copy new WSGI from project directory (instead of restoring backup)
try:
    new_wsgi_path = '/home/tip/tip/wsgi.py'
    if os.path.exists(new_wsgi_path):
        with open(new_wsgi_path, 'r', encoding='utf-8') as f:
            new_wsgi_content = f.read()
        with open('/var/www/tip_pythonanywhere_com_wsgi.py', 'w', encoding='utf-8') as f:
            f.write(new_wsgi_content)
        # Delete backup file
        if os.path.exists('/home/tip/original_wsgi_backup.txt'):
            os.remove('/home/tip/original_wsgi_backup.txt')
    else:
        # Fallback: restore original WSGI if new one doesn't exist
        with open('/home/tip/original_wsgi_backup.txt', 'r', encoding='utf-8') as f:
            original_content = f.read()
        with open('/var/www/tip_pythonanywhere_com_wsgi.py', 'w', encoding='utf-8') as f:
            f.write(original_content)
        os.remove('/home/tip/original_wsgi_backup.txt')
except Exception as e:
    with open('/home/tip/deploy_error.txt', 'a', encoding='utf-8') as f:
        f.write(f"Update WSGI failed: {str(e)}\\n")

# Step 3: WSGI response function (comply with WSGI standard)
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    if deploy_success:
        return [b'Deployment success! Check /home/tip/deploy_log.txt']
    else:
        return [b'Deployment failed! Check /home/tip/deploy_error.txt']
'''
    
    # Upload temporary WSGI file via API
    url = f'https://{HOST}/api/v0/user/{USERNAME}/files/path{WSGI_FILE_PATH}'
    try:
        resp = requests.post(
            url,
            headers=HEADERS,
            files={'content': ('wsgi.py', BytesIO(temp_wsgi.encode('utf-8')), 'text/plain')},
            timeout=15
        )
        if resp.status_code in [200, 201]:
            print("Pure English temporary WSGI uploaded successfully (no encoding issues)")
            return True
        else:
            print(f"Failed to upload temporary WSGI: {resp.status_code} - {resp.content.decode('utf-8')}")
            return False
    except Exception as e:
        print(f"Exception when uploading temporary WSGI: {e}")
        return False

def reload_webapp():
    """Reload Web App to trigger deployment"""
    url = f'https://{HOST}/api/v0/user/{USERNAME}/webapps/{WEBAPP_DOMAIN}/reload/'
    try:
        resp = requests.post(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        print("Web App reloaded successfully, deployment command triggered!")
        return True
    except Exception as e:
        print(f"Failed to reload Web App: {e}")
        return False

# ===================== Execution Flow =====================
if __name__ == '__main__':
    print("Starting automated deployment process for 'tip' account...")
    
    # Step 1: Backup original WSGI to file
    if not backup_original_wsgi_to_file():
        print("WSGI backup failed, terminate deployment")
        exit(1)
    
    # Step 2: Upload pure English temporary WSGI
    if not upload_deployment_wsgi():
        print("Temporary WSGI upload failed, terminate deployment")
        exit(1)
    
    # Step 3: Reload Web App to trigger deployment
    if not reload_webapp():
        print("Web App reload failed, deployment not triggered")
        exit(1)
    
    # Wait for deployment completion (clone repository needs time)
    print("Waiting for deployment completion (30 seconds)...")
    time.sleep(30)
    
    # Reload Web App again to apply new code
    print("Reloading Web App to apply new code...")
    if not reload_webapp():
        print("Warning: Final reload failed, but deployment may still be successful")
    
    print("Deployment process completed!")
    print("Verification steps:")
    print("   1. Check log files: /home/tip/deploy_log.txt (success) / deploy_error.txt (failure)")
    print("   2. Check repository: /home/tip/tip")
    print("   3. Access website: https://tip.pythonanywhere.com")
