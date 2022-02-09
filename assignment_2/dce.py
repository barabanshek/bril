import sys
import json

# Global simple pass
def do_dce_function_pass(function):
    instrs = function['instrs']
    instr_cnt = len(instrs)

    # Get what vars are ever read
    r_args = set()
    for instr in instrs:
        args = instr.get("args")
        if args:
            for arg in args:
                r_args.update(arg)

    # Remove stuff
    for instr in instrs:
        dest = instr.get("dest")
        if dest:
            if not dest in r_args:
                instrs.remove(instr)

    removed_cnt = instr_cnt - len(instrs)
    return removed_cnt

bb_terminators = 'br', 'jmp', 'ret'
def do_reassign_elimination(function):
    instrs = function['instrs']
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
                        var_reads[arg].append(idx)
    
        # See what we can remove
        for var in vars.keys():
            intervals = vars[var]
            if not var in var_reads:
                continue
            usages = var_reads[var]
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

    removed_cnt = instr_cnt - len(instrs)
    return removed_cnt

def do_dce_function_pass_converge(function):
    do_reassign_elimination(function)
    do = True
    while do:
        do = do_dce_function_pass(function) > 0 or do_reassign_elimination(function) > 0

def doTrivialDCE():
    bril_json = json.load(sys.stdin)

    for f in bril_json['functions']:
        do_dce_function_pass_converge(f)

    json.dump(bril_json, sys.stdout, indent=2, sort_keys=True)

def doOpt():
    doTrivialDCE()

if __name__ == '__main__':
    doOpt()
