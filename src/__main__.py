"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

from autotag import register_auto_tags

# Inject tags to all AWS resources
register_auto_tags({"PROJECT": "WeatherAlertingSystem"})

# Create an AWS resource (S3 Bucket)
bucket = aws.s3.Bucket(
    "163636840347-my-test-bucket",
    acl="private",
)
