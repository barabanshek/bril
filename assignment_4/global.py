import sys
import json
import graphviz

def intersection(lst1, lst2):
    if lst2 == None:
        return lst1
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def union(lst1, lst2):
    final_list = lst1 + lst2
    return final_list

def get_dominators(cfg):
    # {block -> blocks}
    dom = {}
    for i, bb in enumerate(cfg):
        dom[i] = None

    do = True
    while do:
        do = False
        for v_id, v in enumerate(cfg):
            old_dom = dom[v_id]

            # init
            if dom[v_id] == None:
                dom[v_id] = []

            # add itself
            dom[v_id] = [v_id]

            # add pred
            if len(v['pred']) > 0:
                inter_list = dom[v['pred'][0]]
                for idx in range(1, len(v['pred'])):
                    p = v['pred'][idx]
                    inter_list = intersection(inter_list, dom[p])
                dom[v_id] = dom[v_id] + inter_list

            # check for change
            if old_dom != dom[v_id]:
                do = True

    return dom

def construct_dom_tree(doms):
    # {node_id -> children_id}
    tree = {}
    for i in range(len(doms)):
        tree[i] = []

    for idx in range((len(doms) - 1), -1, -1):
        ds = doms[idx]
        for i in range(len(ds) - 1):
            if not ds[i] in tree[ds[i+1]]:
                tree[ds[i+1]].append(ds[i])
    
    return tree

def compute_dom_front(cfg, doms):
    # {node_id -> [frontier]}
    frontier = {}
    
    for v in doms.keys():
        # find what this node does NOT strictly dominate
        no_dom = []
        for v1, ds in doms.items():
            if (not v1 == v) and (not v in ds):
                no_dom.append(v1)
        if no_dom == []:
            continue

        # check if it dominates any pred maybe
        p_dom = []
        for ndn in no_dom:
            preds = cfg[ndn]['pred']
            for pred in preds:
                if (not pred == v) and (v in doms[pred]):
                    p_dom.append(ndn)

        frontier[v] = p_dom

    return frontier

def form_cfg(function):
    instrs = function['instrs']

    # Generate cfg
    bb = []
    cfg = [] # [{'bb' -> bb, 'pred' -> [bb], 'succ' -> [bb], 'in' = {}, 'out' = {}}]
    for idx, instr in enumerate(instrs):
        # Split by terminators
        if instr.get("op") in ['br', 'jmp', 'ret']:
            bb.append(instr)
            # create cfg entry
            cfg.append({'bb': bb, 'pred': [], 'succ': [], 'in': {}, 'out': {}})
            bb = []
        elif instr.get("label"):
            if idx > 1 and (not instrs[idx - 1].get("op") in ['br', 'jmp', 'ret']):
                # split by label
                cfg.append({'bb': bb, 'pred': [], 'succ': [], 'in': {}, 'out': {}})
                bb = []
                bb.append(instr)
            else:
                bb.append(instr)
        else:
            bb.append(instr)
    # Append last
    cfg.append({'bb': bb, 'pred': [], 'succ': [], 'in': {}, 'out': {}})

    # For each bb in cfg, generate predecessors and successors
    for bb_idx, bb in enumerate(cfg):
        bb_first_instr = bb['bb'][0]
        bb_first_instr_label = bb_first_instr.get("label")
        if bb_first_instr_label:
            # this block has predecessors, find them
            # based on prev block
            if (bb_idx > 0) and (not cfg[bb_idx - 1]['bb'][-1].get("op") in ['br', 'jmp']):
                bb['pred'].append(bb_idx - 1)
                cfg[bb_idx - 1]['succ'].append(bb_idx)
            # based on jumps/branches
            for p_bb_idx, p_bb in enumerate(cfg):
                pbb_last_instr = p_bb['bb'][-1]
                if pbb_last_instr.get("op") in ['br', 'jmp']:
                    for label in pbb_last_instr.get("labels"):
                        if label == bb_first_instr_label:
                            # append pred
                            bb['pred'].append(p_bb_idx)
                            # append succ in the corresponding block
                            p_bb['succ'].append(bb_idx)

    return cfg

def doDfPass(pass_name):
    bril_json = json.load(sys.stdin)

    for f in bril_json['functions']:
        cfg = form_cfg(f)
        doms = get_dominators(cfg)
        print("Dominators:\n", doms)
        dom_tree = construct_dom_tree(doms)
        print("Dominator tree:\n", dom_tree)
        frontier = compute_dom_front(cfg, doms)
        print("Domination Fronties:\n", frontier)

def doOpt():
    doDfPass('const_prop')

if __name__ == '__main__':
    doOpt()
