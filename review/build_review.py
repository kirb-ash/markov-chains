import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from collections import Counter
import refs
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
R=refs.R
# ---- Fig: evidence chart
cats=["HW","OS","TIER","LLM"]
groups=[("Simulator / trace",["SIM","TRACE","MIX"],"#4C72B0"),("Real system",["REAL"],"#DD8452"),("Survey / no evaluation",["SURV","CONC"],"#8C8C8C"),("Not verified / not visible",["NV"],"#C9C9C9")]
fig,ax=plt.subplots(figsize=(7.2,3.6),dpi=200)
bottoms=[0]*4
for name,keys,col in groups:
    vals=[sum(1 for r in R if r['cat']==c and r['plat'] in keys) for c in cats]
    ax.barh(range(4),vals,left=bottoms,color=col,label=name,edgecolor="white")
    for i,v in enumerate(vals):
        if v: ax.text(bottoms[i]+v/2,i,str(v),ha="center",va="center",color="white" if col!="#C9C9C9" else "black",fontsize=9)
    bottoms=[b+v for b,v in zip(bottoms,vals)]
ax.set_yticks(range(4)); ax.set_yticklabels([refs.CATNAME[c] for c in cats],fontsize=9); ax.invert_yaxis()
ax.set_xlabel("Number of reviewed papers (n = %d)"%len(R)); ax.legend(fontsize=8,loc="lower right",frameon=False)
for s in ("top","right"): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig("../figures/fig_evidence.png"); plt.close()
# ---- Fig: taxonomy
fig,ax=plt.subplots(figsize=(7.4,4.2),dpi=200); ax.axis("off"); ax.set_xlim(0,10); ax.set_ylim(0,6)
def box(x,y,w,h,txt,fc,fs=8.5,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.05",fc=fc,ec="#444",lw=0.8,zorder=3))
    ax.text(x+w/2,y+h/2,txt,ha="center",va="center",zorder=4,fontsize=fs,fontweight="bold" if bold else "normal",wrap=True)
box(3.2,5.1,3.6,0.7,"Prefetching to hide memory and I/O latency","#E8E8E8",9.5,True)
cols=[("Hardware and ML\ncache prefetchers",0.1,"#DCE6F2",["Spatial / delta\n(Gaze, Pathfinder)","Learned: NN, RL, LLM-designed\n(DART, Athena, MoP)","Coordination and throttling\n(Athena, Themis)"]),
      ("OS-level and\npage-cache",2.6,"#FBE5D6",["Far-memory page\nprediction (FarSight, Memix)","Programmable policy\n(FetchBPF, cache_ext)","GPU unified memory\n(ObservUVM)"]),
      ("Tiered and\nCXL memory",5.1,"#E2F0D9",["Page migration\n(Nomad, Jenga, ARMS)","Prefetch plus tiers\n(Linden)","Surveys and tuning\n(CXL survey, Kanellis)"]),
      ("LLM-era\nprefetching",7.6,"#EADCF2",["KV-cache prefetch\n(InfiniGen, OasisKV)","SSD / storage offload\n(Tutti, NeuroPrefetcher)","Retrieval prefetch\n(RAG)"])]
for name,x,fc,kids in cols:
    box(x,3.9,2.3,0.8,name,fc,8.5,True)
    ax.plot([5,5],[5.1,4.95],color="#444",lw=0.8); ax.plot([1.25,8.75],[4.95,4.95],color="#444",lw=0.8)
    ax.plot([x+1.15,x+1.15],[4.95,4.7],color="#444",lw=0.8)
    for i,k in enumerate(kids):
        yy=2.75-i*1.05
        box(x+0.05,yy,2.2,0.8,k,"white",7.2)
        ax.plot([x+1.15,x+1.15],[3.9,yy+0.8] if i==0 else [yy+1.85,yy+0.8],color="#444",lw=0.6,zorder=1)
plt.tight_layout(); plt.savefig("../figures/fig_taxonomy.png"); plt.close()
# ---- xlsx
wb=Workbook(); ws=wb.active; ws.title="Literature matrix"
hdr=["#","Authors","Title","Venue / source","Year","Category","Evaluation platform","Technique","Reported result (as stated by authors)","Disadvantage / stated limitation","Verification","YOUR NOTES (read it, add your view)"]
ws.append(hdr)
n=len(refs.CLASSIC)
for i,r in enumerate(R,start=n+1):
    ws.append([i,r['a'],r['t'],r['v'],r['y'],refs.CATNAME[r['cat']],refs.PLATNAME[r['plat']],r['tech'],r['res'],r['dis'],"Verified on source page" if r['s']=="V" else "Partial: title/venue only, read it yourself",""])
for c in ws[1]:
    c.font=Font(bold=True,color="FFFFFF"); c.fill=PatternFill("solid",fgColor="305496"); c.alignment=Alignment(wrap_text=True,vertical="center")
for col,w in zip("ABCDEFGHIJKL",[4,30,45,32,6,22,16,45,40,45,22,45]): ws.column_dimensions[col].width=w
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment=Alignment(wrap_text=True,vertical="top")
ws.freeze_panes="D2"
ws2=wb.create_sheet("Background (pre-2024)")
ws2.append(["#","Authors","Title","Venue","Year"])
for i,r in enumerate(refs.CLASSIC,start=1): ws2.append([i,r['a'],r['t'],r['v'],r['y']])
for col,w in zip("ABCDE",[4,40,60,60,6]): ws2.column_dimensions[col].width=w
ws3=wb.create_sheet("How to use")
for line in ["Read each paper's abstract, intro and limitations. Then fill the YOUR NOTES column in your own words.",
 "Rows marked 'Partial' were only seen as title/venue in a search or index. Open the real paper before you cite details.",
 "'Disadvantage' is taken from what the authors say, or flagged as not stated; it is a starting point, not your analysis.",
 "Numbers are the authors' own and come from different setups, so do not compare them across rows."]: ws3.append([line])
ws3.column_dimensions["A"].width=140
wb.save("/mnt/user-data/outputs/literature_matrix.xlsx")
print("ok", Counter(r['plat'] for r in R))
