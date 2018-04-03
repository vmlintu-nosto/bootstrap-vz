import tasks.mounts
import tasks.shrink
import tasks.apt
import tasks.dpkg
from bootstrapvz.common.tasks import dpkg, locale


def get_shrink_type(plugins):
    """Gets the type of shrinking process requested by the user, taking into account backward compatibility
    values

    :param dict plugins: the part of the manifest related to plugins
    :return: None (if none selected), "vmware-vdiskmanager" or "qemu-img" (tool to be used)"""
    shrink_type = plugins['minimize_size'].get('shrink')
    if shrink_type is True:
        shrink_type = 'vmware-vdiskmanager'
    elif shrink_type is False:
        shrink_type = None
    elif shrink_type == 'qemu-img-no-compression':
        shrink_type = 'qemu-img'
    return shrink_type


def validate_manifest(data, validator, error):
    from bootstrapvz.common.tools import rel_path
    validator(data, rel_path(__file__, 'manifest-schema.yml'))

    shrink_type = get_shrink_type(data['plugins'])
    if shrink_type == 'vmware-vdiskmanager' and data['volume']['backing'] != 'vmdk':
        error('Can only shrink vmdk images with vmware-vdiskmanager', ['plugins', 'minimize_size', 'shrink'])
    if shrink_type == 'qemu-img' and data['volume']['backing'] not in ('vmdk', 'vdi', 'raw', 'qcow2'):
        error('Can only shrink vmdk, vdi, raw and qcow2 images with qemu-img', ['plugins', 'minimize_size', 'shrink'])


def resolve_tasks(taskset, manifest):
    taskset.update([tasks.mounts.AddFolderMounts,
                    tasks.mounts.RemoveFolderMounts,
                    ])
    if manifest.plugins['minimize_size'].get('zerofree', False):
        taskset.add(tasks.shrink.AddRequiredZeroFreeCommand)
        taskset.add(tasks.shrink.Zerofree)
    if get_shrink_type(manifest.plugins) == 'vmware-vdiskmanager':
        taskset.add(tasks.shrink.AddRequiredVDiskManagerCommand)
        taskset.add(tasks.shrink.ShrinkVolumeWithVDiskManager)
    if get_shrink_type(manifest.plugins) == 'qemu-img':
        taskset.add(tasks.shrink.AddRequiredQemuImgCommand)
        taskset.add(tasks.shrink.ShrinkVolumeWithQemuImg)
    if 'apt' in manifest.plugins['minimize_size']:
        apt = manifest.plugins['minimize_size']['apt']
        if apt.get('autoclean', False):
            taskset.add(tasks.apt.AutomateAptClean)
        if 'languages' in apt:
            taskset.add(tasks.apt.FilterTranslationFiles)
        if apt.get('gzip_indexes', False):
            taskset.add(tasks.apt.AptGzipIndexes)
        if apt.get('autoremove_suggests', False):
            taskset.add(tasks.apt.AptAutoremoveSuggests)
    if 'dpkg' in manifest.plugins['minimize_size']:
        filter_tasks = [dpkg.CreateDpkgCfg,
                        tasks.dpkg.InitializeBootstrapFilterList,
                        tasks.dpkg.CreateBootstrapFilterScripts,
                        tasks.dpkg.DeleteBootstrapFilterScripts,
                        ]
        msdpkg = manifest.plugins['minimize_size']['dpkg']
        if 'locales' in msdpkg:
            taskset.update(filter_tasks)
            taskset.add(tasks.dpkg.FilterLocales)
            # If no locales are selected, we don't need the locale package
            if msdpkg['locales']:
                taskset.discard(locale.LocaleBootstrapPackage)
                taskset.discard(locale.GenerateLocale)
        if msdpkg.get('exclude_docs', False):
            taskset.update(filter_tasks)
            taskset.add(tasks.dpkg.ExcludeDocs)


def resolve_rollback_tasks(taskset, manifest, completed, counter_task):
    counter_task(taskset, tasks.mounts.AddFolderMounts, tasks.mounts.RemoveFolderMounts)
    counter_task(taskset, tasks.dpkg.CreateBootstrapFilterScripts, tasks.dpkg.DeleteBootstrapFilterScripts)
