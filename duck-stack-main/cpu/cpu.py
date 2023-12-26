
"""
Duck Machine model DM2022 CPU
CIS 211
Feb 20, 2023
Liam Bouffard
Partner: Thalia
"""
"""
Description of understanding with example:

ADD    r1,r1,0[2]      # Count up r1 by 2
STORE  r1,r0,r0[511]    # ... printing each value    
SUB    r0,r1,r0[10]     # ... r1 > 10 ? 
ADD/P  r15,0,r15[-3]    # repeat until r1 > 10

ADD, SUB, MUL, DIV
    OP/COND target, oper1, oper2
STORE
    STORE rX,rY,rZ[disp]
        stores value rX into main memory at address rY.value + rZ.value + disp
LOAD
    LOAD rX,rY,RZ[disp]
        load the memory value at address rY + rZ + disp into rX

each line above is an instruction line

loop over this until r1 > 10
    ADD r1,r1,0[2] # Count up r1 by 2
        since reg 0 is always zero, this adds 2 to r1.value
        and stores it in target r1.value

    STORE r1,r0,r0[511] # ... printing each value
        STORE has a different source destination setup
        stores r1.value (either 0, 2, 4, 6...,8) into memory address 511

    SUB r0,r1,r0[10] # .... r1 > 10?
        r0 always has 0 as its value
        we can use it as a garbage can to get the CONDFLAG of 10 - r1.value
        and throw away the result

    ADD/P r15,0,r15[-3] # repreat until r1 > 10
        r15.value increase by 1 every loop (not at this line of code directly)
        when this instruction line is triggered, the while loop will have iteraded
        over itself 3 times, so r[15] value = 3 (bc 0(add), 1(store), 2(sub), 3(add), 4(add/p))
        SUB checked if r1 > 10, if it's not, SUB gave the P CONDFLAG (negative)
        if the CONDFLAG is P (positive) (r1 > 10), the ADD/P is triggered and 
        r15.value = 0
        Now in the next while loop iteration, we start back at the 0th
        line of instruction and increment r1.value by 2 again
        this process repeats until ADD/P isn't triggered

in other words
    i = 0
    while True:
        i += 2
        print(i)
        keep_looping = 10 - i
        if keep_looping > 0:
            continue
        else:
            break
"""

import context  # Python import search form project root
from instruction_set.instr_format import Instruction, OpCode, CondFlag, decode

from cpu.memory import Memory
from cpu.register import Register, ZeroRegister
from cpu.mvc import MVCEvent, MVCListenable

import logging
logging.basicConfig()
log =  logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class ALU(object):
    """The arithmetic logic unit (also called a "functional unit"
    in a modern CPU) executes a selected function but does not
    otherwise manage CPU state. A modern CPU core may have several
    ALUs to boost performance by performing multiple operatons
    in parallel, but the Duck Machine has just one ALU in one core.
    """
    # The ALU chooses one operation to apply based on a provided
    # operation code.  These are just simple functions of two arguments;
    # in hardware we would use a multiplexer circuit to connect the
    # inputs and output to the selected circuitry for each operation.
    ALU_OPS = {
        OpCode.ADD: lambda x, y: x + y,
        OpCode.SUB: lambda x, y: x - y,
        OpCode.MUL: lambda x, y: x * y,
        OpCode.DIV: lambda x, y: x // y,

        # For memory access operations load, store, the ALU
        # performs the address calculation
        OpCode.LOAD: lambda x, y: x + y,
        OpCode.STORE: lambda x, y: x + y,
        # Some operations perform no operation
        OpCode.HALT: lambda x, y: 0
    }

    def exec(self, op: OpCode, in1_i: int, in2_i: int) -> tuple[int, CondFlag]:
        """"""
        try:
            op_result = self.ALU_OPS[op](in1_i, in2_i)
            if op_result < 0:
                return (op_result, CondFlag.M)
            elif op_result == 0:
                return (op_result, CondFlag.Z)
            elif op_result > 0:
                return (op_result, CondFlag.P)
        except:
            return (0, CondFlag.V) # if division by zero is tried
        
