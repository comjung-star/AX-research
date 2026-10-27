"""Static figure from saved offline results; no model inference."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts import candidate_fusion_ablation as c

def main():
    d=c.read(c.OUT/'results.json')['aggregate'];fig,axes=plt.subplots(1,2,figsize=(10.5,4),layout='constrained')
    labels={'original':'Original query','round_robin':'Round robin','mean_rrf':'Mean RRF','original_plus_mean_rrf':'Original + mean RRF (1:1)'}
    colors=['#666666','#CC6677','#4477AA','#228833']
    for ax,backbone,title in zip(axes,c.BACKBONES,['Single Dense','3-View Dense']):
        for (method,label),color in zip(labels.items(),colors):
            ax.plot(c.CFG['K'],[100*d[backbone+'__'+method][str(k)]['macro_f1'] for k in c.CFG['K']],marker='o',color=color,label=label,linestyle='--' if method=='original' else '-')
        ax.set_title(title);ax.set_xlabel('Final recommendations K');ax.set_ylabel('Macro F1 (%)');ax.set_xticks(c.CFG['K']);ax.set_ylim(0,46);ax.grid(alpha=.25)
    axes[1].legend(fontsize=8)
    fig.suptitle('Fixed input ranks, RRF constant60; no parameter search\nDEV AI-Silver: F1 defined for6 of10 queries, dynamic repeats averaged within query',fontsize=10)
    fig.savefig(c.OUT/'fusion_comparison.png',dpi=180);fig.savefig(c.OUT/'fusion_comparison.svg');plt.close(fig)
    p=c.OUT/'fusion_comparison.svg';p.write_text('\n'.join(x.rstrip() for x in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
if __name__=='__main__':main()
