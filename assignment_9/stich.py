import sys
import json

#
# LVN
#
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
kFoldableOps = ["add", "mul"]
def compare_tuples(t1, t2):
    if len(t1) != len(t2):
        return False

    op1 = t1[0]
    op2 = t2[0]
    if not op1 == op2:
        return False

    t1 = t1[1:]
    t2 = t2[1:]
    if op1 in kFoldableOps:
        t11 = t1[::-1]
        if (not t1 == t2) and (not t11 == t2):
            return False
    else:
        if not t1 == t2:
            return False

    return True

kFoldabelOps = {
    'add': lambda a, b: a + b,
    'mul': lambda a, b: a * b,
    'sub': lambda a, b: a - b,
    'div': lambda a, b: a // b,
    'gt': lambda a, b: a > b,
    'lt': lambda a, b: a < b,
    'ge': lambda a, b: a >= b,
    'le': lambda a, b: a <= b,
    'ne': lambda a, b: a != b,
    'eq': lambda a, b: a == b,
    'or': lambda a, b: a or b,
    'and': lambda a, b: a and b,
    'not': lambda a: not a
}

def bb_lvn(bb):
    # [((val), var)]
    lvn_table = []
    # val -> idx in lvn_table
    heap = {}
    # new instructions
    new_instrs = []
    fold_cnt = 0
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

        # Try to fold
        try:
            if instr.get("op") in kFoldabelOps:
                # check if both args are const
                both_args_const = True
                const_args = []
                for arg in instr.get("args"):
                    if not lvn_table[heap[arg]][0][0] == "const":
                        both_args_const = False
                    else:
                        const_args.append(lvn_table[heap[arg]][0][1])

                if (both_args_const):
                        if len(const_args) == 1:
                            res = kFoldabelOps[instr.get("op")](const_args[0])
                        else:
                            res = kFoldabelOps[instr.get("op")](const_args[0], const_args[1])
                        # replace with const
                        new_instrs[-1] = {"dest": instr.get("dest"), "type": instr.get("type"), "op": "const", "value": res}
                        # incr fold counter
                        fold_cnt = fold_cnt + 1


        except (ZeroDivisionError, KeyError) as error:
            continue

    return (fold_cnt, new_instrs)

#
# DCE
#
# Global simple pass
def do_dce_function_pass(instrs):
    instr_cnt = len(instrs)

    # Get what vars are ever read
    r_args = set()
    for instr in instrs:
        args = instr.get("args")
        if args:
            for arg in args:
                r_args.update({arg})

    # Remove stuff
    for instr in instrs:
        dest = instr.get("dest")
        if dest:
            if not dest in r_args:
                instrs.remove(instr)

    removed_cnt = instr_cnt - len(instrs)
    return removed_cnt

bb_terminators = 'br', 'jmp', 'ret'
def do_reassign_elimination(instrs):
    instr_cnt = len(instrs)

    # Form "basic blocks"
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

    # Per basick block
    for bb in b_blocks:
        # Make intervals: var -> [1st, 2nd, 3rd, ...]
        vars = {}
        for idx, instr in enumerate(bb):
            dst = instr.get("dest")
            if not dst in vars.keys():
                vars[dst] = [idx]
            else:
                vars[dst].append(idx)

        # Make list of usages
        var_reads = {}
        for idx, instr in enumerate(bb):
            args = instr.get("args")
            if args:
                for arg in args:
                    if not arg in var_reads.keys():
                        var_reads[arg] = [idx]
                    else:
                        if not idx in var_reads[arg]:
                            var_reads[arg].append(idx)

        # See what we can remove
        for var in vars.keys():
            intervals = vars[var]
            if not var in var_reads:
                continue
            usages = var_reads[var]
            #print(var, ":", usages, "->", intervals)
            for i in range(len(intervals) - 1):
                left = intervals[i]
                right = intervals[i+1]
                used = False
                for usage in usages:
                    if (usage > left and usage < right):
                        used = True
                        break
                if not used:
                    del instrs[left]

            # check last insstruction in each interval
            if (intervals[-1] > usages[-1]):
                del instrs[intervals[-1]]

    removed_cnt = instr_cnt - len(instrs)
    return removed_cnt

def doStich():
    bril_json = json.load(sys.stdin)

    # Load trace file.
    f = open(sys.argv[1])
    for line in f:
        trace = json.loads(line)

    # Process trace file
    new_trace = []

    # Add speculate
    new_trace.append({'op': 'speculate'})

    for t in trace:
        # Remove jumps
        if (t['op'] == 'jmp'):
            continue
        
        # Replace br with guard
        if (t['op'] == 'br'):
            t['op'] = 'guard'
            t['args'] = t['args']
            t['labels'] = ['trace_entry']

        # Just append
        new_trace.append(t)

    # Add commit
    new_trace.append({"op": "commit"})

    # Jump to the end
    new_trace.append({'op': 'jmp', 'labels': ['very_end']})

    # Add .trace_entry label
    new_trace.append({"label": 'trace_entry'})

    #
    # Apply optimizations
    #
    bb_lvn(new_trace)
    do = True
    while do:
        do = do_dce_function_pass(new_trace) > 0 or do_reassign_elimination(new_trace) > 0

    # stich into main function.
    idx = 0
    for f in bril_json['functions']:
        if f['name'] == 'main':
            for trace_i in new_trace:
                f['instrs'].insert(idx, trace_i)
                idx = idx + 1
            # append .very_end label
            f['instrs'].append({"label": 'very_end'})

    json.dump(bril_json, sys.stdout, indent=2, sort_keys=True)

if __name__ == '__main__':
    doStich()
