use std::collections::HashMap;
use std::convert::TryFrom;

use serde_json::Value;

use crate::ir_types::{Operation, Type, ValueOp, EffectOp};
use crate::basic_block::BBProgram;

#[derive(Debug,Clone)]
enum BrilValue {
    Int(i64),
    Bool(bool),
}

impl BrilValue {
    fn new(typ: Type, value: Value) -> Result<BrilValue, InterpError> {
        match typ {
            Type::Int => match value.as_i64() {
                Some(i) => Ok(BrilValue::Int(i)),
                _ => Err(InterpError::BadJsonInt),
            },
            Type::Bool => match value.as_bool() {
                Some(b) => Ok(BrilValue::Bool(b)),
                _ => Err(InterpError::BadJsonBool),
            },
        }
    }

    fn get_type(&self) -> Type {
        match self {
            BrilValue::Int(..) => Type::Int,
            BrilValue::Bool(..) => Type::Bool,
        }
    }
}

impl TryFrom<BrilValue> for i64 {
    type Error = InterpError;
    fn try_from(value: BrilValue) -> Result<i64, InterpError> {
        match value {
            BrilValue::Int(i) => Ok(i),
            _ => Err(InterpError::BadValueType(Type::Int, value.get_type().clone())),
        }
    }
}

impl TryFrom<BrilValue> for bool {
    type Error = InterpError;
    fn try_from(value: BrilValue) -> Result<bool, InterpError> {
        match value {
            BrilValue::Bool(b) => Ok(b),
            _ => Err(InterpError::BadValueType(Type::Bool, value.get_type().clone())),
        }
    }
}

#[derive(Debug)]
pub enum InterpError {
    BadJsonInt,
    BadJsonBool,
    NoMainFunction,
    BadNumArgs(usize, usize), // (expected, actual)
    VarNotFound(String),
    BadAsmtType(Type, Type), // (expected, actual). For when the LHS type of an instruction is bad
    LabelNotFound(String),
    BadValueType(Type, Type), // (expected, actual)
}

fn check_asmt_type(expected: Type, actual: Type) -> Result<(), InterpError> {
    if expected == actual {
        return Ok(());
    }
    Err(InterpError::BadAsmtType(expected, actual))
}

fn get_args<T>(
    vars: &HashMap<String, BrilValue>,
    arity: usize,
    args: Vec<String>
    ) -> Result<Vec<T>, InterpError>
where T: TryFrom<BrilValue>,
      InterpError: std::convert::From<<T as TryFrom<BrilValue>>::Error>,
      <T as TryFrom<BrilValue>>::Error: std::convert::From<InterpError>
{
    if args.len() != arity {
        return Err(InterpError::BadNumArgs(arity, args.len()));
    }

    let mut arg_vals = vec![];
    for arg in args {
        let arg_bril_val = vars.get(&arg)
             .ok_or_else(|| InterpError::VarNotFound(arg.clone()))?;
        arg_vals.push(T::try_from(arg_bril_val.clone())?);
    }
    Ok(arg_vals)
}

pub fn execute(prog: BBProgram) -> Result<(), InterpError> {
    let (main_fn, blocks, labels) = prog;
    let mut curr_block: usize = main_fn.ok_or(InterpError::NoMainFunction)?;
    let mut vars: HashMap<String, BrilValue> = HashMap::new();

    use Operation::*;
    use BrilValue::*;

    'outer: loop {
        let curr_block_obj = &blocks[curr_block];
        let curr_instrs = &curr_block_obj.instrs;
        for operation in curr_instrs.clone() {
            match operation {
                Const { dest, typ, value } => {
                    vars.insert(dest, BrilValue::new(typ, value)?);
                },
                Add { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Int, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Int(args[0] + args[1]));
                },
                Mul { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Int, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Int(args[0] * args[1]));
                },
                Sub { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Int, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Int(args[0] - args[1]));
                },
                Div { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Int, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Int(args[0] / args[1]));
                },
                Eq { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Bool, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Bool(args[0] == args[1]));
                },
                Lt { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Bool, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Bool(args[0] < args[1]));
                },
                Gt { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Bool, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Bool(args[0] > args[1]));
                },
                Le { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Bool, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Bool(args[0] <= args[1]));
                },
                Ge { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Bool, typ)?;
                    let args = get_args::<i64>(&vars, 2, args)?;
                    vars.insert(dest, Bool(args[0] >= args[1]));
                },
                Not { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Bool, typ)?;
                    let args = get_args::<bool>(&vars, 2, args)?;
                    vars.insert(dest, Bool(!args[0]));
                },
                And { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Bool, typ)?;
                    let args = get_args::<bool>(&vars, 2, args)?;
                    vars.insert(dest, Bool(args[0] && args[1]));
                },
                Or { params: ValueOp { dest, typ, args } } => {
                    check_asmt_type(Type::Bool, typ)?;
                    let args = get_args::<bool>(&vars, 2, args)?;
                    vars.insert(dest, Bool(args[0] || args[1]));
                },
                Jmp { params: EffectOp { args } } => {
                    if args.len() != 1 {
                        return Err(InterpError::BadNumArgs(1, args.len()));
                    }
                    curr_block = *(labels.get(&args[0]).ok_or_else(
                            || InterpError::LabelNotFound(args[0].clone())
                        )?);
                    continue 'outer;
                },
                Br { params: EffectOp { args } } => {
                    if args.len() != 3 {
                        return Err(InterpError::BadNumArgs(3, args.len()));
                    }

                    let arg_idx = if get_args(&vars, 1, vec![args[0].clone()])?[0] {
                        1
                    } else {
                        2
                    };
                    curr_block = *(labels.get(&args[arg_idx]).ok_or_else(
                            || InterpError::LabelNotFound(args[arg_idx].clone())
                        )?);
                    continue 'outer;
                },
                Ret { .. } => {
                    return Ok(());
                },
                Id { params: ValueOp { dest, typ, args } } => {
                    if args.len() != 1 {
                        return Err(InterpError::BadNumArgs(1, args.len()));
                    }
                    let src = vars.get(&args[0]).unwrap().clone();
                    check_asmt_type(src.get_type(), typ)?;
                    vars.insert(dest, src);
                }
                Print { args } => {
                    println!("{}", args.into_iter().map(|a| format!("{:?}", vars[&a])).collect::<Vec<_>>().join(", "));
                },
                Nop => {},
            }
        }

        // we have fallen off the end of the basic block without going anywhere
        // we could also fall through to the next basic block? almost certain that's an error, though
        return Ok(());
    }
}
