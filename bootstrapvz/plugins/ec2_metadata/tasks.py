import boto3
import json
import logging
import re
from bootstrapvz.base import Task
from bootstrapvz.common import phases
from bootstrapvz.providers.ec2.tasks import ami
from bootstrapvz.common.tools import log_check_call


class AddPackages(Task):
    description = 'Adding python-pip'
    phase = phases.preparation

    @classmethod
    def run(cls, info):
        info.packages.add('python-pip')
        info.packages.add('python3-pip')


class QueryPackages(Task):
    description = 'Query packages installed in the AMI'
    phase = phases.system_cleaning

    @classmethod
    def run(cls, info):
        from bootstrapvz.common.tools import log_check_call
        command = [ "chroot %s dpkg-query -W" % (info.root) ]
        packages = log_check_call(command, shell=True)
        info._ec2_metadata['packages'] = packages


class QueryGems(Task):
    description = 'Query gems installed in the AMI'
    phase = phases.system_cleaning

    @classmethod
    def run(cls, info):
        from bootstrapvz.common.tools import log_check_call
        command = [ "chroot %s gem list" % (info.root) ]
        gems = log_check_call(command, shell=True)
        info._ec2_metadata['gems'] = gems


class QueryPips(Task):
    description = 'Query pips installed in the AMI'
    phase = phases.system_cleaning

    @classmethod
    def run(cls, info):
        from bootstrapvz.common.tools import log_check_call
        command = [ "chroot %s pip list --format freeze" % (info.root) ]
        pips = log_check_call(command, shell=True)
        info._ec2_metadata['pips'] = pips

        command3 = [ "chroot %s pip3 list --format freeze" % (info.root) ]
        pips3 = log_check_call(command, shell=True)
        info._ec2_metadata['pips3'] = pips3


class WriteAMIMetadata(Task):
    description = 'Write AMI ID to file'
    phase = phases.image_registration
    predecessors = [ami.RegisterAMI]

    @classmethod
    def run(cls, info):
        ami_id = info._ec2['image']['ImageId']

        data = {}
        data['ami_id'] = ami_id
        data['packages'] = {}
        data['gems'] = {}
        data['pips'] = {}
        data['pips3'] = {}
        data['tags'] = {}

        # Package list returned by dpkg-query -W has package name and version
        # separated by a tab
        for line in info._ec2_metadata['packages']:
            l = line.split("\t")
            data['packages'][l[0]] = l[1]

        # Gem list returned by gem list has format "package (version, version)"
        for line in info._ec2_metadata['gems']:
            matches = re.findall(r'(.*?)\s+\((.*?)\)', line)

            for match in matches:
                name = match[0]
                versions = []

                for version in match[1].split(","):
                    versions.append(version.strip())

                data['gems'][name] = versions

        # Gem list returned by pip(3) list has format "package    version"
        for line in info._ec2_metadata['pips']:
            matches = re.findall(r'(.*?)==(.*)', line)

            for match in matches:
                name = match[0]
                versions = []

                for version in match[1].split(","):
                    versions.append(version.strip())

                data['pips'][name] = versions

        for line in info._ec2_metadata['pips3']:
            matches = re.findall(r'(.*?)==(.*)', line)

            for match in matches:
                name = match[0]
                versions = []

                for version in match[1].split(","):
                    versions.append(version.strip())

                data['pips3'][name] = versions

        # Setting up tags on the AMI
        if 'tags' in info.manifest.data:
            raw_tags = info.manifest.data['tags']

            for k, v in raw_tags.items():
                data['tags'][k] = v

        content = json.dumps(data)

        if 'path' in info.manifest.plugins['ec2_metadata']:
            path = info.manifest.plugins['ec2_metadata']['path']
            f = open(path, 'w')
            f.write(content)
            f.close()

        if 's3_bucket' in info.manifest.plugins['ec2_metadata']:
            bucket_name = info.manifest.plugins['ec2_metadata']['s3_bucket']
            prefix = info.manifest.plugins['ec2_metadata']['s3_prefix'] if 's3_prefix' in info.manifest.plugins['ec2_metadata'] else ""

            key = "%s%s.json" % (prefix, ami_id)

            s3 = boto3.resource('s3')
            s3.Bucket(bucket_name).put_object(Key=key, Body=content)
