Add additional apt repos
------------------------

This plugin adds support for adding additional apt repositories. It imports
the public repo key from the given URL and adds the sources list files. Multiple
repositories are supported.

The plugin supports also S3 backed repositories and it installs automatically
apt-transport-s3 package.

Example
~~~~~~~

.. code-block:: yaml

    ---
    plugins:
      apt_repo:
        dev:
          url: s3://devbucket.s3.amazonaws.com/debian
          release: stretch
          components:
            - main
          key_url: https://host/devrepo.gpg
        test:
          url: s3://testbucket.s3.amazonaws.com/debian
          release: stretch
          components:
            - main
          key_url: https://host/testrepo.gpg

Settings
~~~~~~~~

-  ``url``: URL of the apt repo root
-  ``release``: Debian release
-  ``components``: Array of components
-  ``key_url``: URL of the public repo key
