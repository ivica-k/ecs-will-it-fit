# ecs-will-it-fit

`ecs-will-it-fit`, or `willy` in short, is a CLI tool that helps you answer the question: "Will this ECS service fit on
my ECS cluster backed by EC2 instances?". It does so by mimicking<sup>[1](#mimicking)</sup> the selection process that
the ECS scheduler performs while selecting suitable container instances for your task.

`willy` is useful only if your cluster does _not_ have [auto-scaling using capacity providers](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-auto-scaling.html) enabled (**it should**).

## Usage examples

TODO

## Why use willy?

### Speed

ECS scheduler tries to deploy your service in a robust and safe way. This can take time, depending on several configuration
options. Check out Nathan's amazing article on [Speeding up Amazon ECS container deployments](https://nathanpeck.com/speeding-up-amazon-ecs-container-deployments/)
for details.

`willy` perform its checks at a point in time and its answer represents the possibility to fit all the tasks in your
service on the cluster _at that time_. All tasks might fit on the cluster five seconds later, depending on the state of
the cluster and `willy` can't predict that.

`willy` sacrifices being 100% correct five seconds from now in favor of providing a quick answer now.

### Details

ECS deployment will often fail with: `The closest matching container-instance is missing an attribute required by your task`
which lacks details.

`willy` does it differently:

```text
Service 'my-service' can not run on the 'my-cluster' cluster. There are no container instances that have the attributes
required by the task definition. Attribute(s) missing or incorrect on the container instance:

'ecs.vpc-id with value vpc-a1b2c3d4e5f6'"
```

## Implemented features

[From ECS docs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-placement.html#ec2-launch-type):

```
When Amazon ECS places tasks, it uses the following process to select container instances:

1. Identify the container instances that satisfy the CPU, GPU, memory, and port requirements in the task definition.
2. Identify the container instances that satisfy the task placement constraints.
3. Identify the container instances that satisfy the task placement strategies.
4. Select the container instances for task placement.
```

`willy` implements a validator for each of the steps listed above

| Feature               |    Implemented?    |     Has tests?     |
|-----------------------|:------------------:|:------------------:|
| CPU validation        | :heavy_check_mark: | :heavy_check_mark: |
| Memory validation     | :heavy_check_mark: | :heavy_check_mark: |
| Port validation       | :heavy_check_mark: |        :x:         |
| GPU validation        |        :x:         |        :x:         |
| Attributes validation | :white_check_mark: | :white_check_mark: |

## Caveats and known limitations

### Mimicking

Exact technical details of the container instance selection process are not publicly available. `willy` approximates the
process from observations made while scheduling services on ECS.

### Speed vs. accuracy

`willy` perform its checks at a point in time and its answer represents the possibility to fit all the tasks in your
service on the cluster _at that time_. All tasks might fit on the cluster five seconds later, depending on the state of
the cluster and `willy` can't predict that.

`willy` sacrifices being 100% correct five seconds from now in favor of providing a quick answer now.