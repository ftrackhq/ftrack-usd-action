#!/usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging

from ftrack_action_handler.action import BaseAction
import ftrack_api


class EditDescriptions(BaseAction):
    '''Action to allow updating the descriptions on AssetVersion Objects.'''
    label = 'Usd builder'
    identifier = 'com.ftrack.recipes.usd_builder'
    description = 'Create and publish UDS based on selected entity child.'

    def discover(self, session, entities, event):
        # available on any entity
        return True

    def launch(self, session, entities, event):
        for id_, comment in event['data']['values'].items():
            session.get('AssetVersion', id_)['comment'] = comment
        session.commit()

        return {
            'success': True,
            'message': 'Description(s) updated.'
        }

def register(session, **kw):
    if not isinstance(session, ftrack_api.Session):
        return

    action = EditDescriptions(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session(auto_connect_event_hub=True)
    register(session)
    logging.info(
        'Registered actions and listening for event. Use Ctrl-C to abort.'
    )
    session.event_hub.wait()