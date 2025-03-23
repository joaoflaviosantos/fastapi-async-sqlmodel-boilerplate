# Local Dependencies
from src.core.logger import logger_api_test

# Logger instance for the current module
logger = logger_api_test

# Unit tests imports (V1 routes)
from src.apps.auth.tests.test_v1 import *
from src.apps.system.tiers.tests.test_v1 import *
from src.apps.system.rate_limits.tests.test_v1 import *
from src.apps.admin.users.tests.test_v1 import *
from src.apps.admin.tasks.tests.test_v1 import *
from src.apps.blog.posts.tests.test_v1 import *
