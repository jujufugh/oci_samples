import oci
from oci.identity import IdentityClient
from oci.core import ComputeClient
from oci.object_storage import ObjectStorageClient
from oci.streaming import StreamAdminClient
from oci.queue import QueueAdminClient
from oci.functions import FunctionsManagementClient
from oci.logging import LoggingManagementClient
from oci.monitoring import MonitoringClient
from oci.ons import NotificationControlPlaneClient
from oci.loggingsearch import LogSearchClient

# Initialize OCI clients with default config
config = oci.config.from_file()
identity_client = IdentityClient(config)
compute_client = ComputeClient(config)
object_storage_client = ObjectStorageClient(config)
stream_admin_client = StreamAdminClient(config)
queue_admin_client = QueueAdminClient(config)
functions_client = FunctionsManagementClient(config)
logging_client = LoggingManagementClient(config)
monitoring_client = MonitoringClient(config)
notification_client = NotificationControlPlaneClient(config)
log_search_client = LogSearchClient(config)

def get_all_compartments(identity_client, tenancy_id):
    """Retrieve all compartments in the tenancy, handling pagination."""
    compartments = []
    list_compartments_response = identity_client.list_compartments(tenancy_id)
    compartments.extend(list_compartments_response.data)
    while list_compartments_response.has_next_page:
        list_compartments_response = identity_client.list_compartments(
            tenancy_id, page=list_compartments_response.next_page
        )
        compartments.extend(list_compartments_response.data)
    return compartments

def get_resources_in_compartment(compartment_id):
    """Retrieve OCIDs of resources in a given compartment."""
    resources = {}
    
    # Functions
    try:
        functions = functions_client.list_functions(compartment_id).data
        resources['functions'] = [func.id for func in functions]
    except:
        resources['functions'] = []
    
    # Log Groups (Logging Analytics)
    try:
        log_groups = logging_client.list_log_groups(compartment_id).data
        resources['log_groups'] = [lg.id for lg in log_groups]
    except:
        resources['log_groups'] = []
    
    # Metrics (Monitoring) - Placeholder, as metrics are not directly listable
    resources['metrics'] = []  # Adjust based on specific use case
    
    # Topics (Notifications)
    try:
        topics = notification_client.list_topics(compartment_id).data
        resources['topics'] = [topic.topic_id for topic in topics]
    except:
        resources['topics'] = []
    
    # Buckets (Object Storage)
    try:
        namespace = object_storage_client.get_namespace().data
        buckets = object_storage_client.list_buckets(compartment_id, namespace).data
        resources['buckets'] = [bucket.name for bucket in buckets]
    except:
        resources['buckets'] = []
    
    # Queues
    try:
        queues = queue_admin_client.list_queues(compartment_id).data
        resources['queues'] = [queue.id for queue in queues]
    except:
        resources['queues'] = []
    
    # Streams
    try:
        streams = stream_admin_client.list_streams(compartment_id).data
        resources['streams'] = [stream.id for stream in streams]
    except:
        resources['streams'] = []
    
    return resources

def generate_policies(compartment_id, resources, serviceconnector_compartment_ocid):
    """Generate default service connector policies for resources in a compartment."""
    policies = []
    
    # Functions (Task or Target)
    for func_id in resources.get('functions', []):
        policy = (
            f"Allow any-user to use fn-function in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}\n"
            f"Allow any-user to use fn-invocation in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}"
        )
        policies.append(policy)
    
    # Logging Analytics (Target)
    for log_group_id in resources.get('log_groups', []):
        policy = (
            f"Allow any-user to use loganalytics-log-group in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"target.loganalytics-log-group.id='{log_group_id}', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}"
        )
        policies.append(policy)
    
    # Monitoring (Source) - Placeholder
    for metric_compartment in resources.get('metrics', []):
        policy = (
            f"Allow any-user to read metrics in tenancy "
            f"where all {{request.principal.type='serviceconnector', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}', "
            f"target.compartment.id in ('{metric_compartment}') }}"
        )
        policies.append(policy)
    
    # Monitoring (Target) - Placeholder
    for metric_namespace in resources.get('metrics', []):
        policy = (
            f"Allow any-user to use metrics in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"target.metrics.namespace='{metric_namespace}', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}"
        )
        policies.append(policy)
    
    # Notifications (Target)
    for topic_id in resources.get('topics', []):
        policy = (
            f"Allow any-user to use ons-topics in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}"
        )
        policies.append(policy)
    
    # Object Storage (Target)
    for bucket_name in resources.get('buckets', []):
        policy = (
            f"Allow any-user to manage objects in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"target.bucket.name='{bucket_name}', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}"
        )
        policies.append(policy)
    
    # Queue (Source)
    for queue_id in resources.get('queues', []):
        policy = (
            f"Allow any-user to {{ QUEUE_READ , QUEUE_CONSUME }} in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"target.queue.id='{queue_id}', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}"
        )
        policies.append(policy)
    
    # Streaming (Source)
    for stream_id in resources.get('streams', []):
        policy = (
            f"Allow any-user to {{STREAM_READ, STREAM_CONSUME}} in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"target.stream.id='{stream_id}', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}"
        )
        policies.append(policy)
    
    # Streaming (Target)
    for stream_id in resources.get('streams', []):
        policy = (
            f"Allow any-user to use stream-push in compartment id {compartment_id} "
            f"where all {{request.principal.type='serviceconnector', "
            f"target.stream.id='{stream_id}', "
            f"request.principal.compartment.id='{serviceconnector_compartment_ocid}'}}"
        )
        policies.append(policy)
    
    return policies

def main():
    """Main function to traverse compartments and generate policies."""
    tenancy_id = config['tenancy']
    compartments = get_all_compartments(identity_client, tenancy_id)
    
    # Replace with the actual OCID of the compartment containing service connectors
    serviceconnector_compartment_ocid = 'ocid1.compartment.oc1..example'
    
    all_policies = []
    
    for compartment in compartments:
        resources = get_resources_in_compartment(compartment.id)
        policies = generate_policies(compartment.id, resources, serviceconnector_compartment_ocid)
        all_policies.extend(policies)
    
    # Print all generated policies
    for policy in all_policies:
        print(policy)
        print("---")

if __name__ == "__main__":
    main()