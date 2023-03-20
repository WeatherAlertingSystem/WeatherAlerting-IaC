"""An AWS Python Pulumi program - S3 Bucket initialization for Angular Frontend"""

import pulumi
import pulumi_aws as aws

# Create an AWS resource (S3 Bucket)
def create_frontend_bucket():
    bucket = aws.s3.Bucket(
        "163636840347-weather-alerting-frontend",
        bucket="163636840347-weather-alerting-frontend",
        acl="public-read",
        policy=(lambda path: open(path).read())("frontend_s3_policy.json"),
        website=aws.s3.BucketWebsiteArgs(
            index_document="index.html",
            routing_rules="""[{
                "Condition": {
                    "KeyPrefixEquals": "docs/"
                },
                "Redirect": {
                    "ReplaceKeyPrefixWith": "documents/"
                }
                }]
                """,
        ),
        force_destroy=True,
        tags={"PROJECT": "WeatherAlertingSystem"},
    )
    return bucket
