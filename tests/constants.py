all_attributes = [
    {"name": "ecs.cpu-architecture", "value": "x86_64"},
    {"name": "ecs.os-family", "value": "LINUX"},
    {"name": "ecs.availability-zone", "value": "eu-central-1a"},
    {"name": "ecs.instance-type", "value": "t2.small"},
    {"name": "ecs.subnet-id", "value": "subnet-0a1710c3328d7ecd1"},
    {"name": "ecs.vpc-id", "value": "vpc-04c4656e20f1ff7e7"},
    {"name": "ecs.ami-id", "value": "ami-06d198da422b4d577"},
    {"name": "ecs.os-type", "value": "linux"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.33"},
    {"name": "com.amazonaws.ecs.capability.logging-driver.fluentd"},
    {"name": "com.amazonaws.ecs.capability.privileged-container"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.28"},
    {"name": "ecs.capability.secrets.asm.environment-variables"},
    {"name": "ecs.capability.env-files.s3"},
    {"name": "ecs.capability.secrets.ssm.bootstrap.log-driver"},
    {"name": "ecs.capability.firelens.fluentbit"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.23"},
    {"name": "ecs.capability.docker-plugin.local"},
    {"name": "ecs.capability.external"},
    {"name": "com.amazonaws.ecs.capability.logging-driver.json-file"},
    {"name": "com.amazonaws.ecs.capability.logging-driver.syslog"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.34"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.21"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.38"},
    {"name": "ecs.capability.ecr-endpoint"},
    {"name": "com.amazonaws.ecs.capability.task-iam-role"},
    {"name": "ecs.capability.execution-role-awslogs"},
    {"name": "ecs.capability.private-registry-authentication.secretsmanager"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.24"},
    {"name": "ecs.capability.container-ordering"},
    {"name": "ecs.capability.storage.ebs-task-volume-attach"},
    {"name": "ecs.capability.efsAuth"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.30"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.20"},
    {"name": "ecs.capability.secrets.asm.bootstrap.log-driver"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.25"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.26"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.17"},
    {"name": "com.amazonaws.ecs.capability.ecr-auth"},
    {"name": "ecs.capability.task-cpu-mem-limit"},
    {"name": "ecs.capability.task-eni"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.36"},
    {"name": "ecs.capability.task-eni-trunking"},
    {"name": "ecs.awsvpc-trunk-id", "value": "a6148e89-0416-415d-97e0-f23d18e134a4"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.43"},
    {"name": "ecs.capability.firelens.options.config.file"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"},
    {"name": "com.amazonaws.ecs.capability.task-iam-role-network-host"},
    {"name": "ecs.capability.branch-cni-plugin-version unknown-"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.44"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.31"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.32"},
    {"name": "ecs.capability.firelens.fluentd"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.35"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.29"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"},
    {"name": "ecs.capability.task-eni-block-instance-metadata"},
    {"name": "com.amazonaws.ecs.capability.logging-driver.awsfirelens"},
    {"name": "ecs.capability.container-health-check"},
    {"name": "ecs.capability.network.container-port-range"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.22"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.37"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.40"},
    {"name": "ecs.capability.efs"},
    {"name": "ecs.capability.execute-command"},
    {"name": "ecs.capability.service-connect-v1"},
    {"name": "ecs.capability.secrets.ssm.environment-variables"},
    {"name": "ecs.capability.docker-plugin.amazon-ecs-volume-plugin"},
    {"name": "ecs.capability.task-eia.optimized-cpu"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.27"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.39"},
    {"name": "ecs.capability.task-eia"},
    {"name": "ecs.capability.increased-task-cpu-limit"},
    {"name": "ecs.capability.cni-plugin-version unknown-"},
    {"name": "ecs.capability.full-sync"},
    {"name": "com.amazonaws.ecs.capability.logging-driver.awslogs"},
    {"name": "ecs.capability.firelens.options.config.s3"},
    {"name": "ecs.capability.logging-driver.awsfirelens.log-driver-buffer-limit"},
    {"name": "ecs.capability.execution-role-ecr-pull"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.41"},
    {"name": "ecs.capability.task-eni.ipv6"},
    {"name": "ecs.capability.pid-ipc-namespace-sharing"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.42"},
    {"name": "ecs.capability.aws-appmesh"},
    {"name": "com.amazonaws.ecs.capability.logging-driver.none"},
]

just_enough_attributes = [
    {"name": "com.amazonaws.ecs.capability.ecr-auth"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"},
    {"name": "ecs.capability.secrets.asm.environment-variables"},
    {"name": "com.amazonaws.ecs.capability.logging-driver.journald"},
    {"name": "com.amazonaws.ecs.capability.task-iam-role"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.25"},
    {"name": "ecs.capability.execution-role-ecr-pull"},
    {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"},
    {"name": "ecs.capability.task-eni"},
]