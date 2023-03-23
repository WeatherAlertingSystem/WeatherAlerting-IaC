"""An AWS Python Pulumi program - S3 Bucket initialization for Angular Frontend"""

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
account_id = config.require("account_id")
frontend_config = pulumi.Config("frontend")

# Create an AWS resource (S3 Bucket)
def create_frontend_bucket():
    bucket = aws.s3.Bucket(
        f"{account_id}-weather-alerting-frontend",
        bucket=f"{account_id}-weather-alerting-frontend",
        acl="public-read",
        policy=create_s3_frontend_policy(),
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
        force_destroy=frontend_config.require_bool("s3_force_destroy"),
        tags={"PROJECT": "WeatherAlertingSystem"},
    )
    return bucket


def create_s3_frontend_policy():
    frontend_public_get_object_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="PublicReadGetObject",
                actions=[
                    "s3:GetObject",
                ],
                effect="Allow",
                principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(type="*", identifiers=["*"])],
                resources=[f"arn:aws:s3:::{account_id}-weather-alerting-frontend/*"],
            )
        ]
    ).json
    return frontend_public_get_object_policy
