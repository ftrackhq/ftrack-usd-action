
def get_assets_ctx_path(session, root, asset_type):
    all_assets = []
    while root['descendants']:
        # ctx_path = None
        # xformPrim = None
        for child in root['descendants']:
            ctx_path = '/{}'.format(
                '/'.join(
                    [
                        '_'.join(
                            [session.get(l['type'], l['id']).entity_type,
                             l['name']]
                        )
                        for l in child['link']
                    ]
                )
            ).replace(' ', '_').lower()

            assets = session.query(
                'select versions from Asset where parent.id is "{}" and type.name is "{}"'.format(
                    child['parent']['id'], asset_type
                )
            ).all()
            all_assets.append((ctx_path, assets))

    return all_assets
