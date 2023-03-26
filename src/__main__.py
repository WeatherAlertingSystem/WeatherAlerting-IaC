"""An AWS Python Pulumi program"""

from autotag import register_auto_tags
from backend import Backend

# Inject tags to all AWS resources
register_auto_tags({"PROJECT": "WeatherAlertingSystem"})

backend = Backend()
backend.grant_access_rights_for_gh_actions("Backend")
backend.create_app_runner()
