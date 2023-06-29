"""An AWS Python Pulumi program - VPC, NAT"""

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx


class Networking:
    def __init__(self):
        self.common_config = pulumi.Config("WeatherAlerting")

    def create_vpc(self):
        vpc = awsx.ec2.Vpc(
            "weather-alerting",
            nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
                strategy=awsx.ec2.NatGatewayStrategy.SINGLE,
            ),
        )
        self.vpc = vpc
        return vpc

    def create_dafault_sg(self):
        default = aws.ec2.DefaultSecurityGroup(
            "weather-alerting-vpc-default-sg",
            vpc_id=self.vpc.vpc_id,
            ingress=[
                aws.ec2.DefaultSecurityGroupIngressArgs(
                    protocol="-1",
                    self=True,
                    from_port=0,
                    to_port=0,
                )
            ],
            egress=[
                aws.ec2.DefaultSecurityGroupEgressArgs(
                    from_port=0,
                    to_port=0,
                    protocol="-1",
                    cidr_blocks=["0.0.0.0/0"],
                )
            ],
        )
        return default
