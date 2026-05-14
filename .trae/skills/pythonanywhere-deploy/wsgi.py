# This file contains the WSGI configuration for the patent_crawler project
# for PythonAnywhere deployment

import sys
import os
import asyncio
from io import BytesIO
# 提前导入日志模块，避免异常块中导入失败
import logging
import traceback

# ========== 1. Configure Logging ==========
# Set up basic logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== 2. Project Configuration ==========
# Define the project root directory
project_home = '/home/tip/tip'  # PythonAnywhere 上的项目根目录
logger.info(f"Project home set to: {project_home}")

# Check if project directory exists
if not os.path.exists(project_home):
    logger.error(f"Project directory does not exist: {project_home}")
    # Try to find the actual directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Current directory: {current_dir}")
    project_home = current_dir
    logger.info(f"Falling back to current directory: {project_home}")

# Add the project directory to the Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)
    logger.info(f"Added project directory to sys.path: {project_home}")
else:
    logger.info(f"Project directory already in sys.path: {project_home}")

# Show all paths in sys.path for debugging
logger.info("Current sys.path:")
for i, path in enumerate(sys.path):
    logger.info(f"  {i}: {path}")

# Change to the project directory
try:
    os.chdir(project_home)
    logger.info(f"Successfully changed working directory to: {project_home}")
    logger.info(f"Current working directory: {os.getcwd()}")
except OSError as e:
    logger.error(f"Failed to change working directory: {str(e)}")

# 补充：设置Python编码，避免中文乱码
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# Check if main.py exists
main_py_path = os.path.join(project_home, 'main.py')
if os.path.exists(main_py_path):
    logger.info(f"main.py found at: {main_py_path}")
else:
    logger.error(f"main.py NOT found at: {main_py_path}")
    # List files in project directory
    logger.info("Files in project directory:")
    try:
        for item in os.listdir(project_home):
            logger.info(f"  - {item}")
    except Exception as e:
        logger.error(f"Failed to list directory: {str(e)}")

