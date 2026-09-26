import json
import unittest
from pathlib import Path
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.httpclient import HTTPRequest
from tornado import gen
from website.server import Jobs, make_app, MAX_BYTES
from src.config import load_config


class WebsiteTest(AsyncHTTPTestCase):
    def get_app(self):
        self.jobs=Jobs(processor=self.fake_process)
        return make_app(self.jobs)

    def fake_process(self,token):
        job=self.jobs.get(token)
        folder=Path(job['temp'].name)
        if (folder/'input.mp4').read_bytes()!=b'video':
            raise ValueError('Bad uploaded bytes')
        (folder/'analysis.json').write_text(json.dumps({'events':[],'risk':[[0,.5]]}))
        self.jobs.update(token,state='done',progress=100)

    def tearDown(self):
        self.jobs.close()
        super().tearDown()

    def create(self,**overrides):
        payload=dict(name='clip.MP4',size=5,config=load_config(),render=False)
        payload.update(overrides)
        return self.fetch('/api/jobs',method='POST',body=json.dumps(payload),headers={'Content-Type':'application/json'})

    def test_frontend_profiles_and_limits(self):
        self.assertIn(b'Every road has a story',self.fetch('/').body)
        info=json.loads(self.fetch('/api/info').body)
        self.assertEqual(info['max_bytes'],3*1024**3)
        self.assertEqual(len(info['profiles']),2)

    def test_bad_file_oversize_config_and_origin(self):
        self.assertEqual(self.create(size=MAX_BYTES+1).code,400)
        self.assertEqual(self.create(name='file.exe').code,400)
        self.assertEqual(self.create(config={'sample_fps':0}).code,400)
        response=self.fetch('/api/jobs',method='POST',body='{}',headers={'Origin':'https://other.example'})
        self.assertEqual(response.code,403)

    def test_admission_limit_and_cleanup(self):
        result=self.create()
        token=json.loads(result.body)['id']
        folder=Path(self.jobs.get(token)['temp'].name)
        self.assertEqual(self.create().code,409)
        self.assertEqual(self.fetch('/api/jobs/'+token,method='DELETE').code,204)
        self.assertFalse(folder.exists())

    def test_wrong_upload_length_releases_slot(self):
        token=json.loads(self.create().body)['id']
        self.assertEqual(self.fetch(f'/api/jobs/{token}/video',method='PUT',body=b'bad').code,413)
        self.assertEqual(self.create().code,201)

    @gen_test
    async def test_upload_process_download_and_video_ranges(self):
        payload=dict(name='clip.mp4',size=5,config=load_config())
        response=await self.http_client.fetch(self.get_url('/api/jobs'),method='POST',body=json.dumps(payload))
        token=json.loads(response.body)['id']
        response=await self.http_client.fetch(self.get_url(f'/api/jobs/{token}/video'),method='PUT',body=b'video')
        self.assertEqual(response.code,202)
        for _ in range(100):
            status=json.loads((await self.http_client.fetch(self.get_url(f'/api/jobs/{token}'))).body)
            if status['state']=='done':break
            await gen.sleep(.01)
        self.assertEqual(status['state'],'done')
        response=await self.http_client.fetch(self.get_url(f'/api/jobs/{token}/files/analysis.json'))
        self.assertEqual(json.loads(response.body)['risk'],[[0,.5]])
        response=await self.http_client.fetch(HTTPRequest(self.get_url(f'/api/jobs/{token}/files/input.mp4'),headers={'Range':'bytes=0-1'}))
        self.assertEqual(response.code,206)
        self.assertEqual(response.body,b'vi')
        response=await self.http_client.fetch(self.get_url(f'/api/jobs/{token}/files/secret.txt'),raise_error=False)
        self.assertEqual(response.code,404)

if __name__=='__main__':unittest.main()
