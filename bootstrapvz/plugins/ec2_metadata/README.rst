ami-info
----------
This plugin collects metadata about the created AMI and writes the
information in a file.

Settings
~~~~~~~~
- ``path``: Path for the information file
  ``optional``
- ``s3_bucket``: S3 bucket to write the information. File will be named <ami_id>.json
  ``optional``
- ``s3_prefix``: Prefix for S3 key
  ``optional``
