#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/InstrTypes.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/Analysis/LoopInfo.h"

#include <vector>

using namespace llvm;

namespace
{
  struct SkeletonPass : public FunctionPass
  {
    static char ID;
    SkeletonPass() : FunctionPass(ID) {}

    static constexpr size_t kOpCodeBr = 2;

    void print_bb(BasicBlock *bb)
    {
      for (BasicBlock::iterator instr = bb->begin(), ee = bb->end();
           instr != ee; ++instr)
      {
        errs() << "    " << *instr << "\n";
      }
    }

    void print_loop(Loop *loop)
    {
      BasicBlock *preheader = loop->getLoopPreheader();
      errs() << "------- PREHEADER_BB --------"
             << "\n";
      print_bb(preheader);
      for (auto bb = loop->block_begin(), be = loop->block_end(); bb != be; ++bb)
      {
        errs() << "------- BB --------"
               << "\n";
        print_bb(*bb);
      }
    }

    virtual bool runOnFunction(Function &F)
    {
      // Find a busy-waiting loop
      LoopInfo &LI = getAnalysis<LoopInfoWrapperPass>().getLoopInfo();
      for (Loop *L : LI)
      {
        errs() << "> I found a loop in function " << F.getName() << "\n";
        print_loop(L);

        // Get pre-header
        BasicBlock *preheader = L->getLoopPreheader();

        bool do_ = true;
        while (do_)
        {
          // List of instructions to move
          std::vector<BasicBlock::iterator> instr_to_move;

          for (auto bb = L->block_begin(), be = L->block_end(); bb != be; ++bb)
          {
            // Work with instructions.
            for (BasicBlock::iterator instr = (*bb)->begin(), ee = (*bb)->end();
                 instr != ee; ++instr)
            {
              const Instruction *V = &(*instr);
              if (L->isLoopInvariant (V))
              {
                // We don't move the following instructions:
                //  if it's in loop header or footer
                if (bb == L->block_begin() || bb == L->block_end() - 1)
                  continue;

                //  if it's a branch instruction (let's be conservative)
                if (instr->getOpcode() == kOpCodeBr)
                  continue;

                instr_to_move.push_back(instr);
              }
            }
          }

          // Move
          for (auto i : instr_to_move)
          {
            errs() << "   TO MOVE: " << *(i) << "\n";
          }

          if (instr_to_move.size() > 0) {
            Instruction *end = &(preheader->back());
            instr_to_move[0]->moveBefore(end);
          } else {
            do_ = false;
          }

          errs() << "-----------------------------------------"
                 << "\n";
          print_loop(L);
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
