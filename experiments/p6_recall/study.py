"""Campagne exploratoire locale, corpus fixé et traces exportables sans synthèse.

Aucune génération à l'import. Aucun jeu P7 ni corpus de confirmation n'est lu.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import time
import urllib.error
import urllib.request

from app.chat_backend import OllamaChatAdapter
from app.dialogue import default_profile
from core.llm import OllamaClient
from experiments.p6_recall.corpus import build_cases, conditions, control_conditions, render, render_control, score

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS = ('gemma3:latest', 'llama3.1:8b', 'granite3.3:latest', 'mistral:latest')
SEEDS = (1001, 1002, 1003)
SOURCE_PATHS = ('experiments/p6_recall/study.py', 'experiments/p6_recall/corpus.py',
                'app/context.py', 'app/dialogue.py', 'app/chat_backend.py', 'core/llm.py',
                'scripts/p6_recall_study.py')


def utc():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2) + '\n').encode('utf-8')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    path = Path(path)
    with path.open('xb') as target:
        target.write(encoded(value))
        target.flush()
        os.fsync(target.fileno())


def seal_file(path):
    path = Path(path)
    with path.with_suffix(path.suffix + '.sha256').open('x', encoding='utf-8') as target:
        target.write(digest(path) + '  ' + path.name + '\n')


def verify_file(path):
    path = Path(path)
    parts = path.with_suffix(path.suffix + '.sha256').read_text(encoding='utf-8').strip().split()
    if parts != [digest(path), path.name]:
        raise ValueError('Empreinte de fichier invalide : ' + path.name)


def source_hashes():
    return {name: digest(ROOT / name) for name in SOURCE_PATHS}


def verify_sources(expected):
    if source_hashes() != expected:
        raise ValueError('Le code de mesure a changé ; nouveau gel nécessaire.')


def verify_protocol(path):
    path = Path(path)
    parts = path.with_suffix('.sha256').read_text(encoding='utf-8').strip().split()
    if len(parts) != 2 or parts[1] != path.name or parts[0] != digest(path):
        raise ValueError('Sceau du protocole invalide.')
    return parts[0]


def make_jobs(models=DEFAULT_MODELS):
    """Ordre fixe partiellement contrebalancé ; aucune sélection sur les sorties."""
    cases, variants = build_cases(), conditions()
    jobs = []
    for repetition, seed in enumerate(SEEDS):
        model_order = list(models[repetition:] + models[:repetition])
        for model in model_order:
            block = []
            for case in cases:
                for variant in variants:
                    block.append({'case': case, 'condition': variant['id'], 'factors': variant,
                                  'kind': 'factorial', 'expected': case['current_value'],
                                  'messages': render(case, variant)})
                for name in control_conditions():
                    messages, expected = render_control(case, name)
                    block.append({'case': case, 'condition': name, 'factors': None,
                                  'kind': 'control', 'expected': expected, 'messages': messages})
            random.Random(20260908 + repetition).shuffle(block)
            for item in block:
                item.update(model=model, seed=seed, repetition=repetition, block=f'r{repetition}-{model}')
                item['id'] = sha256(encoded({k: item[k] for k in ('model', 'seed', 'condition', 'case')})).hexdigest()[:24]
                jobs.append(item)
    return jobs


def prepare(protocol, destination):
    """Lecture de métadonnées seulement ; pas de chargement/génération de modèle."""
    protocol = Path(protocol).resolve()
    seal = verify_protocol(protocol)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    # Copie scellée autonome : aucune dépendance au chemin du poste d'origine.
    for source in (protocol, protocol.with_suffix('.sha256')):
        with (destination / source.name).open('xb') as target:
            target.write(source.read_bytes())
    adapter = OllamaChatAdapter()
    engines, metadata = {}, {}
    for model in DEFAULT_MODELS:
        engines[model] = adapter.freeze(OllamaClient(model=model, timeout=90, think=False))
        metadata[model] = adapter._json(engines[model]['base_url'], '/api/show', {'model': model})
    jobs = make_jobs()
    write_new(destination / 'cases.json', build_cases())
    write_new(destination / 'conditions.json', conditions())
    write_new(destination / 'jobs.json', jobs)
    write_new(destination / 'models.json', metadata)
    manifest = {'study': 'P6-RECALL-EXPLORATORY-v1', 'created_utc': utc(),
                'protocol': protocol.name, 'protocol_sha256': seal, 'sources': source_hashes(),
                'engines': engines, 'profile': default_profile(), 'seeds': SEEDS,
                'job_count': len(jobs), 'factorial_jobs': sum(j['kind'] == 'factorial' for j in jobs),
                'files': {p.name: digest(p) for p in destination.iterdir() if p.is_file()}}
    write_new(destination / 'manifest.json', manifest)
    seal_file(destination / 'manifest.json')
    return manifest


def load_study(folder):
    folder = Path(folder)
    verify_file(folder / 'manifest.json')
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    if verify_protocol(folder / manifest['protocol']) != manifest['protocol_sha256']:
        raise ValueError('Le protocole ne correspond plus au manifeste.')
    verify_sources(manifest['sources'])
    for name, expected in manifest['files'].items():
        if digest(folder / name) != expected:
            raise ValueError('Pièce de campagne modifiée : ' + name)
    return manifest, json.loads((folder / 'jobs.json').read_text(encoding='utf-8'))


def payload_for(job, manifest):
    profile = manifest['profile']
    options = dict(profile['options'], seed=job['seed'])
    return {'model': job['model'], 'messages': job['messages'], 'stream': False,
            'options': options, 'think': profile['think'], 'truncate': False, 'shift': False}


def invoke(engine, payload):
    """Requête et réponse exactes conservées, y compris erreurs HTTP et sorties vides."""
    body = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
    request = urllib.request.Request(engine['base_url'] + '/api/chat', data=body,
                                     headers={'Content-Type': 'application/json'})
    started = time.monotonic()
    result = {'request_body': body.decode('utf-8'), 'started_utc': utc()}
    try:
        with urllib.request.urlopen(request, timeout=engine['timeout']) as response:
            result.update(http_status=response.status, response_body=response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        result.update(http_status=exc.code, response_body=exc.read().decode('utf-8', errors='replace'))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result.update(http_status=None, response_body=None, transport_error=type(exc).__name__ + ': ' + str(exc))
    result.update(elapsed_seconds=time.monotonic() - started, completed_utc=utc())
    data = None
    try:
        data = json.loads(result['response_body']) if result['response_body'] else None
    except (ValueError, TypeError):
        pass
    result['response'] = data
    if result['http_status'] != 200:
        result['technical_status'] = 'transport_error'
    elif not isinstance(data, dict) or data.get('done') is not True:
        result['technical_status'] = 'invalid_response'
    elif data.get('done_reason') == 'length':
        result['technical_status'] = 'output_truncated'
    elif not isinstance(data.get('message'), dict) or data['message'].get('role') != 'assistant' or not isinstance(data['message'].get('content'), str) or not data['message']['content'].strip():
        result['technical_status'] = 'invalid_response'
    else:
        result['technical_status'] = 'valid'
    return result


def check_engine(engine):
    actual = OllamaChatAdapter().freeze(OllamaClient(model=engine['model'], base_url=engine['base_url'],
                                                     timeout=engine['timeout'], think=False))
    if actual != engine:
        raise ValueError('Runtime ou modèle modifié, arrêt sans substitution : ' + engine['model'])


@contextmanager
def locked(folder):
    # Le verrou OS est libéré même après arrêt brutal du processus. Fichier conservé.
    if os.name == 'nt':
        import msvcrt
    else:
        import fcntl
    with (Path(folder) / 'execution.lock').open('a+b') as handle:
        if handle.tell() == 0:
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError('Une autre exécution détient cette campagne.') from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def qualify(folder):
    """Un appel de forme par modèle ; réponses non utilisées pour sélectionner les facteurs."""
    folder = Path(folder)
    manifest, _ = load_study(folder)
    with locked(folder):
        output = folder / 'qualification'
        output.mkdir(exist_ok=False)
        summary = []
        for i, engine in enumerate(manifest['engines'].values()):
            check_engine(engine)
            job = {'model': engine['model'], 'seed': SEEDS[0], 'messages': [
                {'role': 'user', 'content': 'Pour ce contrôle technique, réponds seulement par un mot court en français.'}]}
            payload = payload_for(job, manifest)
            write_new(output / f'{i}-request.json', payload)
            result = invoke(engine, payload)
            write_new(output / f'{i}-response.json', result)
            seal_file(output / f'{i}-response.json')
            try:
                check_engine(engine)
                post = {'passed': True, 'loaded_models': OllamaChatAdapter._json(engine['base_url'], '/api/ps')}
            except Exception as exc:
                post = {'passed': False, 'error': type(exc).__name__ + ': ' + str(exc)}
            write_new(output / f'{i}-postcheck.json', post)
            data = result.get('response') if isinstance(result.get('response'), dict) else {}
            passed = (result['technical_status'] == 'valid' and isinstance(data.get('prompt_eval_count'), int)
                      and data['prompt_eval_count'] > 0 and isinstance(data.get('eval_count'), int)
                      and data['eval_count'] > 0 and post['passed'])
            summary.append({'model': engine['model'], 'passed': passed, 'technical_status': result['technical_status']})
        report = {'created_utc': utc(), 'scope': 'transport and complete final channel only; not semantic admission',
                  'passed': all(s['passed'] for s in summary), 'models': summary,
                  'files': {p.name: digest(p) for p in output.iterdir()}}
        write_new(output / 'verification.json', report)
        seal_file(output / 'verification.json')
        return report


def run(folder, max_calls=None):
    folder = Path(folder)
    manifest, jobs = load_study(folder)
    verify_file(folder / 'qualification/verification.json')
    qualification = json.loads((folder / 'qualification/verification.json').read_text(encoding='utf-8'))
    if not qualification['passed']:
        raise ValueError('Admission technique incomplète ; aucune campagne comparative lancée.')
    for name, expected in qualification['files'].items():
        if digest(folder / 'qualification' / name) != expected:
            raise ValueError('Preuve de qualification modifiée.')
    with locked(folder):
        records = folder / 'records'
        records.mkdir(exist_ok=True)
        completed = 0
        last_block = None
        for number, job in enumerate(jobs):
            final_path = records / (job['id'] + '.json')
            pending_path = records / (job['id'] + '.request.json')
            if final_path.exists():
                verify_file(final_path)
                existing = json.loads(final_path.read_text(encoding='utf-8'))
                if existing['job_id'] != job['id'] or existing['request_sha256'] != digest(pending_path):
                    raise ValueError('Résultat existant incohérent ; reprise refusée sans régénération.')
                continue
            if max_calls is not None and completed >= max_calls:
                break
            engine = manifest['engines'][job['model']]
            if job['block'] != last_block:
                if last_block is not None:
                    verify_sources(manifest['sources'])
                check_engine(engine)
                last_block = job['block']
                print(json.dumps({'block': last_block, 'position': number, 'total': len(jobs)}), flush=True)
            payload = payload_for(job, manifest)
            if pending_path.exists():
                result = {'technical_status': 'uncertain_execution', 'response': None,
                          'completed_utc': utc(), 'note': 'Previous invocation has no durable result; no automatic retry.'}
            else:
                write_new(pending_path, {'job_id': job['id'], 'payload': payload, 'reserved_utc': utc()})
                result = invoke(engine, payload)
            row = {'job_id': job['id'], 'case_id': job['case']['id'], 'template_id': job['case']['template_id'],
                   'model': job['model'], 'seed': job['seed'], 'condition': job['condition'], 'kind': job['kind'],
                   'request_sha256': digest(pending_path), **result}
            write_new(final_path, row)
            seal_file(final_path)
            completed += 1
            if completed % 25 == 0:
                print(json.dumps({'processed_this_invocation': completed, 'position': number + 1,
                                  'last_technical_status': result['technical_status']}), flush=True)
            if result['technical_status'] in ('transport_error', 'invalid_response'):
                print('Technical interruption retained; resume only after inspecting the cause.', flush=True)
                break
        if last_block is not None:
            check_engine(manifest['engines'][last_block.split('-', 1)[1]])
        verify_sources(manifest['sources'])
        status = {'created_utc': utc(), 'processed_this_invocation': completed,
                  'completed': sum((records / (j['id'] + '.json')).exists() for j in jobs), 'planned': len(jobs)}
        status['collection_complete'] = status['completed'] == status['planned']
        write_new(folder / ('progress-' + str(time.time_ns()) + '.json'), status)
        return status


def analyse(folder, destination):
    """Descriptif uniquement ; refuse une collection partielle et conserve tous les dénominateurs."""
    folder = Path(folder)
    manifest, jobs = load_study(folder)
    rows = []
    for job in jobs:
        path = folder / 'records' / (job['id'] + '.json')
        if not path.exists():
            raise ValueError('Collection incomplète : aucun classement sur un sous-ensemble sélectionné.')
        verify_file(path)
        row = json.loads(path.read_text(encoding='utf-8'))
        pending = folder / 'records' / (job['id'] + '.request.json')
        request = json.loads(pending.read_text(encoding='utf-8'))
        if row['job_id'] != job['id'] or row['request_sha256'] != digest(pending) or request['payload'] != payload_for(job, manifest):
            raise ValueError('Trace hors plan ou altérée.')
        if row['technical_status'] != 'uncertain_execution':
            if json.loads(row['request_body']) != request['payload']:
                raise ValueError('Corps envoyé différent du payload réservé.')
            wire = row.get('response_body')
            try:
                parsed = json.loads(wire) if wire else None
            except (ValueError, TypeError):
                parsed = None
            if parsed != row.get('response'):
                raise ValueError('Réponse décodée différente de la trace brute.')
        if row['technical_status'] == 'valid':
            text = row['response']['message']['content']
            judgement = score(text, job['expected'], job['case']['old_value'])
        else:
            judgement = {'success': False, 'category': row['technical_status']}
        rows.append({'job_id': job['id'], 'model': job['model'], 'kind': job['kind'],
                     'case_id': job['case']['id'], 'template_id': job['case']['template_id'],
                     'condition': job['condition'], 'factors': job['factors'],
                     'technical_status': row['technical_status'], **judgement})
    output = {'scope': 'exploratory fixed corpus; no confirmation or population-level claim',
              'created_utc': utc(), 'all_planned_jobs': len(jobs), 'models': {}, 'scores': rows}
    for model in manifest['engines']:
        selected = [r for r in rows if r['model'] == model and r['kind'] == 'factorial']
        def rate(group):
            return sum(r['success'] for r in group) / len(group)
        effects = {}
        for factor in 'ABCD':
            effects[factor] = rate([r for r in selected if r['factors'][factor]]) - rate([r for r in selected if not r['factors'][factor]])
        interactions = {}
        for i, left in enumerate('ABCD'):
            for right in 'ABCD'[i+1:]:
                cell = lambda a,b: rate([r for r in selected if r['factors'][left] == a and r['factors'][right] == b])
                interactions[left+right] = cell(True,True) - cell(False,True) - cell(True,False) + cell(False,False)
        valid = [r for r in selected if r['technical_status'] == 'valid']
        output['models'][model] = {'planned': len(selected), 'valid': len(valid),
                                   'success_over_planned': rate(selected),
                                   'success_over_valid': rate(valid) if valid else None,
                                   'main_effects': effects, 'two_factor_interactions': interactions,
                                   'controls': {name: {'planned': len(group), 'successes': sum(r['success'] for r in group)}
                                    for name in control_conditions()
                                    for group in [[r for r in rows if r['model'] == model and r['kind'] == 'control' and r['condition'] == name]]}}
    write_new(destination, output)
    return output
