"""Standalone research figure; generated from saved metrics without API calls."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts import openai_triplicate as r

def main():
    b=r.read(r.OUT/'stage2_results.json');c=r.read(r.OUT/'stage3_results.json');allmetrics={**b['aggregate'],**c['aggregate']}
    labels={'A_single_dense':'A: Original / Single','B_three_view_dense':'B: Original / 3-View','BM25_auxiliary':'BM25','C_dynamic_single_dense':'C: Perspectives / Single','D_dynamic_three_view_dense':'D: Perspectives / 3-View'}
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    colors=['#4477AA','#EE6677','#999999','#228833','#AA3377']
    for ax,field in zip(axes,('precision','recall','f1')):
        for (name,text),color in zip(labels.items(),colors):
            ax.plot([5,10,20],[allmetrics[name][str(k)]['macro_'+field]*100 for k in (5,10,20)],marker='o',label=text,color=color)
        ax.set_title('Macro '+field.upper());ax.set_xlabel('Final recommendations K');ax.set_ylabel('Percent');ax.set_xticks([5,10,20]);ax.grid(alpha=.25)
        ax.set_ylim(bottom=0)
    axes[-1].legend(fontsize=8,loc='best');fig.suptitle('112 AX cases / same-model triplicate AI-Silver / P:10 queries, R-F1:6 Silver-positive queries\nDynamic: 3 generations per query; deterministic baseline evaluated once',fontsize=10)
    fig.savefig(r.OUT/'retrieval_comparison.png',dpi=170);fig.savefig(r.OUT/'retrieval_comparison.svg');plt.close(fig)
    svg=r.OUT/'retrieval_comparison.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
if __name__=='__main__':main()
