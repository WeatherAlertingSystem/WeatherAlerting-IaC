import pulumi_aws as aws


def create_gh_open_id_provider():
    return aws.iam.OpenIdConnectProvider(
        "GithubProvider",
        client_id_lists=["sts.amazonaws.com"],
        thumbprint_lists=["6938fd4d98bab03faadb97b34396831e3780aea1"],
        url="https://token.actions.githubusercontent.com",
    )
