"""An AWS Python Pulumi program - App runner for Backend"""

import ast
import time

import pulumi
import pulumi_aws as aws


class Backend:
    def __init__(self):
        self.common_config = pulumi.Config("WeatherAlerting")
        self.backend_config = pulumi.Config("backend")
        self.account_id = self.common_config.require_secret_int("account_id")
        self.app_runner_uri = None
        self.list_of_vpc_subnets = ast.literal_eval(self.common_config.require("default_subnets_list"))

    def grant_access_rights_for_gh_actions(self, repo_name, github_open_id_provider):
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
                                values=[f"repo:{self.backend_config.require('repository')}:*"],
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

    def create_app_runner_vpc_connector(self):
        return aws.apprunner.VpcConnector(
            "AppRunnerVPCConnector",
            vpc_connector_name="AppRunnerVPCConnector",
            security_groups=[self.common_config.require("default_security_group")],
            subnets=[
                self.list_of_vpc_subnets[0],
                self.list_of_vpc_subnets[1],
                self.list_of_vpc_subnets[2],
            ],
        )

    def create_instance_role_arn(self):
        role = aws.iam.Role(
            resource_name="AppRunnerAccessToInstance",
            name="AppRunnerAccessToInstance",
            assume_role_policy=aws.iam.get_policy_document(
                statements=[
                    aws.iam.GetPolicyDocumentStatementArgs(
                        actions=["sts:AssumeRole"],
                        effect="Allow",
                        principals=[
                            aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                                type="Service",
                                identifiers=["tasks.apprunner.amazonaws.com"],
                            )
                        ],
                    )
                ]
            ).json,
        )
        # Attach AppRunner Policy to Instance role.
        aws.iam.RolePolicyAttachment(
            resource_name="AppRunnerAccessPolicy",
            role=role,
            policy_arn="arn:aws:iam::aws:policy/AWSAppRunnerFullAccess",
        )
        return role

    def create_app_runner(self, database_uri, database_username, database_password):
        app_runner = aws.apprunner.Service(
            resource_name="AppRunnerService",
            service_name="AppRunnerService",
            auto_scaling_configuration_arn=aws.apprunner.AutoScalingConfigurationVersion(
                resource_name="AppRunnerAutoScalingConfig",
                auto_scaling_configuration_name="AppRunnerAutoScalingConfig",
                min_size=1,
                max_size=self.backend_config.require_int("auto_scaling_max_instances"),
            ).arn,
            source_configuration=aws.apprunner.ServiceSourceConfigurationArgs(
                authentication_configuration=aws.apprunner.ServiceSourceConfigurationAuthenticationConfigurationArgs(
                    # Workaround due to pulumi-aws bug: https://github.com/pulumi/pulumi-aws/issues/1697
                    access_role_arn=self.create_ecr_access_role().arn.apply(lambda arn: time.sleep(10) or arn)
                ),
                image_repository=aws.apprunner.ServiceSourceConfigurationImageRepositoryArgs(
                    image_identifier=f"{self.backend_config.require('ecr_uri')}:latest",
                    image_repository_type="ECR",
                    image_configuration=aws.apprunner.ServiceSourceConfigurationImageRepositoryImageConfigurationArgs(
                        port=self.backend_config.require_int("port"),
                        runtime_environment_variables=pulumi.Output.all(
                            database_uri, database_username, database_password
                        ).apply(
                            lambda args: {
                                "DB_HOST": f"{args[0]}",
                                "DB_USERNAME": f"{args[1]}",
                                "DB_PASSWORD": f"{args[2]}",
                                "DB_SSL": "true",
                                "DB_SSL_CA_FILE_PATH": "/etc/ssl/rds-combined-ca-bundle.pem",
                            }
                        ),
                    ),
                ),
                auto_deployments_enabled=self.backend_config.require_bool("app_runner_auto_deployment"),
            ),
            network_configuration=aws.apprunner.ServiceNetworkConfigurationArgs(
                egress_configuration=aws.apprunner.ServiceNetworkConfigurationEgressConfigurationArgs(
                    egress_type="VPC",
                    vpc_connector_arn=self.create_app_runner_vpc_connector().arn,
                )
            ),
            instance_configuration=aws.apprunner.ServiceInstanceConfigurationArgs(
                cpu=self.backend_config.require_int("app_runner_cpu"),
                memory=self.backend_config.require_int("app_runner_memory"),
                instance_role_arn=self.create_instance_role_arn().arn,
            ),
        )
        self.app_runner_uri = app_runner.service_url
