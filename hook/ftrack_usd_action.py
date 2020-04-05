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

from pxr import Usd, UsdGeom


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

                # create context path
                ctx_xform = usd_stage.DefinePrim(ctx_path, 'Xform')

                assets = session.query(
                    'select versions from Asset where parent.id is "{}"'.format(child['parent']['id'])
                ).all()

                if not assets:
                    # no asset version found....    
                    continue
                
                for asset in assets:
                    asset_name = '_'.join([asset['type']['short'], asset['name']]).replace(' ', '_').lower()
                    asset_path = os.path.join(ctx_path, asset_name)
                    # create asset path
                    asset_xform = usd_stage.DefinePrim(asset_path, 'Xform')

                    # create prim variant for versions
                    version_variant = asset_xform.GetVariantSets().AddVariantSet('versions')
                    for asset_versions in asset['versions']:
                        # add version as usd variant
                        version_variant.AddVariant('version_v{}'.format(asset_versions['version']))

                        # for component in asset_version['components']:
                        #     file_path = None
                        #     try:
                        #         file_path =  location.get_filesystem_path(component)
                        #     except Exception as error:
                        #         # print error
                        #         pass

                #reset root to child
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
