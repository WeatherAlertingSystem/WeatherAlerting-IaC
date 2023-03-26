"""An AWS Python Pulumi program - S3 Bucket initialization for Angular Frontend"""

import pulumi
import pulumi_aws as aws


class Frontend:
    def __init__(self):
        self.frontend_config = pulumi.Config("frontend")

    # Create an AWS resource (S3 Bucket)
    def create_frontend_bucket(self):
        bucket = aws.s3.Bucket(
            self.frontend_config.require("bucket_name"),
            bucket=self.frontend_config.require("bucket_name"),
            acl="public-read",
            policy=self.create_s3_frontend_policy(),
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
            force_destroy=self.frontend_config.require_bool("s3_force_destroy"),
        )
        return bucket

    def create_s3_frontend_policy(self):
        frontend_public_get_object_policy = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    sid="PublicReadGetObject",
                    actions=[
                        "s3:GetObject",
                    ],
                    effect="Allow",
                    principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(type="*", identifiers=["*"])],
                    resources=[f"arn:aws:s3:::{self.frontend_config.require('bucket_name')}/*"],
                )
            ]
        ).json
        return frontend_public_get_object_policy

    def authorize_github_to_deploy(self, github_open_id_provider):
        # Policy config allowing to Deploy to S3 Frontend Bucket (Put Object)
        deploy_policy_json = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    sid="GithubActionsPutToFrontendBucket",
                    actions=[
                        "s3:PutObject",
                    ],
                    effect="Allow",
                    resources=[f"arn:aws:s3:::{self.frontend_config.require('bucket_name')}/*"],
                )
            ],
            policy_id="AmazonS3PutFrontendBucket",
        ).json

        deploy_policy_resource = aws.iam.Policy(
            "AmazonS3PutFrontendBucket",
            description="Allows to put files into 163636840347-weather-alerting-frontend S3 Bucket."
            " Policy made for github actions - deploy job",
            policy=deploy_policy_json,
        )

        # Trusted entity policy config (answering who can assume a role)
        assume_role_policy = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    sid="GithubActionsPutToFrontendBucket",
                    actions=[
                        "sts:AssumeRoleWithWebIdentity",
                    ],
                    effect="Allow",
                    principals=[
                        aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                            type="Federated",
                            identifiers=[github_open_id_provider.arn],
                        )
                    ],
                    conditions=[
                        aws.iam.GetPolicyDocumentStatementConditionArgs(
                            test="StringLike",
                            variable="token.actions.githubusercontent.com:sub",
                            values=[f"repo:{self.frontend_config.require('repository')}:*"],
                        )
                    ],
                )
            ],
            policy_id="AmazonS3PutFrontendBucket",
        ).json

        frontend_deployer_role = aws.iam.Role(
            "GithubActionsFrontendBucketDeployer",
            name="GithubActionsFrontendBucketDeployer",
            assume_role_policy=assume_role_policy,
        )

        # Attach the created policy to the role
        aws.iam.RolePolicyAttachment(
            "S3PutObjectPolicyAttachment", role=frontend_deployer_role.name, policy_arn=deploy_policy_resource.arn
        )
