import sys
import json

bb_terminators = 'br', 'jmp', 'ret'
def form_bbs(function):
    instrs = function['instrs']
    b_blocks = []
    b_block = []
    for instr in instrs:
        if instr.get("op") in bb_terminators:
            b_block.append(instr)
            b_blocks.append(b_block)
            b_block = []
        else:
            b_block.append(instr)
    b_blocks.append(b_block)
    return b_blocks

def flatten_bbs(bbs):
    instrs = []
    for bb in bbs:
        for instr in bb:
            instrs.append(instr)
    return instrs

# For more advanced lvn optimizations (e.g. commutative property), add in here
def compare_tuples(t1, t2):
    if len(t1) != len(t2):
        return False
    else:
        for e1, e2 in zip(t1, t2):
            if e1 != e2:
                return False
    return True

def bb_lvn(bb):
    # [((val), var)]
    lvn_table = []
    # val -> idx in lvn_table
    heap = {}
    # new instructions
    new_instrs = []
    for instr in bb:
        # form touple val
        val_tuple = []
        val_tuple.append(instr.get("op"))

        # look-up args/values
        if instr.get("args") == None:
            if not instr.get("value") == None:
                val_tuple.append(instr.get("value"))
        else:
            for arg in instr.get("args"):
                if arg in heap.keys():
                    val_tuple.append(heap[arg])
                else:
                    val_tuple.append(arg)

        # check if such a tuple already exists
        resolved = False
        for idx, (val_t, var_t) in enumerate(lvn_table):
            if compare_tuples(val_t, val_tuple):
                # don't add, just append another val in the heap
                heap[instr.get("dest")] = idx
                resolved = True

                # Generate code with id instruction
                new_instrs.append({"dest": instr.get("dest"), "type": instr.get("type"), "op": "id", "args": [lvn_table[idx][1]]})
                break

        if not resolved:
            # add new tuple entry and append in the heap
            lvn_table.append((val_tuple, instr.get("dest")))
            heap[instr.get("dest")] = len(lvn_table) - 1

            # Generate code
            if not instr.get("args"):
                new_instrs.append(instr)
            else:
                new_args = []
                for arg in instr.get("args"):
                    if arg in heap:
                        new_args.append(lvn_table[heap[arg]][1])
                    else:
                        new_args.append(arg)
                instr["args"] = new_args
                new_instrs.append(instr)

    return new_instrs

# Simple lvn pass
def do_lvn_pass(function):
    instrs = function['instrs']
    instr_cnt = len(instrs)

    bbs = form_bbs(function)
    new_bbs = []
    for bb in bbs:
        new_bbs.append(bb_lvn(bb))
    
    function['instrs'] = flatten_bbs(new_bbs)

def doLvn():
    bril_json = json.load(sys.stdin)

    for f in bril_json['functions']:
        do_lvn_pass(f)

    json.dump(bril_json, sys.stdout, indent=2, sort_keys=True)

def doOpt():
    doLvn()

if __name__ == '__main__':
    doOpt()
