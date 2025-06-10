# OCI Service Connector Policies Generator

A Python script that automatically generates IAM policies required for OCI Service Connectors to access various OCI resources across all compartments in a tenancy.

## Description

This script traverses all compartments in an OCI tenancy and discovers resources that can be used as sources or targets for Service Connectors. It then generates the appropriate IAM policies that allow Service Connectors to access these resources.

**Supported Resources:**
- Functions (as tasks or targets)
- Log Groups (Logging Analytics)
- Monitoring Metrics
- Notification Topics
- Object Storage Buckets
- Queues
- Streams

## Prerequisites

- Python 3.6+
- OCI Python SDK
- Valid OCI configuration file (`~/.oci/config`)
- Appropriate IAM permissions to read resources across compartments

## Installation

1. Install the OCI Python SDK:
```bash
pip install oci
```

2. Ensure your OCI configuration is properly set up:
```bash
oci setup config
```

## Configuration

Before running the script, you must update the `serviceconnector_compartment_ocid` variable in the `main()` function:

```python
# Replace with the actual OCID of the compartment containing service connectors
serviceconnector_compartment_ocid = 'ocid1.compartment.oc1..example'
```

## Usage

Run the script directly:

```bash
python generate_service_connector_policies.py
```

The script will:
1. Connect to OCI using your configured credentials
2. Retrieve all compartments in your tenancy
3. Discover resources in each compartment
4. Generate appropriate policies for Service Connector access
5. Output all policies to stdout

## Example Output

```
Allow any-user to use fn-function in compartment id ocid1.compartment.oc1..example where all {request.principal.type='serviceconnector', request.principal.compartment.id='ocid1.compartment.oc1..serviceconnector'}
Allow any-user to use fn-invocation in compartment id ocid1.compartment.oc1..example where all {request.principal.type='serviceconnector', request.principal.compartment.id='ocid1.compartment.oc1..serviceconnector'}
---
Allow any-user to manage objects in compartment id ocid1.compartment.oc1..example where all {request.principal.type='serviceconnector', target.bucket.name='my-bucket', request.principal.compartment.id='ocid1.compartment.oc1..serviceconnector'}
---
```

## Policy Types Generated

### Functions
- `fn-function` and `fn-invocation` permissions for function execution

### Logging Analytics
- `loganalytics-log-group` permissions for log ingestion

### Monitoring
- `metrics` read permissions (source) and use permissions (target)

### Notifications
- `ons-topics` permissions for topic publishing

### Object Storage
- `manage objects` permissions for bucket access

### Queues
- `QUEUE_READ` and `QUEUE_CONSUME` permissions for queue processing

### Streams
- `STREAM_READ`, `STREAM_CONSUME` (source) and `stream-push` (target) permissions

## Customization

To modify the script for your specific needs:

1. **Add/Remove Resource Types**: Modify the `get_resources_in_compartment()` function
2. **Customize Policy Templates**: Edit the policy generation logic in `generate_policies()`
3. **Filter Compartments**: Add filtering logic in the `main()` function
4. **Handle Specific Resource Attributes**: Extend the resource discovery logic

## Notes

- The script uses exception handling to gracefully skip resources that cannot be accessed
- Some resource types (like metrics) are placeholders and may need customization based on your specific use case
- Generated policies follow OCI's principle of least privilege
- Review and test policies before applying them to production environments

## Error Handling

The script includes basic error handling:
- Failed resource discovery operations are silently skipped
- Empty resource lists are handled gracefully
- OCI API errors during resource enumeration are caught and ignored

## Security Considerations

- Ensure the OCI user running this script has appropriate read permissions across all compartments
- Review generated policies before implementation
- Consider using more restrictive conditions based on your security requirements
- The generated policies grant access to Service Connectors from a specific compartment only 
