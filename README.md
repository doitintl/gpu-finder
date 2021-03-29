# GPU Finder

GPU Finder attempts to make it easier to find and provision Compute Engine Instances with GPUs.

## Why GPU Finder?

GPU quotas are not always consistent across regions and at any given time. At peak times, there may be limited availability of GPUs in the cloud due to the high demand for their compute power. This makes finding and provisioning of GPUs difficult and time consuming.

## Prerequisites

* A GCP account and access to a service account with the permissions needed for creating instances. See the [docs](https://cloud.google.com/docs/authentication/production#passing_variable) for creating a key file and setting the GOOGLE_APPLICATION_CREDENTIALS environment variable
* A python environment with google-api-python-client==2.0.2 library installed using pip

## Using the GPU Finder

1. Download the service account key file and set the GOOGLE_APPLICATION_CREDENTIALS environment variable to authenticate with GCP APIs
2. Use 

```bash
pip install -r requirements
```` 
to install the Google API client library

