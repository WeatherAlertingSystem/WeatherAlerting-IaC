"""An AWS Python Pulumi program - App runner for Backend"""

import time

import pulumi
import pulumi_aws as aws


class Backend:
    def __init__(self):
        self.common_config = pulumi.Config("common")
        self.backend_config = pulumi.Config("backend")
        self.account_id = self.common_config.require_secret_int("account_id")

    def grant_access_rights_for_gh_actions(self, repo_name):
        github_open_id_provider = aws.iam.OpenIdConnectProvider(
            f"{repo_name}GithubProvider",
            client_id_lists=["sts.amazonaws.com"],
            thumbprint_lists=["6938fd4d98bab03faadb97b34396831e3780aea1"],
            url="https://token.actions.githubusercontent.com",
        )

        backend_deployer_role = aws.iam.Role(
            f"{repo_name}GithubActionsRole",
            name=f"{repo_name}GithubActionsRole",
            assume_role_policy=aws.iam.get_policy_document(
                statements=[
                    aws.iam.GetPolicyDocumentStatementArgs(
                        actions=["sts:AssumeRoleWithWebIdentity"],
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
                                values=[f"repo:{self.backend_config.require('github_repository')}:*"],
                            )
                        ],
                    )
                ]
            ).json,
        )

        # Policy for pushing image to ECR
        ecr_push_image_policy = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    actions=[
                        "ecr:CompleteLayerUpload",
                        "ecr:GetAuthorizationToken",
                        "ecr:UploadLayerPart",
                        "ecr:InitiateLayerUpload",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:PutImage",
                    ],
                    effect="Allow",
                    resources=["*"],
                )
            ],
            policy_id="PushImagesToECR",
        ).json

        # Attach ecr_push_image_policy to backend_deployer_role
        aws.iam.RolePolicyAttachment(
            "PushImagesToECRPolicyAttachment",
            role=backend_deployer_role,
            policy_arn=aws.iam.Policy(
                resource_name="PushImagesToECR",
                policy=ecr_push_image_policy,
            ).arn,
        )

    def create_ecr_access_role(self):
        role = aws.iam.Role(
            resource_name="AppRunnerAccessToECR",
            name="AppRunnerAccessToECR",
            assume_role_policy=aws.iam.get_policy_document(
                statements=[
                    aws.iam.GetPolicyDocumentStatementArgs(
                        actions=["sts:AssumeRole"],
                        effect="Allow",
                        principals=[
                            aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                                type="Service",
                                identifiers=["build.apprunner.amazonaws.com"],
                            )
                        ],
                    )
                ]
            ).json,
        )
        # Attach Policy to ECR access role.
        aws.iam.RolePolicyAttachment(
            resource_name="GetECRImagesPolicy",
            role=role,
            policy_arn=aws.iam.Policy(
                resource_name="GetECRImagesPolicy",
                policy=aws.iam.get_policy_document(
                    statements=[
                        aws.iam.GetPolicyDocumentStatementArgs(
                            effect="Allow",
                            actions=[
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:DescribeImages",
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchCheckLayerAvailability",
                            ],
                            resources=["*"],
                        )
                    ],
                ).json,
            ).arn,
        )
        return role

    def create_app_runner(self):
        aws.apprunner.Service(
            resource_name="AppRunnerService",
            service_name="AppRunnerService",
            source_configuration=aws.apprunner.ServiceSourceConfigurationArgs(
                authentication_configuration=aws.apprunner.ServiceSourceConfigurationAuthenticationConfigurationArgs(
                    # Workaround due to pulumi-aws bug: https://github.com/pulumi/pulumi-aws/issues/1697
                    access_role_arn=self.create_ecr_access_role().arn.apply(lambda arn: time.sleep(10) or arn)
                ),
                image_repository=aws.apprunner.ServiceSourceConfigurationImageRepositoryArgs(
                    image_identifier=f"{self.backend_config.require('ecr_uri')}:latest",
                    image_repository_type="ECR",
                    image_configuration=aws.apprunner.ServiceSourceConfigurationImageRepositoryImageConfigurationArgs(
                        port=self.backend_config.require_int("port")
                    ),
                ),
                auto_deployments_enabled=self.backend_config.require_bool("app_runner_auto_deployment"),
            ),
            instance_configuration=aws.apprunner.ServiceInstanceConfigurationArgs(
                cpu=self.backend_config.require("app_runner_cpu"),
                memory=self.backend_config.require("app_runner_memory"),
            ),
        )