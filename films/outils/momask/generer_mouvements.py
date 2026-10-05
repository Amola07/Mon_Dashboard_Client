"""Génère des mouvements (articulations 3D, 20 i/s) à partir de phrases, avec MoMask, sur CPU.
    python generer_mouvements.py sortie_dossier "phrase 1#60" "phrase 2#80"   (#n = nombre d'images, multiple de 4)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim"))
import numpy as np, torch
from os.path import join as pjoin
sys.argv = [sys.argv[0]] + ["--gpu_id", "-1", "--ext", "x"] + ["__SEP__"] + sys.argv[1:]
sep = sys.argv.index("__SEP__"); args = sys.argv[sep + 1:]; sys.argv = sys.argv[:sep]
from options.eval_option import EvalT2MOptions
from utils.get_opt import get_opt
from utils.fixseed import fixseed
from utils.motion_process import recover_from_ric
import types
for nom, attr in (("visualization.joints2bvh", "Joint2BVHConvertor"), ("utils.plot_script", "plot_3d_motion")):
    mod = types.ModuleType(nom); setattr(mod, attr, None); sys.modules[nom] = mod
import gen_t2m as G

opt = EvalT2MOptions().parse()
fixseed(opt.seed)
opt.device = torch.device("cpu")
torch.set_num_threads(4)
root = pjoin(opt.checkpoints_dir, opt.dataset_name, opt.name)
model_opt = get_opt(pjoin(root, "opt.txt"), device=opt.device)
vq_opt = get_opt(pjoin(opt.checkpoints_dir, opt.dataset_name, model_opt.vq_name, "opt.txt"), device=opt.device)
vq_opt.dim_pose = 263
vq_model, vq_opt = G.load_vq_model(vq_opt)
model_opt.num_tokens, model_opt.num_quantizers, model_opt.code_dim = vq_opt.nb_code, vq_opt.num_quantizers, vq_opt.code_dim
res_opt = get_opt(pjoin(opt.checkpoints_dir, opt.dataset_name, opt.res_name, "opt.txt"), device=opt.device)
res_model = G.load_res_model(res_opt, vq_opt, opt)
t2m = G.load_trans_model(model_opt, opt, "latest.tar")
for m in (t2m, vq_model, res_model):
    m.eval()
mean = np.load(pjoin(opt.checkpoints_dir, opt.dataset_name, model_opt.vq_name, "meta", "mean.npy"))
std = np.load(pjoin(opt.checkpoints_dir, opt.dataset_name, model_opt.vq_name, "meta", "std.npy"))
out = args[0]; os.makedirs(out, exist_ok=True)
for i, a in enumerate(args[1:]):
    texte, n = a.split("#")
    n = int(n)
    with torch.no_grad():
        lens = torch.LongTensor([n // 4])
        ids = t2m.generate([texte], lens, timesteps=opt.time_steps, cond_scale=opt.cond_scale,
                           temperature=opt.temperature, topk_filter_thres=opt.topkr, gsample=opt.gumbel_sample)
        ids = res_model.generate(ids, [texte], lens, temperature=1, cond_scale=5)
        mot = vq_model.forward_decoder(ids).cpu().numpy()[0] * std + mean
    j = recover_from_ric(torch.from_numpy(mot[:n]).float(), 22).numpy()
    np.save(pjoin(out, f"m{i}.npy"), j)
    print(i, texte, j.shape)
