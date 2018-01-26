from bootstrapvz.base import Task
from bootstrapvz.common import phases
from bootstrapvz.common.tasks import apt
from bootstrapvz.common.tools import log_check_call
import os


class S3BootstrapPackages(Task):
    description = 'Add apt repo support packages to bootstrap installation'
    phase = phases.preparation

    @classmethod
    def run(cls, info):
        info.include_packages.add('ca-certificates')
        info.include_packages.add('apt-transport-s3')


class AddRepoKey(Task):
    description = 'Import additional apt repo keys'
    phase = phases.package_installation
    successors = [apt.WriteSources]

    @classmethod
    def run(cls, info):
        for key in info.manifest.plugins['apt_repo'].iterkeys():
            data = info.manifest.plugins['apt_repo'][key]
            key_url = data['key_url']

            key_file = os.path.join(info.root, 'tmp/repo.gpg')
            log_check_call(['wget', key_url, '-O', key_file])
            log_check_call(['chroot', info.root, 'apt-key', 'add', '/tmp/repo.gpg'])
            os.remove(key_file)


class AddRepo(Task):
    description = 'Add additional apt repos'
    phase = phases.preparation
    predecessors = [apt.AddManifestSources]

    @classmethod
    def run(cls, info):
        for key in info.manifest.plugins['apt_repo'].iterkeys():
            data = info.manifest.plugins['apt_repo'][key]
            url = data['url']
            release = data['release']
            components = data['components']

            source = "deb %s %s %s" % (url, release, " ".join(components))
            info.source_lists.add(key, source)
