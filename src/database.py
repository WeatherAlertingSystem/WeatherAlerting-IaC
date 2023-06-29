"""An AWS Python Pulumi program - MongoDB Database for backend operations"""


import pulumi
import pulumi_aws as aws


class Database:
    def __init__(self):
        self.common_config = pulumi.Config("WeatherAlerting")
        self.database_config = pulumi.Config("database")
        self.database_username = self.database_config.require_secret("username")
        self.database_password = self.database_config.require_secret("password")
        self.database_uri = None
        self.database_subnet_group = None

    def create_db_subnet_group(self, subnet_ids):
        subnet_group = aws.docdb.SubnetGroup("weather-alerting-subnet-group", subnet_ids=subnet_ids)
        return subnet_group.name

    def create_documentDB(self, db_subnet_group_name):
        db_cluster = aws.docdb.Cluster(
            "MongoDbCluster",
            backup_retention_period=30,
            cluster_identifier="my-docdb-cluster",
            engine="docdb",
            engine_version=self.database_config.require("mongodb_version"),
            master_username=self.database_username,
            master_password=self.database_password,
            skip_final_snapshot=True,
            deletion_protection=False,
            db_subnet_group_name=db_subnet_group_name,
        )
        cluster_instances = []
        instances_number = self.database_config.require_int("instances_number")

        for instance_index in range(instances_number):
            cluster_instances.append(
                aws.docdb.ClusterInstance(
                    f"cluster-instance-{instance_index}",
                    identifier=f"cluster-instance-{instance_index}",
                    cluster_identifier=db_cluster.id,
                    instance_class=self.database_config.require("instance_class"),
                )
            )
        self.database_uri = db_cluster.endpoint
