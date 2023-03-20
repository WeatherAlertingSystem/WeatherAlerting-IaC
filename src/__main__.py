"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

# Create an AWS resource (S3 Bucket)
bucket = aws.s3.Bucket(
    "163636840347-my-test-bucket",
    acl="private",
    tags={"PROJECT": "WeatherAlertingSystem"},
)
