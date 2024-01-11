# Local Dependencies
from src.core.logger import logging, configure_logging

# Configure logging for the worker
configure_logging(log_file='tests')

# Logger instance for the current module
logger = logging.getLogger(__name__)

# Unit tests imports
from src.apps.system.auth.tests.test_v1 import *
from src.apps.system.users.tests.test_v1 import *
from src.apps.system.tiers.tests.test_v1 import *
from src.apps.system.rate_limits.tests.test_v1 import *
from src.apps.blog.posts.tests.test_v1 import *
