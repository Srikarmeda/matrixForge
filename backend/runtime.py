# backend/runtime.py
import numpy as np
import time
from ir.tac_generator import Quadruple

class MatrixVM:
    """
    Target Runtime Engine mapping Optimized TAC Quadruples to NumPy BLAS operations.
    """
    def __init__(self):
        self.memory = {}
        self.output_log = []
        self.execution_time_ms = 0.0

    def execute(self, quads):
        start_time = time.perf_counter()
        
        for q in quads:
            try:
                if q.op == "ALLOC_MAT":
                    pass # NumPy handles dynamic heap allocation automatically
                    
                elif q.op == "LOAD_LIT":
                    self.memory[q.result] = np.array(q.arg1, dtype=np.float64)
                    
                elif q.op == "LOAD_SCALAR":
                    self.memory[q.result] = float(q.arg1)
                    
                elif q.op == "ASSIGN":
                    self.memory[q.result] = self.memory.get(q.arg1, None)
                    
                elif q.op == "MAT_NEG":
                    self.memory[q.result] = -self.memory[q.arg1]
                    
                elif q.op == "MAT_ADD":
                    self.memory[q.result] = np.add(self.memory[q.arg1], self.memory[q.arg2])
                    
                elif q.op == "MAT_SUB":
                    self.memory[q.result] = np.subtract(self.memory[q.arg1], self.memory[q.arg2])
                    
                elif q.op == "MAT_MUL":
                    self.memory[q.result] = np.matmul(self.memory[q.arg1], self.memory[q.arg2])
                    
                elif q.op == "PRINT":
                    val = self.memory.get(q.arg1, "Undefined")
                    if isinstance(val, np.ndarray):
                        # Format matrix cleanly for terminal output
                        formatted_mat = np.array2string(val, formatter={'float_kind':lambda x: f"{x:g}"})
                        self.output_log.append(f"➤ Output Matrix {q.arg1} [{val.shape[0]}x{val.shape[1]}]:\n{formatted_mat}")
                    else:
                        self.output_log.append(f"➤ Output {q.arg1} = {val}")
                        
            except Exception as e:
                self.output_log.append(f"❌ Runtime Fault at Quadruple {q}: {str(e)}")
                break
                
        self.execution_time_ms = (time.perf_counter() - start_time) * 1000
        return self.output_log, self.execution_time_ms