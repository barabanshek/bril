#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/InstrTypes.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/Analysis/LoopInfo.h"

using namespace llvm;

namespace
{
  struct SkeletonPass : public FunctionPass
  {
    static char ID;
    SkeletonPass() : FunctionPass(ID) {}

    Function *monitor;

    static constexpr int kOpCodeCall = 56;
    static constexpr int kOpCodeBr = 2;
    virtual bool runOnFunction(Function &F)
    {
      // Find yield() function
      if (F.getName().find("yield") != std::string::npos)
      {
        errs() << "> I saw a function called " << F.getName() << "\n";
        monitor = &F;
        return false;
      }

      // Find a busy-waiting loop
      LoopInfo &LI = getAnalysis<LoopInfoWrapperPass>().getLoopInfo();
      for (Loop *L : LI)
      {
        // Check if this is indeed a busy-waiting loop
        // Use heuristics: low number if instructions, only `call` and `br`
        bool looks_like_busy_waiting_loop = true;
        for (auto bb = L->block_begin(), be = L->block_end(); bb != be && looks_like_busy_waiting_loop; ++bb)
        {
          for (BasicBlock::iterator instr = (*bb)->begin(), ee = (*bb)->end();
               instr != ee; ++instr)
          {
            // If the loop contains smth else besides for `call` and `br` - terminate here
            if (instr->getOpcode() != kOpCodeCall && instr->getOpcode() != kOpCodeBr)
            {
              looks_like_busy_waiting_loop = false;
            }
          }
        }

        if (!looks_like_busy_waiting_loop)
          continue;
        errs() << "> I found a busy wating loop in function " << F.getName() << "\n";

        // Insert call to yeld()
        ArrayRef<Value *> arguments;
        Instruction *newInst = CallInst::Create(monitor, arguments, "");
        auto first_bb = L->block_begin();
        auto first_instr = (*first_bb)->begin();
        first_instr++;
        ((*first_bb)->getInstList()).insert(first_instr, newInst);
        errs() << "> Instruction inserted " << newInst->getOpcodeName() << "\n";

        // Dump new loop
        for (auto bb = L->block_begin(), be = L->block_end(); bb != be; ++bb)
        {
          for (BasicBlock::iterator instr = (*bb)->begin(), ee = (*bb)->end();
               instr != ee; ++instr)
          {
            errs() << *instr << "\n";
          }
        }
      }

      return false;
    }

    void getAnalysisUsage(AnalysisUsage &AU) const
    {
      AU.addRequired<LoopInfoWrapperPass>();
      return;
    }
  };
}

char SkeletonPass::ID = 0;

// Automatically enable the pass.
// http://adriansampson.net/blog/clangpass.html
static void registerSkeletonPass(const PassManagerBuilder &,
                                 legacy::PassManagerBase &PM)
{
  PM.add(new SkeletonPass());
}
static RegisterStandardPasses
    RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible,
                   registerSkeletonPass);
