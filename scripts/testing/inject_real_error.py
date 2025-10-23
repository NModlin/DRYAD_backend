"""
Inject a real error for testing self-healing system.
"""

import logging
from datetime import datetime

# Configure logging to write to the errors log
logging.basicConfig(
    filename='logs/gremlins_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('app.test_module')

# Inject the error - format it like a real traceback
error_msg = """KeyError: 'email' - Email key not found in user dictionary
File "app/test_module.py", line 14, in get_user_data
    user_email = user_dict['email']"""

logger.error(error_msg)

print("✅ Injected real error for app/test_module.py:14")
print("📝 Error: KeyError: 'email' - Email key not found in user dictionary")
print("⏳ Guardian should detect this within 2-5 seconds...")

