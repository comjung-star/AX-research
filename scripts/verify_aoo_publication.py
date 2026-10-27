"""Reuse the staged-blob scanner, saving only in this new run's folder."""
from types import SimpleNamespace
from scripts import aoo_experiment as run
from scripts import verify_query_isolated_publication as scanner

if __name__=='__main__':
    scanner.run=SimpleNamespace(ROOT=run.ROOT,OUTPUT=run.OUT,api=run.api,save=run.save)
    scanner.verify()
