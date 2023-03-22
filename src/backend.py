"""An AWS Python Pulumi program - App runner for Backend"""

import pulumi
import pulumi_aws as aws


class Backend:
    def __init__(self):
        self.common_config = pulumi.Config("common")
        self.backend_config = pulumi.Config("backend")
        self.account_id = self.common_config.require_secret_int("account_id")

        self.ecr_repository = self.create_aws_ecr_repository()
        self.app_runner = self.create_app_runner()

    def create_aws_ecr_repository(self):
        return aws.ecr.Repository(
            f"{self.account_id}",
            name="backend",
            force_delete=self.backend_config.require_bool("ecr_repo_force_destroy"),
        )

    def create_ecr_access_role(self):
        role = aws.iam.Role(
            resource_name="access_to_ecr_for_apprunner",
            name="access_to_ecr_for_apprunner",
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
            resource_name="ECR_access_policy",
            role=role,
            policy_arn=aws.iam.Policy(
                resource_name="ECR_access_policy",
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
        return aws.apprunner.Service(
            resource_name="app-runner",
            service_name="backend_app_runner",
            source_configuration=aws.apprunner.ServiceSourceConfigurationArgs(
                authentication_configuration=aws.apprunner.ServiceSourceConfigurationAuthenticationConfigurationArgs(
                    access_role_arn=self.create_ecr_access_role().arn
                ),
                image_repository=aws.apprunner.ServiceSourceConfigurationImageRepositoryArgs(
                    image_identifier=self.ecr_repository.repository_url.apply(lambda url: f"{url}:latest"),
                    image_repository_type="ECR",
                    image_configuration=aws.apprunner.ServiceSourceConfigurationImageRepositoryImageConfigurationArgs(
                        port=3000
                    ),
                ),
                auto_deployments_enabled=self.backend_config.require_bool("app_runner_auto_deployment"),
            ),
            instance_configuration=aws.apprunner.ServiceInstanceConfigurationArgs(
                cpu=self.backend_config.require("app_runner_cpu"),
                memory=self.backend_config.require("app_runner_memory"),
            ),
            # TODO:
            # network_configuration=aws.apprunner.ServiceNetworkConfigurationArgs(
            #     ingress_configuration=aws.apprunner.ServiceNetworkConfigurationIngressConfigurationArgs(
            #         is_publicly_accessible=False
            #     ),
            #     egress_configuration=aws.apprunner.ServiceNetworkConfigurationEgressConfigurationArgs(
            #         egress_type="VPC",
            #         vpc_connector_arn="tbu",
            #     ),
            # ),
        )
