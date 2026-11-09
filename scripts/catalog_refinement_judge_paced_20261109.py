"""Same frozen blind judge jobs with conservative Gemini start spacing only."""
import threading
import time

from scripts import catalog_refinement_execution_20261109 as execution


if __name__=='__main__':
    execution.guarded()
    original=execution.run.one_call
    lock=threading.Lock()
    next_start=[0.]
    def paced(name,provider,request):
        if provider=='gemini':
            with lock:
                delay=max(0,next_start[0]-time.monotonic())
                if delay:time.sleep(delay)
                next_start[0]=time.monotonic()+15
        return original(name,provider,request)
    execution.run.one_call=paced
    execution.judge()
