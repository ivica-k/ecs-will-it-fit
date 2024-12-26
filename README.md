# ecs-will-it-fit

`ecs-will-it-fit`, or `willy` in short, is a CLI tool that helps you answer the question: "Will this ECS service fit on
my ECS cluster backed by EC2 instances?". It does so by mimicking<sup>[1](#mimicking)</sup> the selection process that
the ECS scheduler performs while selecting suitable container instances for your service.

`willy` is useful only if your cluster does _not_ have [auto-scaling using capacity providers](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-auto-scaling.html) enabled
(**it should**).

<!-- TOC -->
* [ecs-will-it-fit](#ecs-will-it-fit)
  * [Usage examples](#usage-examples)
  * [Why use willy?](#why-use-willy)
    * [Speed](#speed)
    * [Details](#details)
  * [Implemented features](#implemented-features)
  * [Caveats and known limitations](#caveats-and-known-limitations)
    * [Mimicking](#mimicking)
    * [Speed vs. accuracy](#speed-vs-accuracy)
    * [Task placement constraints](#task-placement-constraints)
<!-- TOC -->

## Usage examples

TODO

## Why use willy?

### Speed

Simply put, `willy` sacrifices being 100% correct five seconds from now in favor of providing a quick answer _now_.

ECS scheduler tries to deploy your service in a robust and safe way. This can take time, depending on several configuration
options. Check out Nathan's amazing article on [Speeding up Amazon ECS container deployments](https://nathanpeck.com/speeding-up-amazon-ecs-container-deployments/)
for details.

`willy` perform its checks at a point in time and its answer represents the possibility to fit all the tasks in your
service on the cluster _at that time_. Those tasks might fit on the cluster five seconds later, depending on the state
of the cluster and `willy` can't predict that.

### Details

If an ECS deployment fails because of a missing attribute, the deployment event will state something similar to:

```
The closest matching container-instance is missing an attribute required by your task
```

which lacks details.

If an ECS deployment fails because of lack of CPU resources the deployment event does a better job at providing details:

```text
Service my-service was unable to place a task because no container instance met all of its requirements.
The closest matching container-instance 48fccf62981f4fc2b53e62233a586fe8 has insufficient CPU units available.
```

`willy` does it differently when reporting missing attributes:

```text
Service 'my-service' can not run on the 'my-cluster' cluster. There are no container instances that have the attributes
required by the task definition. Attribute(s) missing or incorrect on the container instance:

'ecs.vpc-id' with value 'vpc-a1b2c3d4e5f6'"
```

## Implemented features

Task placement process on Amazon ECS - [source](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-placement.html#ec2-launch-type):

```
When Amazon ECS places tasks, it uses the following process to select container instances:

1. Identify the container instances that satisfy the CPU, GPU, memory, and port requirements in the task definition.
2. Identify the container instances that satisfy the task placement constraints.
3. Identify the container instances that satisfy the task placement strategies.
4. Select the container instances for task placement.
```

`willy` implements a validator for each of the steps listed above

| Identify the container instances that satisfy the... | `willy` feature      | Implemented?                                                  | Has tests?         |
|------------------------------------------------------|----------------------|---------------------------------------------------------------|--------------------|
| CPU requirements                                     | CPU validator        | :white_check_mark:                                            | :white_check_mark: |
| Memory requirements                                  | Memory validator     | :white_check_mark:                                            | :white_check_mark: |
| Port requirements                                    | Network validator    | :white_check_mark:                                            | :x:                |
| GPU requirements                                     | Attributes validator | :x:                                                           | :x:                |
| Task placement constraints                           | Attributes validator | :white_check_mark:<sup>[2](#task-placement-constraints)</sup> | :white_check_mark: |

## Caveats and known limitations

### Mimicking

Exact technical details of the container instance selection process are not publicly available. `willy` approximates the
process from observations made while scheduling services on ECS.

### Speed vs. accuracy

`willy` sacrifices being 100% correct five seconds from now in favor of providing a quick answer _now_.

`willy` perform its checks at a point in time and its answer represents the possibility to fit all the tasks in your
service on the cluster _at that time_. All tasks might fit on the cluster five seconds later, depending on the state of
the cluster and `willy` can't predict that.

### Task placement constraints

Implementation of all [operators supported by ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-query-language.html)
is not complete.

| Operator               | Description                | Implemented?       |
|------------------------|----------------------------|--------------------|
| ==, equals             | String equality            | :white-check-mark: |
| !=, not_equals         | String inequality          | :x:                |
| >, greater_than        | Greater than               | :x:                |
| >=, greater_than_equal | Greater than or equal to   | :x:                |
| <, less_than           | Less than                  | :x:                |
| <=, less_than_equal    | Less than or equal to      | :x:                |
| exists                 | Subject exists             | :white-check-mark: |
| !exists, not_exists    | Subject doesn't exist      | :x:                |
| in                     | Value in argument list     | :white-check-mark: |
| !in, not_in            | Value not in argument list | :x:                |
| =~, matches            | Pattern match              | :x:                |
| !~, not_matches        | Pattern mismatch           | :x:                |