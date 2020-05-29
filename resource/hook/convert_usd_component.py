# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import logging
import os
import sys
import tempfile
import subprocess


# add pxr libraries
sys.path.append(os.path.expanduser('~/.local/lib/bin'))

# add local dependencies

dependencies_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'dependencies')

)

sys.path.append(dependencies_directory)
import ftrack_api


class ConvertUsdComponentAction(object):
    '''Action to open a component directory in os file browser.'''

    identifier = 'ftrack-connect-convert-usd-component'

    failed = {
        'success': False,
        'message': (
            'Could not open component directory.'
        )
    }

    def __init__(self, session, logger):
        '''Instantiate action with *session*.'''
        self.session = session
        self.logger = logger

    def discover(self, event):
        '''Discover *event*.'''
        selection = event['data'].get('selection', [])
        if (
            len(selection) == 1 and
            selection[0]['entityType'] == 'Component'
        ):
            return {
                'items': [{
                    'label': 'Convert Alembic to USD',
                    'actionIdentifier': self.identifier
                }]
            }

    def resolve_path(self, component_id):
        '''Return path from *component_id*.'''
        legacy_component = None
        legacy_location = None
        try:
            legacy_component = ftrack.Component(component_id)
            legacy_location = legacy_component.getLocation()
        except Exception:
            self.logger.exception(
                'Could not pick location for legacy component {0!r}'.format(
                    legacy_component
                )
            )

        location = None
        component = None
        try:
            component = self.session.get('Component', component_id)
            location = self.session.pick_location(component)
        except Exception:
            self.logger.exception(
                'Could not pick location for component {0!r}'.format(
                    legacy_component
                )
            )

        path = None
        if legacy_location and location:
            if legacy_location.getPriority() < location.priority:
                path = legacy_component.getFilesystemPath()
                self.logger.info(
                    'Location is defined with a higher priority in legacy api: '
                    '{0!r}'.format(
                        legacy_location
                    )
                )

            elif (
                legacy_location.getPriority() == location.priority and
                legacy_location.getId() == location['id'] and
                legacy_location.getName() == 'ftrack.unmanaged'
            ):
                # The legacy api is better suited to resolve the path for a
                # location in the ftrack.unmanaged location, since it will
                # account for platform and disk while resolving.
                path = legacy_component.getFilesystemPath()
                self.logger.info(
                    'Location is unmanaged on both legacy api and api.'
                )

            else:
                path = location.get_filesystem_path(component)
                self.logger.info(
                    'Location is defined with a higher priority in api: '
                    '{0!r}'.format(
                        location
                    )
                )

        elif legacy_location:
            path = legacy_component.getFilesystemPath()
            self.logger.info(
                'Location is only defined in legacy api: {0!r}'.format(
                    legacy_location
                )
            )

        elif location:
            path = location.get_filesystem_path(component)
            self.logger.info(
                'Location is only in api: {0!r}'.format(
                    legacy_location
                )
            )

        return path

    def launch(self, event):
        '''Launch action for *event*.'''
        selection = event['data']['selection'][0]

        if selection['entityType'] != 'Component':
            return

        path = None
        component_id = selection['entityId']
        try:
            path = self.resolve_path(component_id)
        except Exception:
            self.logger.exception(
                'Exception raised while resolving component with id '
                '{0!r}'.format(
                    component_id
                )
            )

        if path is None:
            self.logger.info(
                'Could not determine a valid file system path for: '
                '{0!r}'.format(
                    component_id
                )
            )
            return self.failed

        if os.path.splitext(path)[-1] not in ['.abc']:
            return self.failed

        temp = tempfile.NamedTemporaryFile(suffix='.usd').name

        if os.path.exists(path):
            # File or directory exists.
            subprocess.Popen(['usdcat', path, '--out', temp])
        else:
            # No file, directory or parent directory exists for path.
            self.logger.info(
                'Directory resolved but non-existing {0!r} and {1!r}:'
                '{0!r}'.format(
                    component_id, path
                )
            )
            return self.failed

        component = self.session.get('Component', component_id)
        version = component['version']
        name = 'usd_{}'.format(component['name'])

        self._add_component(version, name, temp)

        return {
            'success': True,
            'message': 'Successfully opened component directory.'
        }

    def _add_component(self, asset_version, name, path):

        asset_version.create_component(
            path,
            data={
                'name': name
            },
            location='auto'
        )

        self.session.commit()

    def register(self):
        '''Register to event hub.'''
        self.session.event_hub.subscribe(
            u'topic=ftrack.action.discover '
            u'and source.user.username="{0}"'.format(
                self.session.api_user
            ),
            self.discover
        )

        self.session.event_hub.subscribe(
            'topic=ftrack.action.launch and data.actionIdentifier={0} and '
            'source.user.username="{1}"'.format(
                self.identifier,
                self.session.api_user
            ),
            self.launch
        )
#
#
# def register(session, **kw):
#     '''Register hooks.'''
#
#     logger = logging.getLogger(
#         'ftrack_connect:open-component-directory'
#     )
#
#     # Validate that session is an instance of ftrack_api.session.Session. If
#     # not, assume that register is being called from an old or incompatible API
#     # and return without doing anything.
#     if not isinstance(session, ftrack_api.Session):
#         logger.debug(
#             'Not subscribing plugin as passed argument {0!r} is not an '
#             'Session instance.'.format(session)
#         )
#         return
#
#     action = ConvertUsdComponentAction(session, logger)
#     action.register()