class CPUStep(MVCEvent):
    """CPU is beginning step with PC at a given address"""
    def __init__(self, subject: "CPU", pc_addr: int,
                 instr_word: int, instr: Instruction)-> None:
        self.subject = subject
        self.pc_addr = pc_addr
        self.instr_word = instr_word
        self.instr = instr

class CPU(MVCListenable):
    """Duck Machine central processing unit (CPU)
    has 16 registers (including r0 that always hold zero
    and r15 that holds the program counter), a few
    flag reisters (condition codes, halted state),
    and some logic for sequencing execution. The CPU
    does not contain the main memroy but has a bus connecting
    it to a seperate memory.
    """
    def __init__(self, memory: Memory):
        super().__init__()
        self.memory = memory # Not part of CPU; what we really have is a connection
        self.registers = [ZeroRegister(), Register(), Register(), Register(),
                          Register(), Register(), Register(), Register(),
                          Register(), Register(), Register(), Register(),
                          Register(), Register(), Register(), Register()]
        self.condition = CondFlag.ALWAYS
        self.halted = False
        self.alu = ALU()

    def step(self):
        """One fetch/decode/execute step"""
        # retrieve instruction class that corresponds to instr_addr
        # print('count')
        instr_addr = self.registers[15].get() # every while loop iteration this addr +1
        instr_word = self.memory.get(instr_addr)
        instr = decode(instr_word)
        self.notify_all(CPUStep(self, instr_addr, instr_word, instr))

        # setup vars for use
        in1_i = instr.reg_src1 # index
        in2_i = instr.reg_src2 # index
        op = instr.op
        target = instr.reg_target
        offset = instr.offset

        # print('in1:', in1_i)
        # print('in2:', in2_i)
        # print('op:', op)
        # print('target:', target)
        # print('offset:', offset)

        # instr.op == HALT, change self.halted = True, and return, the while loop will stop
        if op == OpCode.HALT:
            # print('HALT')
            self.halted = True
            return
        
        # if instruction cond and CPU object cond is Never
        # prevous line sets self.condition to the result of its op(oper1, oper2)
        # M = 0001 = 1
        # Z = 0010 = 2
        # P = 0100 = 4 
        # V = 1000 = 8
        # if instr.cond = 0001 and self.condition = 0100
        # instr.cond & self.condition = 0000 = NEVER
        # which would skip to the next line
        if (self.condition & instr.cond) == CondFlag.NEVER:
            # print('CONDFLAG == NEVER')
            self.registers[15].put(self.registers[15].get() +1)
            return
        
        # apply the instruction op to the left and right 
        # operand dictated by same instruction object
        # changes the CPU state to the CONDFLAG of the operation applied to operand1 and operand2
        result, self.condition = self.alu.exec(op, self.registers[in1_i].get(), self.registers[in2_i].get() + offset)
        if self.condition == CondFlag.V:
            self.halted = True
            return
        
   
        # increase register 15 value by 1
        self.registers[15].put(self.registers[15].get() + 1)
        # if op is LOAD -> get the value from memory of index result, 
        # then put that value as the value in the register of index target
        if op == OpCode.LOAD:
            # print('LOAD')
            # first iteratation of while loop in run method puts duck_input method as value in register 14.
            # not sure how it prompts it though but it prompts it within line 138
            self.registers[target].put(self.memory.get(result)) 
            return
        # if op is STORE -> get the value from the register with index target
        # and store it in memory of index result
        if op == OpCode.STORE:
            # print('STORE')
            # prints value
            self.memory.put(result, self.registers[target].get())
            return
        # if target != 0 -> put the result in the register of index target
        if target != 0:
            self.registers[target].put(result)
            return

    def run(self, from_addr=0, single_step=False) -> None:
        """Step the CPU until it executes a HALT"""
        self.halted = False
        self.registers[15].put(from_addr)
        step_count = 0
        while not self.halted: # HALT = opCode 0
            if single_step:
                input(f"Step {step_count}; press enter")
            self.step()
            step_count += 1


