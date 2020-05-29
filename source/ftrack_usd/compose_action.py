import tempfile
from pxr import Usd, Sdf
import os


class UsdCtxStage(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.usd_stage = Usd.Stage.CreateNew(self.filepath)

    def __enter__(self):
        return self.usd_stage

    def __exit__(self, type, value, traceback):
        print 'saving {}'.format(self.filepath)
        self.usd_stage.GetRootLayer().Save()


class BaseUSDCompositingAction(object):

    @property
    def location(self):
        return self.session.pick_location()

    def get_tmp_file(self, ext='usda'):
        temp = tempfile.NamedTemporaryFile(suffix='.{}'.format(ext), delete=False).name
        return temp

    def get_component(self, asset, component_name, task_name, status_name):
        query = (
            'select name, version.task.type.name, version.asset.id, version.status.name from Component where'
            ' version.asset.id is "{0}"'
            ' and version.status.name is "{1}"'
            ' and name like "{2}%"'
            ' and version.task.type.name is "{3}"'
            ' order by version.version descending'
        ).format(
            asset['id'], status_name, component_name, task_name
        )

        return self.session.query(query).first()


    def get_assets_ctx_path(self, root, asset_type):
        all_assets = []
        while root['descendants']:
            for child in root['descendants']:
                ctx_path = '/{}'.format(
                    '/'.join(
                        [
                            '_'.join(
                                [self.session.get(l['type'], l['id']).entity_type,
                                 l['name']]
                            )
                            for l in child['link']
                        ]
                    )
                ).replace(' ', '_').lower()

                assets = self.session.query(
                    'select name, type.name, versions from Asset where parent.id is "{}" and type.name is "{}"'.format(
                        child['parent']['id'], asset_type
                    )
                ).all()

                for asset in assets:
                    asset_name = '_'.join(
                        [asset['type']['short'], asset['name']]
                    ).replace(' ', '_').lower()
                    asset_path = os.path.join(ctx_path, asset_name)
                    all_assets.append((asset_path, asset))
            root = child

        return all_assets

    def publish_result(self, root, file_path, asset_name, asset_type):
        asset_type = self.session.query('AssetType where name is "{}"'.format(asset_type)).one()

        asset = self.session.query(
            'Asset where name is "{}" and parent.id is "{}" and type.id is "{}"'.format(
                asset_name, root['parent']['id'], asset_type['id']
            )
        ).first()

        if not asset:
            asset = self.session.create('Asset', {
                'name': asset_name,
                'type': asset_type,
                'parent': root['parent']
            })

        asset_version = self.session.create('AssetVersion', {
            'asset': asset,
            'task': root
        })
        self.session.commit()

        asset_version.create_component(
            file_path,
            data={
                'name': 'usd'
            },
            location='auto'
        )

        self.session.commit()
