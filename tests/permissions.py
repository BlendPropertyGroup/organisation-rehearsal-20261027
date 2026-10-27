"""Tests only the disposable repository's GitHub permissions; deploys no software."""
import json
import os
import re
import sys
import urllib.error
import urllib.request

repository = os.environ['GITHUB_REPOSITORY']
assert repository in {
    'BlendPropertyGroup/organisation-rehearsal-20261027',
    'blendproperty/organisation-rehearsal-20261027',
}
assert os.environ.get('GITHUB_API_URL', 'https://api.github.com') == 'https://api.github.com'
revision = os.environ['GITHUB_SHA']
assert re.fullmatch(r'[0-9a-f]{40}', revision)


def request(path, data=None):
    req = urllib.request.Request(
        'https://api.github.com/repos/' + repository + path,
        data=None if data is None else json.dumps(data).encode(),
        headers={
            'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        },
        method='GET' if data is None else 'POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


status, repo = request('')
assert status == 200 and repo['id'] == 1435287249 and repo['full_name'] == repository
if sys.argv[1:] == ['read-only']:
    status, result = request('/git/blobs', {'content': 'synthetic permission probe', 'encoding': 'utf-8'})
    assert status == 403 and result['message'] == 'Resource not accessible by integration', (status, result.get('message'))
    print('PASS: authenticated read succeeded; contents write denied with403.')
elif sys.argv[1:] == ['deployment']:
    status, deployment = request('/deployments', {
        'ref': revision,
        'environment': 'synthetic-rehearsal',
        'description': 'Permission rehearsal only; no application or external service deployed.',
        'auto_merge': False,
        'required_contexts': [],
        'production_environment': False,
        'transient_environment': True,
    })
    assert status == 201 and deployment['sha'] == revision and deployment['environment'] == 'synthetic-rehearsal'
    status, result = request('/deployments/' + str(deployment['id']) + '/statuses', {
        'state': 'success',
        'description': 'Synthetic GitHub metadata only; no application deployment.',
    })
    assert status == 201 and result['state'] == 'success'
    print('PASS: scoped deployment permission recorded synthetic metadata only.')
else:
    raise SystemExit('Expected read-only or deployment mode.')
