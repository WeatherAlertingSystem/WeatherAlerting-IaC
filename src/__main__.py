"""An AWS Python Pulumi program"""

# Import custom modules
from frontend_s3 import Frontend

# Backend resources
# ...

# Frontend resources
frontend = Frontend()
frontend.create_frontend_bucket()
frontend.authorize_github_to_deploy()
