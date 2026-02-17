"""
Background index task queue: one worker thread consumes rebuild_index / add_chunks tasks.
Coalesces multiple rebuild_index into one. Used for non-blocking index updates.
"""
import queue
import threading
from typing import Any

from app.services.faiss_store import add_chunks_to_index, rebuild_index


def _worker_loop(task_queue: queue.Queue[dict[str, Any]]) -> None:
    while True:
        try:
            task = task_queue.get()
        except Exception:
            break
        if task is None:
            break
        t = task.get("type")
        if t == "rebuild_index":
            rebuild_index()
            while True:
                try:
                    next_task = task_queue.get_nowait()
                except queue.Empty:
                    break
                if next_task is None:
                    task_queue.put(None)
                    break
                if next_task.get("type") == "rebuild_index":
                    pass
                else:
                    task_queue.put(next_task)
                    break
        elif t == "add_chunks":
            doc_id = task.get("doc_id")
            if doc_id is not None:
                add_chunks_to_index(doc_id)


def start_index_worker(task_queue: queue.Queue[dict[str, Any]]) -> threading.Thread:
    t = threading.Thread(target=_worker_loop, args=(task_queue,), daemon=True, name="index-worker")
    t.start()
    return t


def enqueue_rebuild_index(task_queue: queue.Queue[dict[str, Any]]) -> None:
    task_queue.put({"type": "rebuild_index"})


def enqueue_add_chunks(task_queue: queue.Queue[dict[str, Any]], doc_id: int) -> None:
    task_queue.put({"type": "add_chunks", "doc_id": doc_id})