# ========== 3. ASGI to WSGI Adapter ==========
# This adapter converts the FastAPI ASGI app to a WSGI-compatible app
def asgi_to_wsgi(asgi_app):
    def wsgi_app(environ, start_response):
        # Build ASGI scope
        headers = []
        for k, v in environ.items():
            if k.startswith("HTTP_"):
                header_name = k[5:].lower().replace("_", "-")
                headers.append((header_name.encode("utf-8"), v.encode("utf-8")))
        
        # Handle special headers that don't start with HTTP_
        if "CONTENT_TYPE" in environ:
            headers.append((b"content-type", environ["CONTENT_TYPE"].encode("utf-8")))
        if "CONTENT_LENGTH" in environ:
            headers.append((b"content-length", environ["CONTENT_LENGTH"].encode("utf-8")))
        
        scope = {
            "type": "http",
            "method": environ["REQUEST_METHOD"],
            "path": environ["PATH_INFO"],
            "query_string": environ["QUERY_STRING"].encode("utf-8"),
            "headers": headers,
            "server": (environ["SERVER_NAME"], int(environ["SERVER_PORT"])),
            "client": (environ.get("REMOTE_ADDR", ""), int(environ.get("REMOTE_PORT", 0))),
        }

        # Store response data
        response_status = '500 Internal Server Error'  # 默认500错误，确保不会为None
        response_headers = [('Content-Type', 'text/plain; charset=utf-8')]  # 默认响应头
        response_body = []

        # ASGI send function
        async def send(message):
            nonlocal response_status, response_headers
            if message["type"] == "http.response.start":
                response_status = f"{message['status']} {message.get('reason', '')}"
                response_headers = [
                    (k.decode("utf-8"), v.decode("utf-8")) 
                    for k, v in message["headers"]
                ]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        # ASGI receive function (handles request body)
        async def receive():
            wsgi_input = environ.get("wsgi.input", BytesIO(b""))
            request_body = wsgi_input.read() if hasattr(wsgi_input, "read") else b""
            return {"type": "http.request", "body": request_body, "more_body": False}

        # Run the ASGI app
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # 运行ASGI应用，捕获内部异常
            loop.run_until_complete(asgi_app(scope, receive, send))
        except Exception as e:
            # 记录ASGI应用运行异常
            logger.error(f"ASGI app execution failed: {type(e).__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            # 构造错误响应体
            response_body.append(f"ASGI app error: {str(e)}".encode("utf-8"))
        finally:
            # 确保循环无论是否成功都关闭，避免内存泄漏
            loop.close()

        # Return WSGI response
        start_response(response_status, response_headers)
        return [b"".join(response_body)]

    return wsgi_app

# ========== 4. Import and Initialize the App ==========
# Import the FastAPI app from main.py
application = None
try:
    logger.info("Attempting to import main module...")
    # First try simple import
    try:
        import main
        logger.info(f"Successfully imported main module from: {main.__file__}")
        fastapi_asgi_app = main.app
    except ImportError:
        # Try from current directory
        logger.info("Trying relative import...")
        sys.path.insert(0, '.')
        import main
        logger.info(f"Successfully imported main module from: {main.__file__}")
        fastapi_asgi_app = main.app
    
    logger.info("Successfully imported FastAPI app from main.py")
    
    # Manually initialize database tables (WSGI doesn't have lifespan)
    try:
        from app.core.database import CrawlerBase, AppBase, crawler_engine, app_engine, CrawlerSessionLocal
        from app.models import (
            WeeklyReport, Repository, RepositoryImage, AISummary,
            RepositoryStatistic, Paper, PaperDailyReport, ProductSelector,
            NavCategory, NavTool, ExcludedProject, JsCode,
        )
        
        logger.info("Creating database tables...")
        CrawlerBase.metadata.create_all(bind=crawler_engine)
        AppBase.metadata.create_all(bind=app_engine)
        logger.info("Database tables created successfully")
        
        # Initialize nav data
        from app.core.init_nav_db import init_nav_db
        init_nav_db()
        
        # Initialize crawler data
        from app.core.init_data import init_data
        db = CrawlerSessionLocal()
        try:
            init_data(db)
        except Exception as e:
            db.rollback()
            logger.error(f"Data initialization failed: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database initialization failed: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
    
    # Convert to WSGI-compatible app
    application = asgi_to_wsgi(fastapi_asgi_app)
    logger.info("Successfully converted ASGI app to WSGI-compatible app")
    
except Exception as e:
    # 完善日志记录，捕获更详细的错误堆栈
    error_message = f"{type(e).__name__}: {str(e)}"
    error_traceback = traceback.format_exc()
    
    logger.error(f"Application initialization failed: {error_message}")
    logger.error("="*80)
    logger.error("Full error traceback:")
    logger.error(error_traceback)
    logger.error("="*80)
    
    # 保存错误信息供error_application使用
    error_info = {
        'message': error_message,
        'type': type(e).__name__,
        'traceback': error_traceback,
        'project_home': project_home,
        'cwd': os.getcwd(),
        'main_exists': os.path.exists('main.py'),
        'sys_paths': list(sys.path)
    }
    
    # Create a simple error response for debugging
    def error_application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-Type', 'text/plain; charset=utf-8')]
        start_response(status, response_headers)
        error_msg = f"WSGI Initialization Error: {error_info['message']}\n\n"
        error_msg += f"Project home: {error_info['project_home']}\n"
        error_msg += f"Current dir: {error_info['cwd']}\n"
        error_msg += f"main.py exists: {error_info['main_exists']}\n"
        error_msg += "\nSys.path:\n"
        for path in error_info['sys_paths']:
            error_msg += f"  - {path}\n"
        error_msg += "\nFull traceback:\n"
        error_msg += error_info['traceback']
        return [error_msg.encode('utf-8')]
    
    application = error_application
    logger.info("Set up error application for debugging")

# Ensure application is defined
if application is None:
    logger.error("Application is still None after initialization")
    def fallback_application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-Type', 'text/plain; charset=utf-8')]
        start_response(status, response_headers)
        return [b"Fallback error: Application not initialized"]
    application = fallback_application