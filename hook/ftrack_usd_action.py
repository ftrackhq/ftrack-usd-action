#!/usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging

from ftrack_action_handler.action import BaseAction
import ftrack_api
import sys
sys.path.append('/home/ftrackwork/.local/lib/python')

from pxr import Usd, UsdGeom


class USDAction(BaseAction):
    '''Action to allow updating the descriptions on AssetVersion Objects.'''
    label = 'Usd builder'
    identifier = 'com.ftrack.recipes.usd_builder'
    description = 'Create and publish UDS based on selected entity child.'

    def discover(self, session, entities, event):
        # available on any entity
        if not entities:
            return False
        
        return True

    def launch(self, session, entities, event):
        usd_stage = Usd.Stage.CreateNew('HelloWorld.usda')

        entity_type, entity_id = entities[0]
        root = self.session.get(entity_type, entity_id)

        while root['descendants']:
            for child in root['descendants']:
                # placement =  '/{0}'.format('/'.join([link['name'] for link in child['link']]))
                links = [l['name'] for l in child['link']]
                link = ''
                for clink in links:
                    link += '/'+ clink
                    print link
                    # xformPrim = UsdGeom.Xform.Define(usd_stage, link)

                # asset_versions = session.query(
                #     'select components from AssetVersion where task.id is "{}"'.format(child['id'])
                # ).all()
                # for asset_version in asset_versions:
                #     for component in asset_version['components']:
                #         print component
                #         file_path = None
                #         try:
                #             file_path =  location.get_filesystem_path(component)
                #         except Exception as error:
                #             print error
                #             pass

                #         if file_path and os.path.splitext(filepath)[-1] == '.usd':
                #             print filepath

                root = child
        # usd_stage.GetRootLayer().Save()

        return {
            'success': True,
            'message': 'Done.'
        }

def register(session, **kw):
    if not isinstance(session, ftrack_api.Session):
        return
    action = USDAction(session)
    action.register()
