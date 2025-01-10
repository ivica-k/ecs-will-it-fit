# ecs-will-it-fit

<p>
  <img width="64" src="https://github.com/ivica-k/ecs-will-it-fit/blob/main/img/willy_512.png?raw=true" alt="Heeeeere's Willy!"/>
</p>

`willy` (short for `ecs-will-it-fit`) is a CLI tool that helps you answer the question: "Will this ECS service fit on
my ECS cluster backed by EC2 instances?". It does so by mimicking<sup>[1](#mimicking)</sup> the selection process that
the ECS scheduler performs while selecting suitable container instances for your service.

`willy` is useful only if your cluster does _not_ have [auto-scaling using capacity providers](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-auto-scaling.html) enabled
(**it should**).

<!-- TOC -->
* [ecs-will-it-fit](#ecs-will-it-fit)
  * [Installation](#installation)
    * [Authentication](#authentication)
  * [Usage examples](#usage-examples)
      * [CPU units](#cpu-units)
      * [Memory](#memory)
      * [Ports](#ports)
      * [Task placement constraints (attributes)](#task-placement-constraints-attributes)
  * [Why use willy?](#why-use-willy)
    * [Speed](#speed)
    * [Details](#details)
  * [Implemented features](#implemented-features)
  * [Caveats and known limitations](#caveats-and-known-limitations)
    * [Mimicking](#mimicking)
    * [Speed vs. accuracy](#speed-vs-accuracy)
    * [Task placement constraints](#task-placement-constraints)
<!-- TOC -->

## Installation

Install from GitHub
```shell
pip install pip@git+https://github.com/ivica-k/ecs-will-it-fit
```

### Authentication

`willy` supports the default [authentication mechanism of boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html).
The read-only API calls it performs to AWS ECS require the following IAM permissions: 

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecs:DescribeClusters",
                "ecs:ListContainerInstances",
                "ecs:DescribeContainerInstances",
                "ecs:DescribeServices",
                "ecs:DescribeTaskDefinition"
            ],
            "Resource": "*"
        }
    ]
}
```

## Usage examples

General help:

```text
$ willy -h
usage: willy [-h] -c CLUSTER -s SERVICE [--verbose | --no-verbose | -V]

Checks whether an ECS service can fit on an ECS (EC2) cluster.

optional arguments:
  -h, --help            show this help message and exit
  -c CLUSTER, --cluster CLUSTER
                        Name of the ECS cluster.
  -s SERVICE, --service SERVICE
                        Name of the ECS service.
  --verbose, --no-verbose, -V
                        Enable verbose output. Contains EC2 instance information and other details. (default: False)
```

#### CPU units

Happy path, terse output:

```text
$ willy --service my-service --cluster my-cluster
Service 'my-service' can be scheduled on the 'my-cluster' cluster.
```

Happy path, verbose output:

```text
$ willy --service my-service --cluster my-cluster --verbose
Service 'my-service' can be scheduled on the 'my-cluster' cluster.

Container instances on which service 'my-service' can be scheduled:

        Instance ID |   CPU remaining |       CPU total | Memory remaining |    Memory total |
------------------- | --------------- | --------------- | ---------------- | --------------- |
i-abcdefgh123456789 |            1792 |            2048 |           15231  |           15743 |
i-hgfedcba987654321 |            1792 |            2048 |           15231  |           15743 |
i-hgfedcba123456789 |             512 |            2048 |            8575  |           15743 |
```

Unhappy path, terse output, not enough CPU units:

```text
$ willy -s my-service -c my-cluster --verbose
Service 'my-service' can not run on the 'my-cluster' cluster. Number of required CPU units is 3072 but the cluster
has 2048 CPU units available across 2 container instances.
```

Unhappy path, verbose output, not enough CPU units:

```text
$ willy -s my-service -c my-cluster --verbose
Service 'my-service' can not run on the 'my-cluster' cluster. There are no container instances that meet the hardware
requirements of 3072 CPU units.

Container instances incapable of running the service:

        Instance ID |   CPU remaining |       CPU total | Memory remaining |    Memory total |
------------------- | --------------- | --------------- | ---------------- | --------------- |
i-abcdefgh123456789 |            1792 |            2048 |           15231  |           15743 |
i-hgfedcba987654321 |            1792 |            2048 |           15231  |           15743 |
i-hgfedcba123456789 |             512 |            2048 |            8575  |           15743 |
```

#### Memory

Unhappy path, terse output, not enough memory:

```text
$ willy -s my-service -c my-cluster
Service 'my-service' can not run on the 'my-cluster' cluster. Number of required memory units is 1024 but the
cluster has 256 memory units available across 2 container instance(s).
```

Unhappy path, verbose output, not enough memory:

```text
$ willy -s my-service -c my-cluster --verbose
Service 'my-service' can not run on the 'my-cluster' cluster. There are no container instances that meet the
hardware requirements of 1024 memory units.

Container instances incapable of running the task definition:

        Instance ID |   CPU remaining |       CPU total | Memory remaining |    Memory total |
------------------- | --------------- | --------------- | ---------------- | --------------- |
i-abcdefgh123456789 |            1792 |            2048 |             512  |           15743 |
i-hgfedcba987654321 |            1792 |            2048 |             512  |           15743 |
i-hgfedcba123456789 |             512 |            2048 |             512  |           15743 |
```

#### Ports

Unhappy path, terse output, port(s) taken:

```text
$ willy -s my-service -c my-cluster
Service 'my-service' can not run on the 'my-cluster' cluster. The service requires ports [21, 22] that are used on
all container instances in the cluster.
```

Unhappy path, verbose output, port(s) taken:

```text
$ willy -s my-service -c my-cluster --verbose
Service 'my-service' can not run on the 'my-cluster' cluster. The service requires ports [21, 22] that are used on
all container instances in the cluster.

Container instances incapable of running the task definition:

        Instance ID | Used ports (TCP) |Used ports (UDP) |
------------------- | ---------------- | --------------- |
i-abcdefgh123456789 |           22, 53 |                 |
i-hgfedcba987654321 |           22, 53 |                 |
```

#### Task placement constraints (attributes)

Unhappy path, terse output, wrong instance type placement constraint:

```text
$ willy -s my-service -c my-cluster --verbose
 Service 'my-service' can not run on the 'my-cluster' cluster. There are no container instances that have the 
attribute(s) required by the task definition.
```

Unhappy path, verbose output, wrong instance type placement constraint:

```text
$ willy -s my-service -c my-cluster --verbose
Service 'my-service' can not run on the 'my-cluster' cluster. There are no container instances that have the
attribute(s) required by the task definition.

Missing attribute(s):

attribute:ecs.instance-type==t2.nano
```

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
| ==, equals             | String equality            | :white_check_mark: |
| !=, not_equals         | String inequality          | :x:                |
| >, greater_than        | Greater than               | :x:                |
| >=, greater_than_equal | Greater than or equal to   | :x:                |
| <, less_than           | Less than                  | :x:                |
| <=, less_than_equal    | Less than or equal to      | :x:                |
| exists                 | Subject exists             | :white_check_mark: |
| !exists, not_exists    | Subject doesn't exist      | :x:                |
| in                     | Value in argument list     | :white_check_mark: |
| !in, not_in            | Value not in argument list | :x:                |
| =~, matches            | Pattern match              | :x:                |
| !~, not_matches        | Pattern mismatch           | :x:                |