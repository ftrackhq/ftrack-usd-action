#!/usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import tempfile
import os
from ftrack_action_handler.action import BaseAction
import ftrack_api
import sys
sys.path.append(os.path.expanduser('~/.local/lib/python'))

from pxr import Usd,Sdf


class USDAction(BaseAction):
    '''Action to allow updating the descriptions on AssetVersion Objects.'''
    label = 'Usd builder'
    identifier = 'com.ftrack.recipes.usd_builder'
    description = 'Create and publish UDS based on selected entity child.'
    asset_name = 'USD Scene'

    def discover(self, session, entities, event):
        # available on any entity
        if not entities:
            return False

        for entity_type, entity_id in entities:
            if entity_type != 'Project':
                return True

        return False

    def launch(self, session, entities, event):
        temp = tempfile.NamedTemporaryFile(suffix='.usda', delete=False).name
        usd_stage = Usd.Stage.CreateNew(temp)
        location = session.pick_location()

        entity_type, entity_id = entities[0]
        root = self.session.get(entity_type, entity_id)

        while root['descendants']:
            # ctx_path = None
            # xformPrim = None
            for child in root['descendants']:

                ctx_path =  '/{}'.format(
                    '/'.join(
                        [
                            '_'.join(
                                [session.get(l['type'],l['id']).entity_type, 
                                l['name']]
                            ) 
                            for l in child['link']
                        ]
                    )
                ).replace(' ', '_').lower()


                assets = session.query(
                    'select versions from Asset where parent.id is "{}" and type.name is "Geometry"'.format(
                        child['parent']['id']
                    )
                ).all()

                for asset in assets:
                    if not asset['versions']:
                        continue

                    asset_name = '_'.join(
                        [asset['type']['short'], asset['name']]).replace(' ',
                                                                         '_').lower()
                    asset_path = os.path.join(ctx_path, asset_name)

                    # asset_xform = usd_stage.DefinePrim(asset_path, 'Xform')
                    # version_variant = asset_xform.GetVariantSets().AddVariantSet(
                    #     'versions')

                    for asset_version in asset['versions']:
                        # version = 'v{}'.format(asset_version['version'])

                        for component in asset_version['components']:

                            if (
                                    not component['name'].startswith('usd_') or
                                    not component['file_type'].startswith(
                                        '.usd')
                            ):
                                continue

                            file_path = None
                            try:
                                file_path = location.get_filesystem_path(
                                    component)
                            except Exception as error:
                                stage.RemovePrim(asset_path)
                                print error
                                continue

                            component_name = component['name'].replace(' ',
                                                                       '_').replace(
                                '-', '_').lower()
                            component_path = os.path.join(asset_path,
                                                          'component_{}'.format(
                                                              component_name))
                            component_xform = usd_stage.DefinePrim(component_path,
                                                               'Mesh')

                            # version_variant.AddVariant(version)
                            # version_variant.SetVariantSelection(version)
                            #
                            # print 'creating component path {} with version variant {}'.format(
                            #     component_path, version)
                            #
                            # with version_variant.GetVariantEditContext() as ctx:
                            #     component_xform.SetPayload(
                            #         Sdf.Payload(file_path))

                root = child

        usd_stage.GetRootLayer().Save()

        # publish to context
        asset_type = session.query('AssetType where name is "scene"').one()

        asset = session.query(
            'Asset where name is "{}" and parent.id is "{}" and type.id is "{}"'.format(
                self.asset_name, root['parent']['id'], asset_type['id']
            )
        ).first()

        if not asset:
            asset = session.create('Asset', {
                'name': self.asset_name,
                'type': asset_type,
                'parent': root['parent']
            })

        asset_version = session.create('AssetVersion', {
            'asset': asset,
            'task': root
        })
        session.commit()

        asset_version.create_component(
            temp,
            data={
                'name': 'usd'
            },
            location='auto'
        )

        session.commit()

        return {
            'success': True,
            'message': 'Done.'
        }

def register(session, **kw):
    if not isinstance(session, ftrack_api.Session):
        return
    action = USDAction(session)
    action.register()
