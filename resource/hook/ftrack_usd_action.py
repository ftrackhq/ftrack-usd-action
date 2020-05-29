#!/usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import tempfile
import os

import sys

sys.path.append(os.path.expanduser('~/.local/lib/python'))

from pxr import Usd, Sdf


dependencies_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'dependencies')

)
sys.path.append(dependencies_directory)
from ftrack_action_handler.action import BaseAction
import ftrack_api

from ftrack_usd.compose_action import BaseUSDCompositingAction, UsdCtxStage


class USDAction(BaseAction, BaseUSDCompositingAction):
    '''Action to allow updating the descriptions on AssetVersion Objects.'''
    label = 'Usd builder'
    identifier = 'com.ftrack.recipes.usd_builder'
    description = 'Create and publish UDS based on selected entity child.'
    asset_name = 'USD Scene'
    asset_type = 'scene'

    def discover(self, session, entities, event):
        # available on any entity
        if not entities:
            return False

        for entity_type, entity_id in entities:
            if entity_type != 'Project':
                return True

        return False

    def launch(self, session, entities, event):
        temp_file = self.get_tmp_file()
        entity_type, entity_id = entities[0]
        root = self.session.get(entity_type, entity_id)
        print 'launching for', root

        with UsdCtxStage(temp_file) as usd_stage:
            print 'stage', usd_stage

            results = self.get_assets_ctx_path(root, 'Geometry')
            print 'asets', results

        self.publish_result(root, temp_file, self.asset_name, self.asset_type)

        return {
            'success': True,
            'message': 'Done.'
        }


def register(session, **kw):
    if not isinstance(session, ftrack_api.Session):
        return
    action = USDAction(session)
    print 'registering', action.identifier
    action.register()
