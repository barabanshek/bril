import sys
import json
import graphviz
from copy import deepcopy

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
                if (v in doms[pred]):
                    p_dom.append(ndn)

        frontier[v] = p_dom

    return frontier

def dfs(cfg, path, node, target_node, paths):
    l_path = path.copy()
    l_path.append(node)
    if node == target_node:
        paths.append(l_path)
    else:
        cfg[node]['in'] = 1
        for succ in cfg[node]['succ']:
            if not cfg[succ]['in'] == 1:
                dfs(cfg, l_path, succ, target_node, paths)

def find_all_paths(cfg, node1, node2):
    paths = []
    dfs(cfg, [], node1, node2, paths)
    return paths

def check_dom(cfg, doms):
    for v, ds in doms.items():
        for d in ds:
            if not d == v:
                # d dominates v
                # check that all paths to v contain d
                paths = find_all_paths(cfg, 0, v)
                for path in paths:
                    if not d in path:
                        return False
    return True

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

def insert_phi(cfg, b, v, args, labels, type_):
    phi = {
        'op': 'phi',
        'dest': v,
        'type': type_,
        'labels': labels,
        'args': args,
    }
    cfg[b]['bb'].insert(1, phi)

cnt = 0
def rename(bb_n, cfg, dom_tree, stack_):
    stack_internal = deepcopy(stack_)
    #print("bb= ", bb_n)
    #print("stack_internal_before= ", stack_internal)
    #print("bb_instr= ", cfg[bb_n])
    global cnt
    bb = cfg[bb_n]
    for instr in bb['bb']:
        if instr.get('op') and (not instr['op'] == 'phi'):
            args = instr.get('args')
            if args:
                for i, arg in enumerate(args):
                    old_name = stack_internal[arg][-1]
                    args[i] = old_name

        dest = instr.get('dest')
        if dest:
            new_name =  dest + '_' + str(cnt)
            instr['dest'] = new_name
            stack_internal[dest].append(new_name)
            cnt = cnt + 1

    for s in bb['succ']:
        bb_name = bb['bb'][0]['label']
        succ_bb = cfg[s]
        for instr in succ_bb['bb']:
            if instr.get('op'):
                if instr['op'] == 'phi':
                    idx = instr['labels'].index(bb_name)
                    instr['args'][idx] = stack_internal[instr['args'][idx]][-1]

    #print("stack_internal_after= ", stack_internal)
    for d in dom_tree[bb_n]:
    #    print(bb_n)
    #    print("stack_internal_CALL= ", stack_internal)
        rename(d, cfg, dom_tree, stack_internal)

def do_ssa(cfg, frontier, dom_tree):
#    print("cfg= ", cfg)
    vars_ = {}
    types_ = {}
    for dd_idx, bb in enumerate(cfg):
        for instr in bb['bb']:
            dest = instr.get('dest')
            type_ = instr.get('type')
            types_[dest] = type_
            if dest:
                if not dest in vars_.keys():
                    vars_[dest] = [dd_idx]
                else:
                    vars_[dest].append(dd_idx)
#    print("Vars= ", vars_)

    # insert Fi-nodes
    for v in vars_.keys():
        for d in vars_[v]:
            if d in frontier:
                df = frontier[d]
                for b in df:
                    insert_phi(cfg, b, v, [v, v], [cfg[x]['bb'][0]['label'] for x in cfg[b]['pred']], types_[v])
                    if not b in vars_[v]:
                        vars_[v].append(b)

    # rename
    stack_ = {}
    for v in vars_:
        stack_[v] = []
        stack_[v].append(v)

    rename(0, cfg, dom_tree, stack_)

def cfg_to_f(f, cfg):
    new_f = []
    for bb in cfg:
        for instr in bb['bb']:
            new_f.append(instr)
    f["instrs"] = new_f

def doDfPass(pass_name):
    bril_json = json.load(sys.stdin)

    for f in bril_json['functions']:
        cfg = form_cfg(f)
        doms = get_dominators(cfg)
    #    print("Dominators:\n", doms)
        dom_tree = construct_dom_tree(doms)
    #    print("Dominator tree:\n", dom_tree)
        frontier = compute_dom_front(cfg, doms)
    #    print("Domination Fronties:\n", frontier)
    #    print("Correctness for get_dominators() -> ", check_dom(cfg, doms))

        # SSA
        do_ssa(cfg, frontier, dom_tree)
        cfg_to_f(f, cfg)

    # Dump new cfg
    json.dump(bril_json, sys.stdout, indent=2, sort_keys=True)


def doOpt():
    doDfPass('const_prop')

if __name__ == '__main__':
    doOpt()
