#!/usr/bin/env python3

import os
import argparse
import time
import re
from multiprocessing import get_context
from threading import Event, Thread
import requests

WORKERS = 8
_mp_progress = None

_INFO_FILTER = re.compile(r'^\s*(timestamp|posixseconds|nanoseconds|PV).*\n?', re.MULTILINE)
_PREFIX_BLACKLIST = ['IP']


def run_main(args):
    save_dir = os.path.join('record', args.uutname)
    os.makedirs(save_dir, exist_ok=True)
    epics_info_filepath = os.path.join(save_dir, "epics_info.txt")
    pvnames = get_pvnames(args.uutname)
    write_pv_info(args.uutname, pvnames, epics_info_filepath)


def get_pvnames(host):
    """get all PVs from host"""
    url = f"http://{host}/tmp/records.dbl"
    resp = requests.get(url, timeout=5)
    return sorted([line.strip() for line in resp.text.splitlines() if line.strip()])


def _pool_worker_init(progress):
    global _mp_progress
    _mp_progress = progress
    import epics.ca as ca
    from epics.ca import clear_cache
    ca.initial_context = None
    clear_cache()


def _fetch_pv_chunk(args):
    """Fetch PV info for a chunk in a worker process."""
    import epics.ca as ca
    from epics import PV

    host, pvnames, connection_timeout = args
    results = {}
    if not pvnames:
        return results

    pvs = [(name, PV(name)) for name in pvnames]
    deadline = time.time() + connection_timeout
    while time.time() < deadline:
        ca.poll()
        if all(pv.connected for _, pv in pvs):
            break

    for name, pv in pvs:
        try:
            if pv.connected:
                text = _INFO_FILTER.sub('', pv.info).replace(host, '<UUT>') + '\n\n'
                results[name] = text
            else:
                pvtype = getattr(pv, 'type', 'unknown')
                results[name] = (
                    f"== {name}  ({pvtype}) ==\n"
                    f"Unable to read info\n"
                    f"=============================\n\n"
                ).replace(host, '<UUT>')
        except Exception:
            pvtype = getattr(pv, 'type', 'unknown')
            results[name] = (
                f"== {name}  ({pvtype}) ==\n"
                f"Unable to read info\n"
                f"=============================\n\n"
            ).replace(host, '<UUT>')
        with _mp_progress.get_lock():
            _mp_progress.value += 1
    return results


def write_pv_info(host, pvnames, filename, connection_timeout=60.0):
    """Write all PV info to a file using parallel CA worker processes."""
    t0 = time.time()
    to_fetch = [
        name for name in pvnames
        if not any(name.startswith(prefix) for prefix in _PREFIX_BLACKLIST)
    ]
    skipped = set(pvnames) - set(to_fetch)
    results = {}

    if to_fetch:
        workers = min(WORKERS, len(to_fetch))
        chunk_size = (len(to_fetch) + workers - 1) // workers
        chunks = [to_fetch[i:i + chunk_size] for i in range(0, len(to_fetch), chunk_size)]
        chunk_args = [(host, chunk, connection_timeout) for chunk in chunks]

        mp_ctx = get_context('fork')
        progress = mp_ctx.Value('i', 0)
        stop_progress = Event()

        def report_progress():
            while not stop_progress.wait(0.1):
                print(f"\r\033[KGetting PV info {progress.value}/{len(to_fetch)}", end="", flush=True)
            print(f"\r\033[KGetting PV info {progress.value}/{len(to_fetch)}", end="", flush=True)

        progress_thread = Thread(target=report_progress, daemon=True)
        progress_thread.start()
        try:
            with mp_ctx.Pool(
                processes=workers,
                initializer=_pool_worker_init,
                initargs=(progress,),
                maxtasksperchild=1,
            ) as pool:
                for chunk_result in pool.imap(_fetch_pv_chunk, chunk_args):
                    results.update(chunk_result)
        finally:
            stop_progress.set()
            progress_thread.join()

    with open(filename, 'w') as fp:
        fp.write(f"Total PVs {len(pvnames)}\n")
        for pvname in pvnames:
            if pvname in skipped:
                continue
            if pvname not in results:
                results[pvname] = (
                    f"== {pvname}  (unknown) ==\n"
                    f"Unable to read info\n"
                    f"=============================\n\n"
                ).replace(host, '<UUT>')
            fp.write(results[pvname])

    print()
    print(f"EPICS PVs written to {filename}")
    print(f"Fetched {len(to_fetch)} PVs in {time.time() - t0:.1f}s")


def get_parser():
    parser = argparse.ArgumentParser(description="Generate PV info file")
    parser.add_argument("uutname", help="UUT hostname")
    return parser


if __name__ == "__main__":
    run_main(get_parser().parse_args())
