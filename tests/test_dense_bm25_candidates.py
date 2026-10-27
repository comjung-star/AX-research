from fractions import Fraction
import pytest
from scripts import dense_bm25_candidates as c

def test_channel_weights_and_exact_score():
    order,score=c.channel_fuse(['a','b','c'],['c','b','a'])
    assert score['a']==Fraction(1,61)/2+Fraction(1,63)/2
    assert score['a']==score['c'] and order.index('a')<order.index('c')

def test_identical_channels_recover_dense_order():
    ids=['c','a','b'];order,_=c.channel_fuse(ids,ids);assert order==ids

def test_duplicate_all_perspectives_does_not_inflate_score():
    _,a=c.channel_fuse(['a','b'],['b','a']);_,b=c.channel_fuse(['a','b'],['a','b'])
    assert c.mean_path_scores([a,b])==c.mean_path_scores([a,b,a,b])

def test_outer_is_mean_of_local_scores_not_second_rrf():
    _,a=c.channel_fuse(['a','b'],['a','b']);_,b=c.channel_fuse(['b','a'],['a','b'])
    _,m=c.mean_path_scores([a,b]);assert m['a']==(a['a']+b['a'])/2

def test_full112_and_deterministic_ties():
    ids=[str(i) for i in range(112)];rank,_=c.channel_fuse(ids,list(reversed(ids)));assert len(set(rank))==112
    with pytest.raises(AssertionError):c.channel_fuse(['a','a'],['a','b'])

def test_primary_and_matched_controls_are_fixed():
    assert c.CONDITIONS['C']['reference']=='A' and c.CONDITIONS['F']['reference']=='D'
    assert c.CONDITIONS['S_C3']['reference']=='B' and c.CONDITIONS['S_F3']['reference']=='E'
    assert c.CFG['api_calls']==0 and c.CFG['new_dense_embeddings']==0

def test_one_view_outer_operator_reduces_to_same_hybrid():
    ranking,scores=c.channel_fuse(['c','a','b'],['a','b','c'])
    assert c.mean_path_scores([scores])==(ranking,scores)

def test_only_source_code_gets_eol_normalization(tmp_path,monkeypatch):
    monkeypatch.setattr(c,'ROOT',tmp_path)
    source=tmp_path/'src/ax_research/retrieval/bm25.py';source.parent.mkdir(parents=True);source.write_bytes(b'x\r\n')
    first=c.fingerprint(source);source.write_bytes(b'x\n');assert c.fingerprint(source)==first
    data=tmp_path/'dataset.csv';data.write_bytes(b'x\r\n');first=c.fingerprint(data);data.write_bytes(b'x\n');assert c.fingerprint(data)!=first
