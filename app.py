"""Run: streamlit run app.py"""
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from src.config import ROOT, load_config, validate_config

st.set_page_config(page_title='RoadLens | Traffic intelligence', page_icon='🚦', layout='wide')
st.markdown('''<style>
.stApp {background:#0b1220;color:#e8eef8} h1,h2,h3{letter-spacing:-.035em}
[data-testid="stMetric"]{background:#152238;border:1px solid #263951;padding:18px;border-radius:14px}
.block-container{max-width:1250px;padding-top:2.5rem} .eyebrow{color:#53d8bd;font-size:12px;letter-spacing:.18em}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">WIUT HACKATHON · COMPUTER VISION</div>', unsafe_allow_html=True)
st.title('RoadLens')
st.write('Turn fixed-camera road footage into tracks, event timelines, and measurable traffic insights.')
demo, calibration, results, approach, team = st.tabs(['Analyze video', 'Camera setup', 'Sample results', 'Approach & report', 'Team'])

with calibration:
    st.subheader('Configure a fixed camera')
    st.write('Upload a reference video below to see its first frame. Coordinates range from 0 to 1: divide x by image width and y by image height. Draw the road and lanes by entering polygon vertices in JSON.')
    st.info('Only set calibrated=true after defining the road, all relevant crossings, queue zones at signals, and lane directions. Camera geometry does not transfer automatically to another road.')
    profile = st.selectbox('Camera profile', ['camera.json', 'C3896.draft.json'])
    if profile.endswith('.draft.json'):
        st.warning('Draft geometry from C3896 footage. Lane directions, signal mapping and prohibited turns remain unset. Review the regions before interpreting events.')
    config_text = st.text_area('Camera configuration', json.dumps(load_config(ROOT/'configs'/profile), indent=2), height=330, key=f'config_{profile}')
    try:
        config = validate_config(json.loads(config_text))
        st.success('Configuration is valid.' if config.get('calibrated') else 'Valid configuration. Event rules are currently disabled; object tracking works.')
        st.download_button('Download camera.json', json.dumps(config, indent=2), 'camera.json', 'application/json')
        st.caption('For the submission, save this file as configs/camera.json. The demo uses the edited configuration for the next analysis.')
    except (ValueError, KeyError, TypeError) as exc:
        config = None
        st.error(f'Invalid configuration: {exc}')

with demo:
    st.subheader('See what happened on the road')
    st.write('Upload a fixed road CCTV clip. MP4 · up to 2 minutes · 100 MB. Processing runs on this server.')
    upload = st.file_uploader('Choose a video', type=['mp4'])
    export = st.checkbox('Create annotated playback (adds processing time)', value=False)
    st.caption('Uploads are processed in temporary storage and removed after analysis. Results remain in your browser session. This prototype is not a calibrated safety system.')
    if upload:
        st.video(upload)
    if st.button('Analyze video', type='primary', disabled=upload is None or config is None):
        st.session_state.pop('analysis', None)
        st.session_state.pop('annotated', None)
        if upload.size > 100*1024*1024:
            st.error('Please upload a file under 100 MB.')
        elif not (ROOT/'weights/yolo11n.pt').is_file():
            st.error('Model weights are missing. Run python scripts/download_weights.py on the server first.')
        else:
            bar = st.progress(0, text='Reading video…')
            try:
                import cv2
                from src.pipeline import analyze
                with tempfile.TemporaryDirectory(prefix='roadlens-') as directory:
                    path = Path(directory)/'upload.mp4'
                    path.write_bytes(upload.getvalue())
                    cap = cv2.VideoCapture(str(path))
                    try:
                        fps, frames = cap.get(5), cap.get(7)
                        ok, first = cap.read()
                        if not ok or not np.isfinite(fps) or fps <= 0 or frames/fps > 120:
                            raise ValueError('Use a decodable MP4 no longer than 120 seconds.')
                        if first.shape[0]*first.shape[1] > 3840*2160:
                            raise ValueError('Maximum supported resolution is 4K.')
                    finally:
                        cap.release()
                    st.session_state['first_frame'] = cv2.cvtColor(first, cv2.COLOR_BGR2RGB)
                    data = analyze(path, config, lambda x: bar.progress(x, text=f'Detecting and tracking · {x:.0%}'))
                    if export:
                        from src.render import render_video
                        bar.progress(1.0, text='Creating annotated playback…')
                        rendered = render_video(path, data, Path(directory)/'annotated.mp4')
                        st.session_state['annotated'] = rendered.read_bytes()
                        st.session_state['browser_video'] = bool(shutil.which('ffmpeg'))
                    st.session_state['analysis'] = data
                    st.session_state['analysis_name'] = upload.name
                bar.progress(1.0, text='Analysis complete')
            except Exception as exc:
                st.error(f'Analysis failed: {exc}')
    if 'analysis' in st.session_state:
        data = st.session_state['analysis']
        if 'annotated' in st.session_state:
            if st.session_state.get('browser_video'):
                st.video(st.session_state['annotated'])
            else:
                st.caption('Download annotated playback. Install ffmpeg on the server for browser-compatible H.264.')
            st.download_button('Download annotated video', st.session_state['annotated'], 'annotated.mp4', 'video/mp4')
        st.caption(f"Results for {st.session_state['analysis_name']}. Rerun analysis after changing the video or configuration.")
        columns = st.columns(4)
        for col, label, value in zip(columns, ['Duration', 'Events', 'Processing time', 'Runtime / duration'],
                                     [f"{data['meta']['duration']:.1f}s", len(data['events']), f"{data['meta']['elapsed']:.1f}s", f"{data['meta']['realtime_factor']:.2f}×"]):
            col.metric(label, value)
        if not data['calibrated']:
            st.warning('Camera is uncalibrated: no event claims are made. Configure the scene to enable event detection.')
        elif not data['events']:
            st.info('No supported events detected. Only rules with the required camera geometry and signal mapping can run; this does not prove the video is event-free.')
        if data['events']:
            st.dataframe([dict(start=s, end=e, event=k) for s, e, k in data['events']], hide_index=True)
            fig = go.Figure()
            for s, e, label in data['events']:
                fig.add_trace(go.Bar(x=[e-s], base=[s], y=[label], orientation='h', name=label, showlegend=False))
            fig.update_layout(xaxis_title='Seconds', height=280)
            st.plotly_chart(fig, use_container_width=True)
            selected = st.selectbox('Jump to an event', range(len(data['events'])), format_func=lambda i: f'{data["events"][i][2]} at {data["events"][i][0]:.1f}s')
            if upload and upload.name == st.session_state['analysis_name']:
                st.video(upload, start_time=int(data['events'][selected][0]))
        st.subheader('Traffic observations')
        if data['counts']:
            import pandas as pd
            st.line_chart(pd.DataFrame(data['counts']).set_index('time'))
        points = [o['point'] for frame in data['tracks'] for o in frame['objects']]
        if points:
            fig = go.Figure(go.Histogram2d(x=[p[0] for p in points], y=[p[1] for p in points], nbinsx=40, nbinsy=30, colorscale='Teal'))
            fig.update_layout(title='Object occupancy heatmap (not optical flow)', xaxis_range=[0,1], yaxis=dict(range=[1,0]), height=350)
            st.plotly_chart(fig, use_container_width=True)
        st.subheader('Track inspection')
        frame_index = st.slider('Sampled frame', 0, max(0, len(data['tracks'])-1), 0) if len(data['tracks']) > 1 else 0
        if data['tracks']:
            sample = data['tracks'][frame_index]
            st.caption(f"Timestamp: {sample['t']:.2f}s. Coordinates are normalized.")
            st.dataframe(sample['objects'], hide_index=True)
        if data['risk_enabled']:
            fig = go.Figure(go.Scatter(x=[r[0] for r in data['risk']], y=[r[1] for r in data['risk']], fill='tozeroy'))
            fig.update_layout(title='Experimental image-plane collision risk', yaxis=dict(range=[0,1],title='Risk score (0–1)'), xaxis_title='Timestamp (seconds)')
            st.plotly_chart(fig, use_container_width=True)
            st.caption('Uncalibrated heuristic score. Perspective and occlusion can cause false alarms.')
        st.caption('JSON risk entries are [timestamp_seconds, score_0_to_1]. Only the second number is the risk score.')
        risk_csv = 'timestamp_seconds,score_0_to_1\n'+'\n'.join(f'{t},{score}' for t,score in data['risk'])
        st.download_button('Download labeled risk CSV',risk_csv,'risk.csv','text/csv')
        st.download_button('Download predictions JSON', json.dumps({k: data[k] for k in ('events','risk')}, indent=2), 'predictions.json', 'application/json')
        st.download_button('Download full analysis', json.dumps(data), 'analysis.json', 'application/json')

with calibration:
    if 'first_frame' in st.session_state:
        st.image(st.session_state['first_frame'], caption='Reference frame from the last analyzed upload', use_container_width=True)
        if config:
            from src.render import draw_scene
            st.image(draw_scene(st.session_state['first_frame'],config),caption='Configured road, crossings, queues and excluded regions. Confirm alignment with this camera.',use_container_width=True)

with results:
    st.subheader('Sample-video evidence')
    files = sorted((ROOT/'outputs').glob('*.analysis.json')) if (ROOT/'outputs').exists() else []
    if not files:
        st.info('Official sample videos have not been supplied. No benchmark scores or sample results are claimed.')
    for path in files:
        with st.expander(path.stem):
            sample = json.loads(path.read_text())
            st.json(sample['meta'])
            video_path = path.with_name(path.name.replace('.analysis.json', '.annotated.mp4'))
            if video_path.exists():
                st.video(str(video_path))
            st.dataframe([dict(start=s, end=e, event=k) for s,e,k in sample['events']])
            st.download_button('Download analysis', path.read_bytes(), path.name, key=str(path))

with approach:
    st.subheader('A transparent baseline')
    st.write('YOLO11n detects people and road vehicles. ByteTrack connects objects across frames. Normalized bottom-center trajectories are compared with configured road regions to produce event segments. Segment filtering and merging enforce consistent output boundaries.')
    st.code('Video → YOLO11n → ByteTrack → trajectories → camera rules → event timeline')
    st.write('Ten configurable event rules: wrong_way, stopped_vehicle, jaywalking, congestion, failure_to_yield, red_light, stop_line, solid_line_crossing, illegal_turn and illegal_u_turn. Signal rules require verified lane-to-signal mapping and separate lamp crops; turn rules require explicitly prohibited entry/maneuver/exit paths.')
    st.write('Accident, near_miss, road_obstacle and fire_smoke classification remain unsupported. Optional risk uses past trajectories only and estimates image-plane closest approach; it is not a calibrated probability. Predicted amber boxes bridge short display gaps and are excluded from event evidence.')
    st.write('Known limitations: occlusion, ID switches, low-resolution pedestrians, perspective distortion, wrong geometry, and stationary queues outside their configured regions. Object occupancy is reported as an EDA proxy, not physical traffic flow.')
    st.write('Validation status: synthetic rule tests and local smoke tests. Hidden-set accuracy, sample accuracy and organizer-GPU runtime remain unmeasured until the official data and harness arrive.')
    st.markdown('[YOLO documentation](https://docs.ultralytics.com/models/yolo11/) · [ByteTrack](https://github.com/FoundationVision/ByteTrack)')

with team:
    st.subheader('The team behind RoadLens')
    st.info('Add your three members, portfolio links, repository URL, and actual contributions in configs/team.json before publication.')
    team_path = ROOT/'configs/team.json'
    if team_path.exists():
        members = json.loads(team_path.read_text())
        for member in members.get('members', []):
            st.write(f"**{member['name']}** — {member['role']}")
            st.write(member.get('contributions', ''))
            for label, url in member.get('links', {}).items():
                st.link_button(label, url)
