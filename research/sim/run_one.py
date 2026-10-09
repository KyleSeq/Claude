import sys, json
from economy_sim import study, show, BASE
import proposals
cfg = {"base":BASE,"G":proposals.RECOMMENDED}[sys.argv[1]]
res=study(cfg,int(sys.argv[2]),int(sys.argv[3])); show(cfg,res)
json.dump(res,open(f"results_{sys.argv[1]}.json","w"),indent=1)
