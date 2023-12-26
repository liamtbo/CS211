def step(self):
        """One fetch/decode/execute step"""
        # the next 'address is in r15
        instr_addr = self.registers[15].get()

        # The instruction at that address we get from memory
        instr_word = self.memory.get(instr_addr)

        # Decode instructions
        instr = decode(instr_word)

        # Display the CPU state when we have decoded the isntruction,
        # before we have executed it
        self.notify_all(CPUStep(self, instr_addr, instr_word, instr))

        # Get all the relevant fields
        op = instr.op
        in1_i_idx = instr.reg_src1
        in2_i_idx = instr.reg_src2
        targ_idx = instr.reg_target
        offset = instr.offset

        # Stop execution once we see the HALT
        if op == OpCode.HALT:
            self.halted = True
            return
        
        # If the instruction has a condition predicate, we can
        # only execute it when the CPU state has the same or 
        # matching predicate.
        #
        # The instruction counter still needs
        # to be incremented (by 1, even though the word size is 4)
        if (self.condition & instr.cond) == CondFlag.NEVER:
            self.registers[15].put(self.registers[15].get() +1)
            return
        
        # Now we can evaluate the instruction, get result and new
        # CPU flag / conditions
        res, self.condition = self.alu.exec(op, 
                                            self.registers[in1_i_idx].get(),
                                            self.registers[in2_i_idx].get() + offset)
        
        # Anything went wrong here we terminate
        if self.condition == CondFlag.V:
            self.halted = True
            return
        
        # Increment instruction counter.
        # It should be done her before the potential LOADS but
        # after the exec abve.
        self.registers[15].put(self.registers[15].get() + 1)

        if op == OpCode.LOAD:
            self.registers[targ_idx].put(self.memory.get(res))
            return
        
        if op == OpCode.STORE:
            self.memory.put(res, self.registers[targ_idx].get())
            return
        
        if targ_idx != 0:
            self.registers[targ_idx].put(res)
            return