import argparse


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Checks whether an ECS service can fit on an ECS (EC2) cluster."
    )
    parser.add_argument(
        "-c", "--cluster", help="Name of the ECS cluster.", required=True
    )
    parser.add_argument(
        "-s", "--service", help="Name of the ECS service.", required=True
    )
    parser.add_argument(
        "--verbose",
        "-V",
        default=False,
        required=False,
        action=argparse.BooleanOptionalAction,
        type=bool,
        help="Enable verbose output, with EC2 instance information and other details.",
    )

    return parser.parse_args()

def cli():
    args = _parse_args()

    cluster = args.cluster
    service = args.service
    verbose = args.verbose

    from willy.main import will_it_fit

    will_it_fit(cluster_name=cluster, service_name=service, verbose=verbose)

if __name__ == "__main__":
    cli()
