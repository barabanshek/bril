import sys
import json

### Passes
def merge_const_prop(var_list):
#    print("merge:")
#    print(var_list)
    ret = {}
    for var in var_list:
        for k,v in var.items():
            if k in ret.keys():
                # if same, just use it, otherwise mark '?'
                if not ret[k] == v:
                    ret[k] = '?'
            else:
                ret[k] = v
#    print(ret)
    return ret

def transfer_const_prop(bb, bb_in):
#    print("transfer:", bb[0])
#    print(bb_in)
    ret = {}
    for k,v in bb_in.items():
        ret[k] = v

    for instr in bb:
        if instr.get("op") in ['br', 'jmp', 'ret', 'print'] or instr.get("label"):
            continue

        if instr.get("dest") in bb_in.keys():
            # potentially re-write prev. value
            # check if we can do const prop
            if instr.get("op") == "const":
                # re-write
                ret[instr.get("dest")] = instr.get("value")
            else:
                # propagate
                ret[instr.get("dest")] = "?"
        else:
            # add new variable
            # check if const
            if instr.get("op") == "const":
                ret[instr.get("dest")] = instr.get("value")
            else:
                # propagate
                ret[instr.get("dest")] = "?"

    return (not bb_in == ret), ret

#
# constant propagation
#
mergers = {'const_prop': merge_const_prop}
transfers = {'const_prop': transfer_const_prop}

def do_df_pass(function, merge, transfer):
    cfg = form_cfg(function)

    # loop
    worklist = list(range(len(cfg)))
    while worklist:
        bb_idx = worklist.pop(0)
    #    print(bb_idx, ":", cfg[bb_idx]['pred'])
        cfg[bb_idx]['in'] = merge([cfg[p]['out'] for p in cfg[bb_idx]['pred']])
    #    print(bb_idx, ":", cfg[bb_idx]['in'])
        changed, cfg[bb_idx]['out'] = transfer(cfg[bb_idx]['bb'], cfg[bb_idx]['in'])
    #    print(bb_idx, ":", cfg[bb_idx]['out'])
        if changed:
        #    print(bb_idx, ":successors:", cfg[bb_idx]['succ'])
            worklist.extend([p for p in cfg[bb_idx]['succ']])

    return cfg

def print_cfg_result(cfg):
    for c in cfg:
        print(c['bb'][0], ":")
        print("    ", "in: ", c['in'])
        print("    ", "out: ", c['out'])

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
            if not instrs[idx - 1].get("op") in ['br', 'jmp', 'ret']:
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
        cfg = do_df_pass(f, mergers[pass_name], transfers[pass_name])
        print_cfg_result(cfg)

def doOpt():
    doDfPass('const_prop')

if __name__ == '__main__':
    doOpt()
