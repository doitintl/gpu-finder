#!/usr/bin/env python

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example of using the Compute Engine API to create and delete instances.
Creates a new compute engine instance and uses it to apply a caption to
an image.
    https://cloud.google.com/compute/docs/tutorials/python-guide
For more information, see the README.md under /compute.
"""

import time
import json
import googleapiclient.discovery

def check_gpu_config(config):
    compute_config = config
    if compute_config['instance_config']['machine_type'].startswith('a2'):
        number_of_gpus_requested = compute_config['instance_config']['number_of_gpus']
        gpus_in_machine_type = compute_config['instance_config']['machine_type'][(compute_config['instance_config']['machine_type'].find('highgpu')+8):(len(compute_config['instance_config']['machine_type'])-1)]
        if number_of_gpus_requested != int(gpus_in_machine_type):
            raise Exception("Please match the number of GPUs parameter with the correct machine type in the config file")

def get_zone_info(compute, project):
    zone_list = []
    request = compute.zones().list(project=project)
    while request is not None:
        response = request.execute()
        for zone in response['items']:
            if zone['status'] == 'UP':
                zone_regions = {
                    'region': zone['name'][0:len(zone['name'])-2],
                    'zone': zone['name']
                }
                zone_list.append(zone_regions)
        request = compute.zones().list_next(previous_request=request, previous_response=response)
    return zone_list

def check_machine_type_and_accelerator(compute, project, machine_type, gpu_type, zones):
    zone_list = zones
    available_zones = []
    for zone in zone_list:
        request = compute.machineTypes().list(project=project, zone=zone['zone'])
        while request is not None:
            response = request.execute()
            for machine in response['items']:
                if 'accelerators' in machine and machine['name'] == machine_type and machine['accelerators'][0]['guestAcceleratorType'] == gpu_type:
                    zones_with_instances = {
                        'machine_type': machine['name'],
                        'region': zone['region'],
                        'zone': zone['zone'],
                        'guest_cpus': machine['guestCpus'],
                        'description': machine['description'],
                        'accelerators': machine['accelerators']
                    }
                    available_zones.append(zones_with_instances)
                elif machine['name'] == machine_type:
                    zones_with_instances = {
                        'machine_type': machine['name'],
                        'region': zone['region'],
                        'zone': zone['zone'],
                        'guest_cpus': machine['guestCpus'],
                        'description': machine['description']
                    }
                    available_zones.append(zones_with_instances)
            request = compute.machineTypes().list_next(previous_request=request, previous_response=response)
    if not available_zones:
        raise Exception(f"No machine types of {machine_type} are available")
    return available_zones

def get_accelerator_quota(compute, project, config, zone, requested_gpus):
    zone_list = zone
    accelerator_list = []
    for i in zone_list:
        request = compute.acceleratorTypes().list(project=project, zone=i['zone'])
        while request is not None:
            response = request.execute()
            if 'items' in response:
                for accelerator in response['items']:
                    if accelerator['name'] == config['instance_config']['gpu_type']:
                        if requested_gpus <= accelerator['maximumCardsPerInstance']:
                            accelerator_dict = {
                                "region": i['region'],
                                "zone": i['zone'],
                                "machine_type": i['machine_type'],
                                "guest_cpus": i['guest_cpus'],
                                "name": accelerator['name'],
                                "description": accelerator['description'],
                                "maximum number of GPUs per instance": accelerator['maximumCardsPerInstance']
                            }
                            accelerator_list.append(accelerator_dict)
                            print(f"{requested_gpus} GPUs requested per instance, {i['zone']} has {accelerator['name']} GPUs with a maximum of {accelerator['maximumCardsPerInstance']} per instance")
                        else:
                            print(
                                f"{requested_gpus} GPUs requested per instance, {i['zone']} doesn't have enough GPUs, with a maximum of {accelerator['maximumCardsPerInstance']} per instance")
            request = compute.acceleratorTypes().list_next(previous_request=request, previous_response=response)
    if not accelerator_list:
        raise Exception(f"No accelerator types of {config['instance_config']['gpu_type']} are available with {config['instance_config']['machine_type']} in any zone, or wrong number of GPUs requested")
    return accelerator_list

# def get_region_quotas(compute, project, regions):
#     region_list = regions
#     region_under_quota = []
#     request = compute.regions().list(project=project)
#     while request is not None:
#         response = request.execute()
#         for region in response['items']:
#             if region['name'] in region_list:
#                 region_zones = {
#                     'region': region['name'],
#                     'zones': region['zones'],
#                     'gpu_quotas': [q for q in region['quotas'] if q['metric'] ==
#                 }
#                 region_under_quota.append(region_zones)
#         return region_under_quota
#
#
# def zones_with_preferred_accelerator_type(compute, project, zone, gpu_type, number_of_gpus):
#     zone_list = []
#     for i in zone:
#         request = compute.acceleratorTypes().list(project=project, zone=i)
#         while request is not None:
#             response = request.execute()
#             filter_accelarators = [accelerator for accelerator in response['items'] if accelerator['name'] == gpu_type]
#             for accelerator in filter_accelarators:
#                 if accelerator['maximumCardsPerInstance'] >= number_of_gpus:
#                     print(f"{accelerator['maximumCardsPerInstance']} {gpu_type} GPUs per instance are available in {i}")
#                     zone_list.append(i)
#                 else:
#                     print(f"{accelerator['maximumCardsPerInstance']} {gpu_type} GPUs per instance are available in {i}, however, this is lower than the {number_of_gpus} GPUs needed per instance")
#             request = compute.acceleratorTypes().list_next(previous_request=request, previous_response=response)
#     return zone_list
#
#
# def zones_with_preferred_machine_types(compute, project, zone, machine_type):
#     zone_list = []
#     for i in zone:
#         machine_by_zone_list = []
#         request = compute.machineTypes().list(project=project, zone=i)
#         while request is not None:
#             response = request.execute()
#             filter_machines = [machine for machine in response['items'] if machine['name'] == machine_type]
#             for machine in filter_machines:
#                 print(f"{machine_type} machine type is available in {i}")
#                 machine_by_zone_list.append(machine)
#             zone_list.append(machine_by_zone_list)
#             request = compute.machineTypes().list_next(previous_request=request, previous_response=response)
#     return zone_list


def create_instance(compute, project, config, zone_list):
    compute_config = config
    regions_to_try = list({v['region'] for v in zone_list})
    created_instances = []
    instances = 0
    regions_attempted = 0
    print(f"There are {len(regions_to_try)} regions to try")
    for region in regions_to_try:
        print(f"Attempting to create instances in {region}")
        zones = [z for z in zone_list if z['region'] == region]
        print(f"There are {len(zones)} zones to try in {region}")
        zones_attempted = 0
        move_regions = 0
        for i in range(len(zones)):
            zone_config = zones[i]
            for j in range(compute_config['number_of_instances']):
                print(f"Creating instance number {instances+1} of {compute_config['number_of_instances']} in {zone_config['zone']}, zone {zones_attempted+1} out of {len(zones)} attempted.")
                image_project = compute_config['instance_config']['image_project']
                image_family = compute_config['instance_config']['image_family']
                image_response = compute.images().getFromFamily(
                    project=image_project, family=image_family).execute()
                source_disk_image = image_response['selfLink']
                instance_name = compute_config['instance_config']['name'] + '-' + str(instances+1) + '-' + zone_config['zone']
                # Configure the machine
                machine_type = f"zones/{zone_config['zone']}/machineTypes/{compute_config['instance_config']['machine_type']}"
                # startup_script = open(
                #     os.path.join(
                #         os.path.dirname(__file__), 'startup-script.sh'), 'r').read()
                # image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
                # image_caption = "Ready for dessert?"

                config = {
                    'name': instance_name,
                    'machineType': machine_type,

                    # Specify the boot disk and the image  to use as a source.
                    'disks': [
                        {
                            'kind': 'compute#attachedDisk',
                            'type': 'PERSISTENT',
                            'boot': True,
                            'mode': 'READ_WRITE',
                            'autoDelete': True,
                            'deviceName': compute_config['instance_config']['name'],
                            'initializeParams': {
                                'sourceImage': source_disk_image,
                                'diskType': f"projects/{project}/zones/{zone_config['zone']}/diskTypes/{compute_config['instance_config']['disk_type']}",
                                'diskSizeGb': compute_config['instance_config']['disk_size'],
                                'labels': {}
                            },
                            "diskEncryptionKey": {}
                        }
                    ],
                    'canIpForward': False,
                    'guestAccelerators': [
                        {
                            'acceleratorCount': compute_config['instance_config']['number_of_gpus'],
                            'acceleratorType': f"zones/{zone_config['zone']}/acceleratorTypes/{compute_config['instance_config']['gpu_type']}"
                        }
                    ],

                    'tags': {
                        "items": compute_config['instance_config']['firewall_rules']
                    },

                    # Specify a network interface with NAT to access the public
                    # internet.
                    'networkInterfaces': [{
                        'kind': 'compute#networkInterface',
                        'network': compute_config['instance_config']['network_interfaces']['network'],
                        'accessConfigs': [
                            {
                                'kind': 'compute#accessConfig',
                                'name': 'External NAT',
                                'type': 'ONE_TO_ONE_NAT',
                                'networkTier': 'PREMIUM'
                            }
                        ],
                        'aliasIpRanges': []
                    }
                    ],
                    'description': '',
                    'labels': {},
                    'scheduling': {
                        'preemptible': False,
                        'onHostMaintenance': 'TERMINATE',
                        'automaticRestart': True,
                        'nodeAffinities': []
                    },
                    'deletionProtection': False,
                    'reservationAffinity': {
                        'consumeReservationType': 'ANY_RESERVATION'
                    },
                    # Allow the instance to access cloud storage and logging.
                    'serviceAccounts': [{
                        'email': compute_config['instance_config']['identity_and_api_access']['service_account_email'],
                        'scopes': [
                            compute_config['instance_config']['identity_and_api_access']['scopes']
                        ]
                    }
                    ],
                    'shieldedInstanceConfig': {
                        'enableSecureBoot': False,
                        'enableVtpm': True,
                        'enableIntegrityMonitoring': True
                    },

                    'confidentialInstanceConfig': {
                        'enableConfidentialCompute': False
                    },

                    # Metadata is readable from the instance and allows you to
                    # pass configuration from deployment scripts to instances.
                    'metadata': {
                        'kind': 'compute#metadata',
                        'items': [],
                    }
                }

                print(f"Creating instance {instance_name}.")
                operation = compute.instances().insert(
                    project=project,
                    zone=zone_config['zone'],
                    body=config).execute()

                print('Waiting for operation to finish...')
                move_zones = 0
                while True:
                    result = compute.zoneOperations().get(
                        project=project,
                        zone=zone_config['zone'],
                        operation=operation['name']).execute()

                    if result['status'] == 'DONE':
                        print("done.")
                        if 'error' in result:
                            error_results = result['error']['errors']
                            if error_results[0]['code'] == 'QUOTA_EXCEEDED':
                                move_regions = 1
                                print(Exception(result['error']))
                            else:
                                raise Exception(result['error'])
                        else:
                            instances += 1
                            move_regions = 0
                            print(f"Success: {instance_name} created")
                            print(f"{instances} created, {compute_config['number_of_instances']-instances} more to create")
                            instance_details = {
                                "name": instance_name,
                                "zone": zone_config['zone']
                            }
                            created_instances.append(instance_details)
                        break
                if instances >= compute_config['number_of_instances']:
                    print(f"Reached the desired number of instances")
                    break
                elif move_regions == 1:
                    print(f"Quota exceeded in region {region}, moving to next region")
                    break
            if instances >= compute_config['number_of_instances']:
                break
            elif move_regions == 1:
                break
            zones_attempted += 1
        regions_attempted += 1
        if instances >= compute_config['number_of_instances']:
            break
        elif regions_attempted >= len(regions_to_try):
            print(f"All regions attempted, there are not enough resources to create the desired {compute_config['number_of_instances']} instances, {instances} created")
            break
    return(created_instances)
    time.sleep(1)

def delete_instance(compute, project, instance_details):
    instances = instance_details
    print(f"Deleting {len(instances)} instances.")
    for i in range(len(instances)):
        instance = instances[i]
        zone = instance["zone"]
        name = instance["name"]

        print(f"Deleting instance {name}.")
        operation = compute.instances().delete(
            project=project,
            zone=zone,
            instance=name).execute()

        print('Waiting for operation to finish...')
        while True:
            result = compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation['name']).execute()

            if result['status'] == 'DONE':
                print("done.")
                if 'error' in result:
                    raise Exception(result['error'])
                break

def create_instance_test(compute, project, config, zone, requested_gpus):
    zone_list = zone
    accelerator_list = []
    for i in zone_list:
        request = compute.acceleratorTypes().list(project=project, zone=i['zone'])
        while request is not None:
            response = request.execute()
            if 'items' in response:
                for accelerator in response['items']:
                    print(accelerator)


def main(gpu_config, wait=True):
    compute = googleapiclient.discovery.build('compute', 'v1')
    if gpu_config["instance_config"]["zone"]:
        print(f"Processing selected zones from {gpu_config['instance_config']['zone']}")
        zone_info = get_zone_info(compute, gpu_config["project_id"])
        compute_zones = [z for z in zone_info if z['zone'] in gpu_config['instance_config']['zone']]
    else:
        print("Processing all zones")
        compute_zones = get_zone_info(compute, gpu_config["project_id"])
    check_gpu_config(gpu_config)
    # distinct_zones = list({v['zone'] for v in compute_zones})
    available_zones = check_machine_type_and_accelerator(compute, gpu_config["project_id"], gpu_config["instance_config"]["machine_type"], gpu_config["instance_config"]["gpu_type"], compute_zones)
    accelerators = get_accelerator_quota(compute, gpu_config["project_id"], gpu_config, available_zones, gpu_config["instance_config"]["number_of_gpus"])
    available_regions = list({v['region'] for v in available_zones})
    if available_regions:
        print(f"Machine type {gpu_config['instance_config']['machine_type']} is available in the following regions: {available_regions}")
        instance_details = create_instance(compute, gpu_config["project_id"], gpu_config, accelerators)
        if wait:
            print("hit enter to delete instances")
            input()
        delete_instance(compute, gpu_config["project_id"], instance_details)
    else:
        print(f"No regions available with the instance configuration {gpu_config['instance_config']['machine_type']} machine type and {gpu_config['instance_config']['gpu_type']} GPU type")

if __name__ == '__main__':
    with open('gpu-config.json', 'r') as f:
        gpu_config = json.load(f)
    main(gpu_config)