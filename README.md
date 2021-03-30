# GPU Finder

GPU Finder attempts to make it easier to find and provision Compute Engine Instances with GPUs.

## Why GPU Finder?

GPU quotas are not always consistent across regions and at any particular time. At peak times, there may be limited availability of GPUs in the cloud due to the high demand for their compute power. This makes finding and provisioning of GPUs difficult and time consuming.

## Prerequisites

* A GCP account and access to a service account with the permissions needed for creating instances. See the [docs](https://cloud.google.com/docs/authentication/production#passing_variable) for creating a key file and setting the GOOGLE_APPLICATION_CREDENTIALS environment variable
* A python environment with google-api-python-client==2.0.2 library installed using pip

## Using the GPU Finder

1. Download the service account key file and set the GOOGLE_APPLICATION_CREDENTIALS environment variable to authenticate with GCP APIs
2. Install the Google API client library by running the command below:
```bash
pip install -r requirements
```` 
3. Modify the `gpu-config.json` file to set the appropriate configuration parameters. In addition to the name of the machine, the important parameters to set are:
    * number_of_instances: Number of instances to create
    * machine_type: [The type of Compute Engine machine(s) to create](https://cloud.google.com/compute/docs/machine-types)
    * zone: [A list of zones to attempt to create instances in](https://cloud.google.com/compute/docs/regions-zones). To attempt all zone, leave the list blank (i.e. empty brackets [] will look for instances in all zones)
    * gpu_type: [The type of GPU to use](https://cloud.google.com/compute/docs/gpus). Note that A100s have to be used with [A2 machine types](https://cloud.google.com/compute/docs/gpus/create-vm-with-gpus#examples-add-gpu-a100), while the other GPU types can be configured with N1 machine types.
    * number_of_gpus: [The number of GPUs to attach to each instance](https://cloud.google.com/compute/docs/gpus)

| GPU Model    | Configuration Name   | Compatible Machine Types | Number of GPUs |
|--------------|----------------------|--------------------------|----------------|
| NVIDIA® A100 | nvidia-tesla-a100    | A2                       | 1, 2, 4, 8, 16 |
| NVIDIA® T4   | nvidia-tesla-t4      | N1                       | 1, 2, 4        |
| NVIDIA® V100 | nvidia-tesla-v100    | N1                       | 1, 2, 4, 8     |
| NVIDIA® P4   | nvidia-tesla-p4      | N1                       | 1, 2, 4        |
| NVIDIA® P100 | nvidia-tesla-p100    | N1                       | 1, 2, 4        |
| NVIDIA® K80  | nvidia-tesla-k80     | N1                       | 1, 2, 4, 8     |

4. Additional configuration like disk type, disk size, firewall rules, image type, image family, VPC, startup scripts, and others can be set in the configuration file too.
5. When running the script, you will see output in the logs about which regions and zones the instances will be created in, the names of instances, and whether a quota has been reached in a given region.


