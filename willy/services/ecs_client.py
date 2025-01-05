import boto3

ECS_CLIENT = None


def get_ecs_client():
    global ECS_CLIENT

    if ECS_CLIENT:
        return ECS_CLIENT

    else:
        session = boto3.session.Session()
        ECS_CLIENT = session.client("ecs")

        return ECS_CLIENT
