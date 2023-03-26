"""An AWS Python Pulumi program"""

from autotag import register_auto_tags

# Import custom modules
from frontend_s3 import Frontend

# Inject tags to all AWS resources
register_auto_tags({"PROJECT": "WeatherAlertingSystem"})

# Backend resources
# ...


# Frontend resources
frontend = Frontend()
frontend.create_frontend_bucket()
frontend.authorize_github_to_deploy()
