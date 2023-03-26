"""An AWS Python Pulumi program"""


import utils

# Import custom modules
from autotag import register_auto_tags
from backend import Backend
from frontend_s3 import Frontend

# Inject tags to all AWS resources
register_auto_tags({"PROJECT": "WeatherAlertingSystem"})

# Common resources
open_id_provider = utils.create_gh_open_id_provider()

# Backend resources
backend = Backend()
backend.grant_access_rights_for_gh_actions(repo_name="Backend", github_open_id_provider=open_id_provider)
backend.create_app_runner()


# Frontend resources
frontend = Frontend()
frontend.create_frontend_bucket()
frontend.authorize_github_to_deploy(github_open_id_provider=open_id_provider)
